from typing import Optional
from datetime import date, timedelta

from sqlalchemy.orm import Session

from src.exceptions import ContactNotFoundError, ContactAlreadyExistsError
from src.database.models import Contact, User
from src.schemas import ContactModel, ContactUpdate

async def get_contacts(
    first_name: Optional[str],
    last_name: Optional[str],
    email: Optional[str],
    skip: int,
    limit: int,
    db: Session,
    current_user: User
) -> list[Contact]:

    contacts = db.query(Contact).filter(Contact.user_id == current_user.id)

    if first_name:

        contacts = contacts.filter(Contact.first_name.ilike(f'%{first_name}%'))

    if last_name:

        contacts = contacts.filter(Contact.last_name.ilike(f'%{last_name}%'))

    if email:

        contacts = contacts.filter(Contact.email.ilike(f'%{email}%'))

    return contacts.offset(skip).limit(limit).all()

async def get_contact(contact_id: int, db: Session, current_user: User) -> Contact:

    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()

    if contact is None:

        raise ContactNotFoundError(contact_id)

    return contact

async def create_contact(body: ContactModel, db: Session, current_user: User) -> Contact:

    exist_contact = db.query(Contact).filter(Contact.email == body.email).first()

    if exist_contact:

        raise ContactAlreadyExistsError(body.email)

    contact = Contact(**body.model_dump(), user_id=current_user.id)

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact

async def update_contact(contact_id: int, body: ContactUpdate, db: Session, current_user: User) -> Contact | None:

    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()

    if contact is None:

        raise ContactNotFoundError(contact_id)

    update_data = body.model_dump(exclude_unset=True)

    if 'email' in update_data:

        existing = db.query(Contact).filter(Contact.email == update_data['email'], Contact.id != contact_id).first()

        if existing:

            raise ContactAlreadyExistsError(update_data['email'])

    if 'phone_number' in update_data:

        existing = db.query(Contact).filter(Contact.phone_number == update_data['phone_number'], Contact.id != contact_id).first()

        if existing:
        
            raise ContactAlreadyExistsError(update_data['phone_number'])

    for key, value in update_data.items:

        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)

    return contact

async def remove_contact(contact_id: int, db: Session, current_user: User) -> None:

    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()

    if contact is None:
    
        raise ContactNotFoundError(contact_id)

    db.delete(contact)
    db.commit()

    return None

async def get_upcoming_birthday(db: Session, current_user: User) -> list[Contact]:

    today = date.today()

    upcoming_limit = today + timedelta(days=7)

    contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()

    result = []

    for contact in contacts:

        try:

            birthday_this_year = contact.birthday.replace(year=today.year)

        except ValueError:

            birthday_this_year = date(today.year, 3, 1)

        if birthday_this_year < today:

            try:

                birthday_this_year = contact.birthday.replace(year=today.year + 1)

            except ValueError:

                birthday_this_year = date(today.year + 1, 3, 1)

        if today <= birthday_this_year <= upcoming_limit:

            result.append(contact)

    return result