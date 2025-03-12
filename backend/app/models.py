from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os

#  env variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in .env file!")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client.booktracker

# pydantic models for request/response validation
class User(BaseModel):
    email: EmailStr
    password: str

class UserInDB(User):
    id: str
    hashed_password: str

class Book(BaseModel):
    title: str
    author: str
    rating: int
    status: str  # "read" or "to-read"

class BookInDB(Book):
    id: str
    user_id: str

# helper function to convert MongoDB ObjectId to string
def convert_object_id_to_str(data):
    if isinstance(data, list):
        return [{**item, "_id": str(item["_id"])} for item in data]
    elif isinstance(data, dict):
        return {**data, "_id": str(data["_id"])}
    return data
