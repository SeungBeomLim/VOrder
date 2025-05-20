import json
import torch
import numpy as np

from tqdm import tqdm
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus


def process_and_upload_to_mongodb(document: dict):
    username = quote_plus("justintak0426")
    password = quote_plus("hgullm")
    uri = f"mongodb+srv://{username}:{password}@document-embedding.ak89u.mongodb.net/?retryWrites=true&w=majority&appName=Document-embedding"

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
        db = client["embed_document"]
        collection = db["rulebook"]

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