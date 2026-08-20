from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Security, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer

from src.schemas import UserModel, TokenResponse, SignupResponse, UserResponse
from sqlalchemy.orm import Session
from src.database.connect_to_db import db_connect
from src.database.models import User
from src.repository import auth as repository_auth
from src.authorize import get_current_user

import cloudinary
import cloudinary.uploader

import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / '.env'

load_dotenv(dotenv_path=env_path)


router = APIRouter(prefix = '/auth', tags = ['auth'])

security = HTTPBearer()

@router.post('/signup', response_model = SignupResponse, status_code = 201)
async def sign_up(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(db_connect)):

    return await repository_auth.create_user(body, background_tasks, request, db)

@router.post('/login', response_model = TokenResponse)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db_connect)):

    return await repository_auth.get_user(body, db)

@router.get('/refresh_token')
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(db_connect)):

    return await repository_auth.get_refresh_token(credentials, db)

@router.get('/me', response_model=UserResponse)
async def read_user(current_user: User = Depends(get_current_user)):

    return current_user

@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(db_connect)):

    return await repository_auth.confirm_email(token, db)

@router.patch('/avatar', response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_connect)
):

    cloudinary.config(
        cloud_name = os.getenv('CLOUD_NAME'),
        api_keys = os.getenv('CLOUD_KEY'),
        api_secret=os.getenv('CLOUD_SECRET'),
        secure = True,
    )

    cloudinary.uploader.upload(
        file.file,
        public_id = f'ContactApp/{current_user.email}',
        overwrite = True
    )

    src_url = cloudinary.CloudinaryImage(f'ContactApp/{current_user.email}').build_url(
        width = 250,
        height = 250,
        crop='fill'
    )

    user = await repository_auth.update_avatar(current_user.email, src_url, db)

    return user
