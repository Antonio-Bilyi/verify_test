from datetime import date

from sqlalchemy import String, Date, UniqueConstraint, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):

    pass

class Contact(Base):

    __tablename__ = 'contacts'
    __table_args__ = (
        UniqueConstraint('email', 'user_id', name='uq_contact_email_per_user'),
        UniqueConstraint('phone_number', 'user_id', name='uq_phone_number_per_user')
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(250))
    phone_number: Mapped[str] = mapped_column(String(20))
    birthday: Mapped[date] = mapped_column(Date)
    information: Mapped[str] = mapped_column(String(500), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['User'] = relationship('User', back_populates='contacts')

    def __str__(self):

        return f'{self.first_name} {self.last_name}'

class User(Base):

    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(150), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    contacts: Mapped[list['Contact']] = relationship('Contact', back_populates='user')
    confirmed: Mapped[bool] = mapped_column(default=False)