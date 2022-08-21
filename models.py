from enum import unique
from locale import currency
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    profile_image = Column(String)
    merchant_id = Column(String)
    email = Column(String)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    access_key = Column(String)
    currency = Column(String)
    location_id = Column(String)
    items = relationship("Item", back_populates="owner")
    cover_picture = Column(String)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    days = Column(Integer)
    state = Column(String)
    departure_date = Column(String)
    total_seats = Column(Integer)
    price = Column(Integer)
    stock = Column(Integer)
    image = Column(String)

    owner = relationship("User", back_populates="items")

class Checkout(Base):
    __tablename__ = "checkouts"
    
    id = Column(Integer, primary_key=True, index=True)

    item_id = Column(Integer)
    quantity = Column(Integer)

    checkout_id = Column(String, index=True)
    checkout_url = Column(String)
    checkout_total = Column(Integer)
    transaction_id = Column(String)