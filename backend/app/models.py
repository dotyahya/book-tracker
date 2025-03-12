from pymongo import MongoClient
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv
from bson import ObjectId
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

class UserInDB(BaseModel):
    id: str = Field(..., alias="_id")  # Map MongoDB's '_id' to 'id'
    email: EmailStr
    hashed_password: str = Field(..., alias="hashed_password")  # Match DB field

    class Config:
        populate_by_name = True  # Allow field names from aliases
        arbitrary_types_allowed = True

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
    if isinstance(data, dict):
        return {k: str(v) if isinstance(v, ObjectId) else v for k, v in data.items()}
    return data
