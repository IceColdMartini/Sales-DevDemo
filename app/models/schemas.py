
from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    sender: str
    recipient: str
    text: str

class Product(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    price: float
    sale_price: Optional[float] = None
    stock_count: int
    image_url: str
    images: List[str]
    rating: float
    review_count: int
    is_active: bool
    category_id: str
    created_at: str
    updated_at: str
    product_tag: Optional[List[str]] = []

class Conversation(BaseModel):
    sender_id: str
    messages: List[dict]

class ApiResponse(BaseModel):
    sender: str
    product_interested: Optional[str] = None
    response_text: str
    isReady: bool
