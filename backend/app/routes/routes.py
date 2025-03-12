from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from app.models import User, UserInDB, Book, BookInDB, convert_object_id_to_str
from app.models import db  # Importing db connection from models.py
from bson import ObjectId

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing in .env file!")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# Password Helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return UserInDB(**convert_object_id_to_str(user))

# User Routes
@router.post("/signup")
async def signup(user: User):
    existing_user = db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump_json()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]

    db.users.insert_one(user_dict)
    return {"message": "User created successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Book Routes
@router.post("/books")
async def add_book(book: Book, current_user: UserInDB = Depends(get_current_user)):
    book_dict = book.dict()
    book_dict["user_id"] = current_user.id
    db.books.insert_one(book_dict)
    return {"message": "Book added successfully"}

@router.get("/books")
async def get_books(current_user: UserInDB = Depends(get_current_user)):
    books = list(db.books.find({"user_id": current_user.id}))
    return {"books": convert_object_id_to_str(books)}

@router.put("/books/{book_id}")
async def update_book_status(book_id: str, status: str, current_user: UserInDB = Depends(get_current_user)):
    result = db.books.update_one(
        {"_id": ObjectId(book_id), "user_id": current_user.id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book status updated"}

@router.delete("/books/{book_id}")
async def delete_book(book_id: str, current_user: UserInDB = Depends(get_current_user)):
    result = db.books.delete_one({"_id": ObjectId(book_id), "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted"}
