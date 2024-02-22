from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from config.db import SessionLocal,engine,Base,User
from models.Post import Post
from models.User import UserCreate, UserLogin
from models.Token import Token
from middleware.tokens import create_access_token,decode_token,ACCESS_TOKEN_EXPIRE_MINUTES
from typing import Dict
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import Session
import cachetools
import os

# Initialize FastAPI app
app = FastAPI()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fake in-memory database
db_users = {}
db_posts = {}


# Fake user authentication
def authenticate_user(email: str, password: str, db: SessionLocal):
    user = db.query(User).filter(User.email == email).first()
    if not user or user.hashed_password != password:
        return False
    return True


# Dependency to get current user's email from token
def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/login")), db: SessionLocal = Depends(get_db)):
    email = decode_token(token)
    return email


@app.post("/signup")
async def signup(user: UserCreate, db: SessionLocal = Depends(get_db)):
    if user.email in db_users:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_users[user.email] = user.password
    db_user = User(email=user.email, hashed_password=user.password)
    db.add(db_user)
    db.commit()
    return {"message": "User successfully registered"}


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    email = form_data.username
    password = form_data.password

    if not authenticate_user(email, password, db):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}



@app.post("/addPost")
async def add_post(post: Post, current_user_email: str = Depends(get_current_user)):
    post_id = len(db_posts) + 1
    db_posts[post_id] = {"text": post.text, "author": current_user_email}
    return {"postID": post_id}

# Fake getPosts endpoint with response caching
cache = cachetools.TTLCache(maxsize=100, ttl=300)

@app.get("/getPosts")
async def get_posts(current_user_email: str = Depends(get_current_user)):
    cached_posts = cache.get(current_user_email)
    if cached_posts:
        return cached_posts

    user_posts = [{"postID": post_id, "text": post_data["text"]} for post_id, post_data in db_posts.items() if
                  post_data["author"] == current_user_email]
    cache[current_user_email] = user_posts
    return user_posts


# Fake deletePost endpoint
@app.delete("/deletePost")
async def delete_post(post_id: int, current_user_email: str = Depends(get_current_user)):
    if post_id not in db_posts:
        raise HTTPException(status_code=404, detail="Post not found")

    post = db_posts[post_id]
    if post["author"] != current_user_email:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this post")

    del db_posts[post_id]
    return {"message": "Post deleted successfully"}

