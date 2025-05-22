import os
import re
import json
from datetime import datetime, timedelta
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from tqdm import tqdm
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus


# 1. ENV & MODEL SETUP
chat_model = ChatOpenAI(model="gpt-4o-mini")

# 2. LOAD user_info.json
with open("user_info.json", "r", encoding="utf-8") as f:
    user_info = json.load(f)

customer_name   = user_info["name"]
customer_number = user_info["phone_number"]
favorite_drinks = user_info.get("favorite_drinks", [])
saved_menu      = user_info.get("saved_menu", [])
total_menu      = user_info.get("total_menu", [])

# 3. SYSTEM PROMPT
system_prompt = f"""
You are a Starbucks voice-ordering agent. Follow this flow and respond only in English:

1) Ask if the customer wants:
   - a menu recommendation,
   - a normal menu order, or
   - to order from a saved nickname.

2) If recommendation:
   • Recommend from favorite_drinks: {favorite_drinks}
   • Ask “Which of these would you like?”

3) If saved nickname:
   • Ask “Please tell me your nickname.”
   • Match against saved_menu on the “nickname” field:
     {saved_menu}
   • Ask “Is this correct?” to confirm menu, size, extra, price.

4) If normal order:
   • Ask “What menu item would you like?” (from total_menu: {total_menu})
   • Ask “Any extras?” 
   • Ask “What size?”
   • Ask “Anything else to add?”
   • If “no,” go to payment.

5) At the end of ordering, always ask: “Would you like to proceed to payment?”

6) At payment confirmation (“Yes, proceed to payment” etc.),
   • Ask “How many minutes until your order arrives?”
   • Then extract final order details (menu, size, extra, price) from our conversation via LLM.
   • Compute ETA = now + minutes.
   • Build a JSON object with:
     {{
       "customer": "{customer_name}",
       "number": "{customer_number}",
       "menu": <extracted>,
       "size": <extracted>,
       "extra": <extracted>,
       "price": <extracted>,
       "ETA": "<HH:MM>"
     }}
   • Save it to final_order.json
"""

# Message history
messages = [SystemMessage(content=system_prompt)]


def process_and_upload_to_mongodb(document: dict):
    username = quote_plus("justintak0426")
    password = quote_plus("b3fQp24yJubBo9rm")
    uri = f"mongodb+srv://{username}:{password}@llm-project.5t4zx.mongodb.net/?retryWrites=true&w=majority&appName=llm-project"
    
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    # _id 확인
    if "_id" not in document:
        raise ValueError("문서(document)에는 반드시 '_id' 필드가 포함되어야 합니다.")

    # Tensor → list 변환
    for k, v in document.items():
        if isinstance(v, torch.Tensor):
            document[k] = v.tolist()

    client = None
    try:
        # MongoDB 연결
        print("Connecting to MongoDB...")
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["order"]
        collection = db["order_list"]

        print(f"Upserting document with _id={document['_id']}...")
        result = collection.update_one(
            {"_id": document["_id"]},
            {"$set": document},
            upsert=True
        )

        if result.upserted_id is not None:
            print(f"Inserted new document with _id={result.upserted_id}")
        else:
            print(f"Updated existing document with _id={document['_id']}")

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
    messages.append(HumanMessage(content=user_input))
    ai_resp = chat_model.invoke(messages)
    reply = ai_resp.content.strip()
    messages.append(AIMessage(content=reply))

    # detect payment confirmation in user_input
    if re.search(r"\b(proceed|confirm|yes|go ahead|make the order|place the order|pay|okay)\b", user_input, re.IGNORECASE):
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

        eta_time = (datetime.now() + timedelta(minutes=minutes)).strftime("%H:%M")

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