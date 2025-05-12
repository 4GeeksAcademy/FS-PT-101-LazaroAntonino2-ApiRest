from __future__ import annotations  # permite referencias a clases futuras en tipos
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)

    # Relaciones
    profile: Mapped[Optional[Profile]] = relationship('Profile', back_populates='user', uselist=False)
    cars: Mapped[List[Car]] = relationship('Car', back_populates='user')
    favourites: Mapped[List[Favourite]] = relationship('Favourite', back_populates='user')

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "age": self.age,
            "profile": self.profile.serialize() if self.profile else None,
            "favourites": [
            {
                "id": fav.car.id,
                "car": fav.car.name
            } for fav in self.favourites if fav.car]

            # No serializar la contraseña
        }

class Profile(db.Model):
    __tablename__ = 'profiles'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(20))
    bio: Mapped[str] = mapped_column(String(120))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True)

    user: Mapped[User] = relationship('User', back_populates='profile')

    def serialize(self):
        return {
            "user_id": self.user_id,
            "title": self.title,
            "bio": self.bio
        }

class Car(db.Model):
    __tablename__ = 'cars'
    id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[str] = mapped_column(String(20), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), nullable=True)

    user: Mapped[User] = relationship('User', back_populates='cars')
    favourites: Mapped[List[Favourite]] = relationship('Favourite', back_populates='car')

    def serialize(self):
        return {
            'id': self.id,
            'model': self.model,
            'year': self.year,
            'name': self.name,
            'favourite_of': [
                {
                    'id': fav.user.id,
                    'email': fav.user.email
                } for fav in self.favourites if fav.user
            ]
    }


class Favourite(db.Model):
    __tablename__ = 'favourites'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'),nullable=False)
    car_id: Mapped[int] = mapped_column(ForeignKey('cars.id'),nullable=False)

    user: Mapped[User] = relationship('User', back_populates='favourites')
    car: Mapped[Car] = relationship('Car', back_populates='favourites')

    def serialize(self):
        return {
            'id': self.id,
            'user': {
                'email': self.user.email,
                'id': self.user.id
            } if self.user else None,
            'car': {
                'name': self.car.name,
                'id': self.car.id
            } if self.car else None,
    }



