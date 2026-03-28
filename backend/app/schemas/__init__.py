"""
Schemas Pydantic v2 para validación de datos.
"""
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token, TokenData
from app.schemas.book import BookCreate, BookUpdate, BookResponse, BookCategoryResponse
from app.schemas.sale import SaleCreate, SaleResponse, SaleItemCreate, InvoiceResponse
from app.schemas.purchase import PurchaseCreate, PurchaseResponse, PurchaseItemCreate
from app.schemas.client import ClientCreate, ClientResponse, ClientRegister
from app.schemas.employee import EmployeeCreate, EmployeeResponse

__all__ = [
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    "BookCreate",
    "BookUpdate",
    "BookResponse",
    "BookCategoryResponse",
    "SaleCreate",
    "SaleResponse",
    "SaleItemCreate",
    "InvoiceResponse",
    "PurchaseCreate",
    "PurchaseResponse",
    "PurchaseItemCreate",
    "ClientCreate",
    "ClientResponse",
    "ClientRegister",
    "EmployeeCreate",
    "EmployeeResponse",
]
