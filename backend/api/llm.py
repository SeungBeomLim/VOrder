import os
import re
import json
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from tqdm import tqdm
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
import certifi
from zoneinfo import ZoneInfo

# 1. ENV & MODEL SETUP
chat_model = ChatOpenAI(model="gpt-4o-mini")

# 2. LOAD user_info.json
with open("user_info.json", "r", encoding="utf-8") as f:
    user_info = json.load(f)

customer_name   = user_info["name"]
customer_age    = user_info["age"]
customer_number = user_info["phone_number"]
favorite_drinks = user_info.get("favorite_drinks", [])
saved_menu      = user_info.get("saved_menu", [])
total_menu      = user_info.get("total_menu", [])

# 3. SYSTEM PROMPT
system_prompt = f"""
You are a Starbucks voice-ordering agent. Follow this flow and respond only in English:

1) Ask if the customer wants:
   - a menu recommendation,
   - a normal menu order,
   - to order from a saved nickname.
   - Depending on the response, proceed with one of the following:

   If recommendation:
   • Recommend randomly at least 3 from favorite_drinks: {favorite_drinks}
   • Ask: “Which of these would you like?”
   • Wait for the user's response before proceeding.

   If saved nickname:
   • Ask: “Please tell me nickname of custom menu.”
   • Match against saved_menu on the “nickname” field: {saved_menu}
   • If no match, say: “Sorry, I couldn't find that nickname. Please try again.”
   • If matched, confirm menu, size, extra, and price by asking: “Is this correct?”
   • Wait for the user's response before proceeding.

   If normal order:
   • Ask: “What menu item would you like?” (from total_menu: {total_menu})
   • Wait for the user's response before proceeding.

   Then, in two cases except nickname ordering, follow this fixed sequence of questions:
   • Ask: “Hot or Iced?”
   • Wait for the user's response.
   • Ask: “Any extras?”
   • Wait for the user's response.
   • Ask: “What size?”
   • Wait for the user's response.
   • Ask: “Anything else to add?”
   • Wait for the user's response.

2) After the menu selecting, ask: "How many minutes until your order arrives?"

3) At the end of ordering, always ask: “Would you like to proceed to payment?, If so say proceed to payment.”

4) At payment confirmation (“proceed to payment” etc.),
   • Use the conversation context to extract the latest menu, size, extras mentioned by the user.
   • Compute ETA as the current time plus the customer’s response in minutes. Format as HH:MM in 24-hour format.
   • Build a JSON object with:
     {{
       "customer": "{customer_name}",
       "number": "{customer_number}",
       "menu": <extracted>,
       "temp": <extracted>,
       "size": <extracted>,
       "extra": <extracted>,
       "price": <extracted>,
       "ETA": "<HH:MM>"
     }}
   • Save it to final_order.json
   • Do not display or speak the contents of final_order.json under any circumstances.

5) After saving the final order:
   • Always say: “Thank you.” 
"""

# Message history
messages = [SystemMessage(content=system_prompt)]


def process_and_upload_to_mongodb(document: dict):
    """
    document에 '_id'가 없으면 ObjectId를 생성해서 추가한 뒤,
    order.order_list 컬렉션에 upsert합니다.
    """
    # MongoDB 접속 정보
    username = quote_plus("justintak0426")
    password = quote_plus("b3fQp24yJubBo9rm")
    cluster = "llm-project.5t4zx.mongodb.net"
    database = "order"
    collection_name = "order_list"

    uri = (
        f"mongodb+srv://{username}:{password}"
        f"@{cluster}/{database}"
        "?retryWrites=true&w=majority&appName=llm-project"
    )

    # document에 _id가 없으면 uuid4 기반 문자열 생성
    if "_id" not in document:
        document["_id"] = uuid.uuid4().hex  # 예: '3fa85f64f5d14f6e9e4adf81c1f1c6b2'


    # MongoClient 생성 (SSL 인증서 문제 방지를 위해 certifi 사용)
    client = MongoClient(
        uri,
        tls=True,
        tlsCAFile=certifi.where(),
        server_api=ServerApi("1")
    )

    try:
        print("Connecting to MongoDB...")
        # 연결 확인
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")

        db = client[database]
        collection = db[collection_name]

        # Upsert
        print(f"Upserting document with _id={document['_id']}...")
        result = collection.update_one(
            {"_id": document["_id"]},
            {"$set": document},
            upsert=True
        )

        if result.upserted_id:
            print(f"Inserted new document, _id={result.upserted_id}")
        else:
            print(f"Updated existing document, _id={document['_id']}")

    except Exception as e:
        print(f"MongoDB 오류 발생: {e}")
        raise
    finally:
        if client:
            client.close()
            print("MongoDB connection closed")


def order_agent(user_input: str) -> tuple:
    """
    Returns (reply, done_flag). When done_flag=True, final_order.json has been written.
    """
    global eta_minutes

    messages.append(HumanMessage(content=user_input))
    ai_resp = chat_model.invoke(messages)
    reply = ai_resp.content.strip()
    messages.append(AIMessage(content=reply))

    # detect payment confirmation in user_input
    if re.search(r"\b(proceed to payment|proceed|confirm|go ahead|make the order|place the order|pay)\b", user_input, re.IGNORECASE):
        messages.append(HumanMessage(content="How many minutes until your order arrives?"))
        eta_reply = chat_model.invoke(messages).content.strip()
        messages.append(AIMessage(content=eta_reply))

        m = re.search(r"(\d+)", eta_reply)
        minutes = int(m.group(1)) if m else 10

        extract_prompt = (
            "From our conversation, extract only the final order details "
            "and return a raw JSON object with keys: menu, size, extra, price. No explanation."
        )
        messages.append(SystemMessage(content=extract_prompt))
        extract_resp = chat_model.invoke(messages).content.strip()
        messages.append(AIMessage(content=extract_resp))

        # 👇 JSON 안전하게 파싱
        try:
            json_text = re.search(r"\{.*\}", extract_resp, re.DOTALL).group(0)
            details = json.loads(json_text)
        except Exception as e:
            print("❌ Failed to extract JSON:", e)
            return reply, False

        print("Current Time: ", datetime.now(ZoneInfo("Asia/Seoul")))
        print("ETA Minutes: ", minutes)
        eta_time = (datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(minutes=minutes)).strftime("%H:%M")
        print("ETA Time: ", eta_time)


        final_order = {
            "customer": customer_name,
            "number": customer_number,
            "menu": details.get("menu", ""),
            "size": details.get("size", ""),
            "extra": details.get("extra", ""),
            "price": details.get("price", 0),
            "ETA": eta_time
        }

        process_and_upload_to_mongodb(final_order)
        final_order_path = os.path.join(settings.MEDIA_ROOT, "final_order.json")
        with open(final_order_path, "w", encoding="utf-8") as f:
            json.dump(final_order, f, ensure_ascii=False, indent=2)

        print("✅ final_order.json created:\n", json.dumps(final_order, indent=2))
        return reply, True
    
    print(f"🤖 LLM reply: {reply}")

    return reply, False