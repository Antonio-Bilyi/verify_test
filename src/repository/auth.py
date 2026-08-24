from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from fastapi import HTTPException, status, BackgroundTasks, Request
from src.schemas import UserModel, RequestEmail
from src.database.models import User

from src.authorize import create_access_token, create_refresh_token, get_email_from_refresh_token, Hash, get_email_from_token, confirmed_email
from src.services.send_email import send_email

from libgravatar import Gravatar

import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / '.env'

load_dotenv(dotenv_path=env_path)

has_handler = Hash()

async def create_user(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session) -> User:

    exist_user = db.query(User).filter(User.email == body.username).first()

    if exist_user:

        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = 'User already exists'
        )

    avatar = None

    try:

        g = Gravatar(body.username)

        avatar = g.get_image()

    except Exception as e:

        print(e)

    new_user = User(
        email = body.username,
        password = has_handler.get_password_hash(body.password),
        avatar=avatar
    )

    background_tasks.add_task(send_email, new_user.email, body.username, os.getenv('APP_BASE_URL'))

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return {
        'user': new_user,
        'detail': 'User successfully created. Check your email for confirmation.'
    }

async def get_user(body: OAuth2PasswordRequestForm, db: Session):

    user = db.query(User).filter(User.email == body.username).first()

    if user is None:

        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'User not found'
        )

    if not user.confirmed:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email not confirmed"
        )
    
    if not has_handler.verify_password(body.password, user.password):

        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'User not found'
        )

    access_token = await create_access_token(data={'sub': user.email})

    refresh_token = await create_refresh_token(data={'sub': user.email})

    user.refresh_token = refresh_token

    db.commit()

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }

async def get_refresh_token(credentials: HTTPAuthorizationCredentials, db: Session):

    token = credentials.credentials

    email = await get_email_from_refresh_token(token)

    user = db.query(User).filter(User.email == email).first()

    if user.refresh_token != token:

        user.refresh_token = None

        db.commit()

        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Invalid refresh_token'
        )

    access_token = await create_access_token(data={'sub': email})

    refresh_token = await create_refresh_token(data={'sub': email})

    user.refresh_token = refresh_token

    db.commit()

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }

async def confirm_email(token: str, db: Session):

    email = await get_email_from_token(token)

    user = db.query(User).filter(User.email == email).first()

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification error")
    
    if user.confirmed:

        return {"message": "Your email is already confirmed"}
    
    await confirmed_email(email, db)

async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request, db: Session):

    user = db.query(User).filter(User.email == body.email).first()

    if user.confirmed:

        return {"message": "Your email is already confirmed"}

    if user:

        background_tasks.add_task(send_email, user.email, User.email, os.getenv('APP_BASE_URL'))

    return {"message": "Check your email for confirmation."}

async def update_avatar(email: str, url: str, db: Session) -> User:

    user = db.query(User).filter(User.email == email).first()

    user.avatar = url

    db.commit()

    return user