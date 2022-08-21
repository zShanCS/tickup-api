from typing import List, Union

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: Union[str, None] = None
    price: int
    stock: int
    image: Union[str, None] = None
    days: Union[int, None] = None
    state: Union[str, None] = None
    departure_date: Union[str, None] = None
    total_seats: Union[int, None] = None

class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int
    image: str

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: Union[str, None] = None
    name: Union[str, None] = None

class UserCreate(UserBase):
    password: str
    access_key: str
    location_id: str


class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []
    profile_picture : Union[str, None] = None
    cover_picture : Union[str, None] = None

    class Config:
        orm_mode = True
