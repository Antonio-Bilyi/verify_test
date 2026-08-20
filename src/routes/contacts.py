from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from sqlalchemy.orm import Session

from src.database.connect_to_db import db_connect
from src.database.models import User
from src.schemas import ContactModel, ContactResponse, ContactUpdate
from src.repository import contacts as repository
from src.authorize import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.limiter import limiter

router = APIRouter(prefix='/contacts', tags=['contacts'])

@router.get('/', response_model=list[ContactResponse])
@limiter.limit('10/minute')
async def read_contacts(
    request: Request,
    first_name: Optional[str] = Query(default=None, description='Search by first name'),
    last_name: Optional[str] = Query(default=None, description='Search by last name'),
    email: Optional[str] = Query(default=None, description='Search by email'),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(db_connect),
    current_user: User = Depends(get_current_user),
):

    return await repository.get_contacts(first_name, last_name, email, skip, limit, db, current_user)

@router.get('/birthdays', response_model=list[ContactResponse])
@limiter.limit('10/minute')
async def get_birthdays(request: Request, db: Session = Depends(db_connect), current_user: User = Depends(get_current_user)):

    return await repository.get_upcoming_birthday(db, current_user)

@router.get('/{contact_id}', response_model=ContactResponse)
@limiter.limit('10/minute')
async def read_contact(request: Request, contact_id: int, db: Session = Depends(db_connect), current_user: User = Depends(get_current_user)):

    return await repository.get_contact(contact_id, db, current_user)

@router.post('/', response_model=ContactResponse, status_code=201)
@limiter.limit('5/minute')
async def create_contact(request: Request, body: ContactModel, db: Session = Depends(db_connect), current_user: User = Depends(get_current_user)):

    return await repository.create_contact(body, db, current_user)

@router.patch('/{contact_id}', response_model=ContactResponse)
@limiter.limit('5/minute')
async def update_contact(request: Request, contact_id: int, body: ContactUpdate, db: Session = Depends(db_connect), current_user: User = Depends(get_current_user)):

    return await repository.update_contact(contact_id, body, db, current_user)

@router.delete('/{contact_id}', status_code=204)
@limiter.limit('5/minute')
async def remove_contact(request: Request, contact_id: int, db: Session = Depends(db_connect), current_user: User = Depends(get_current_user)):

    await repository.remove_contact(contact_id, db, current_user)