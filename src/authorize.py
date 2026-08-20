from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt
from passlib.context import CryptContext

from sqlalchemy.orm import Session

from src.database.connect_to_db import db_connect
from src.database.models import User
import pickle
import redis.asyncio as redis

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'

load_dotenv(dotenv_path=env_path)

KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

HOST = os.getenv('REDIS_HOST')
PORT = os.getenv('REDIS_PORT')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

r = redis.Redis(host=HOST, port=PORT, db=0)

class Hash:

    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    def verify_password(self, plain_password, hashed_password):

        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):

        return self.pwd_context.hash(password)

async def create_access_token(data: dict, expires_delta: Optional[float] = None):

    to_encode = data.copy()

    if expires_delta:

        expire = datetime.now() + timedelta(seconds=expires_delta)

    else:

        expire = datetime.now() + timedelta(minutes=15)

    to_encode.update({
        'iat': datetime.now(),
        'exp': expire,
        'scope': 'access_token'
    })

    access_token = jwt.encode(to_encode, KEY, algorithm=ALGORITHM)

    return access_token

async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):

    to_encode = data.copy()

    if expires_delta:

        expire = datetime.now() + timedelta(seconds=expires_delta)

    else:

        expire = datetime.now() + timedelta(days=7)

    to_encode.update({
        'iat': datetime.now(),
        'exp': expire,
        'scope': 'refresh_token'
    })

    refresh_token = jwt.encode(to_encode, KEY, algorithm=ALGORITHM)

    return refresh_token

async def get_email_from_refresh_token(refresh_token: str):

    try:

        payload = jwt.decode(refresh_token, KEY, algorithms=[ALGORITHM])

        if payload['scope'] == 'refresh_token':

            email = payload['sub']

            return email

        else:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token has expired'
            )

    except JWTError as e:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Credentials has not validated'
        )

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(db_connect)):

    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Unauthorized',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    try:

        payload = jwt.decode(token, KEY, algorithms=[ALGORITHM])

        if payload['scope'] == 'access_token':

            email = payload['sub']

            if email is None:

                raise exception

        else:

            raise exception
    except JWTError as e:

        raise exception

    current_user = await r.get(f'user: {email}')

    if current_user is None:

        current_user = db.query(User).filter(User.email == email).first()

        if current_user is None:

            raise exception

        await r.set(f'user: {email}', pickle.dumps(current_user))
        await r.expire(f'user: {email}', 900)

    else:

        current_user = pickle.loads(current_user)

    return current_user

async def create_email_token(data: dict):

    to_encode = data.copy()

    expire = datetime.now() + timedelta(days=7)

    to_encode.update({"iat": datetime.now(), "exp": expire})

    email_token = jwt.encode(to_encode, KEY, algorithm=ALGORITHM)

    return email_token

async def get_email_from_token(token: str):

    try:

        payload = jwt.decode(token, KEY, algorithms=[ALGORITHM])

        email = payload['sub']

        return email

    except JWTError as e:
      
      print(e)

      raise HTTPException(
          status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
          detail="Invalid token for email verification"
        )

async def confirmed_email(email: str, db: Session = Depends(db_connect)) -> None:

    user = db.query(User).filter(User.email == email).first()
    
    if user is None:
    
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    
    user.confirmed = True

    db.commit()
