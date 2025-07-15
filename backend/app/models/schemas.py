from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# User schemas
class UserBase(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    hh_user_id: str

class UserUpdate(UserBase):
    pass

class User(UserBase):
    id: UUID
    hh_user_id: str
    credits: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Payment schemas
class PaymentCreate(BaseModel):
    package: str  # "50", "100", "200"

class PaymentCallback(BaseModel):
    payment_id: str
    status: str

class Payment(BaseModel):
    id: int  # Изменено с UUID на int
    amount: float
    credits: int
    status: str
    payment_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Letter generation schemas
class LetterGeneration(BaseModel):
    id: UUID
    vacancy_id: str
    vacancy_title: str
    resume_id: Optional[str]
    letter_content: str
    prompt_filename: str
    ai_model: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class AuthResponse(BaseModel):
    token: str
    refresh_token: Optional[str] = None
    user: User

# Resume schemas
class ResumeResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    title: str
    total_experience: Optional[Dict[str, Any]] = None
    skill_set: Optional[List[str]] = None
    full_text: str

# Dictionary schemas
class Dictionaries(BaseModel):
    experience: List[Dict[str, str]]
    employment: List[Dict[str, str]]
    schedule: List[Dict[str, str]]

# Vacancy schemas
class VacancyDetail(BaseModel):
    id: str
    name: str
    salary: Optional[Dict[str, Any]]
    employer: Dict[str, Any]
    area: Dict[str, Any]
    published_at: str
    schedule: Optional[Dict[str, Any]]
    employment: Optional[Dict[str, Any]]
    description: str
    snippet: Optional[Dict[str, Any]]
    experience: Optional[Dict[str, Any]]
    key_skills: Optional[List[Dict[str, Any]]]
    professional_roles: Optional[List[Dict[str, Any]]]


# Credit check
class CreditCheckResponse(BaseModel):
    has_credits: bool
    credits: int
    message: Optional[str] = None

# Cover letter response schema
class CoverLetter(BaseModel):
    content: str
    prompt_filename: str
    ai_model: str

# Application schemas
class ApplicationCreate(BaseModel):
    resume_id: str
    message: str
    prompt_filename: Optional[str] = None
    ai_model: Optional[str] = None

class Application(BaseModel):
    id: UUID
    user_id: UUID
    vacancy_id: str
    resume_id: str
    message: str
    prompt_filename: Optional[str]
    ai_model: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Pseudonymization schemas
class MappingBase(BaseModel):
    original_value: str
    pseudonym: str
    data_type: str  # 'name', 'email', 'phone', 'company', etc

class MappingCreate(MappingBase):
    session_id: UUID

class Mapping(MappingBase):
    id: UUID
    session_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class MappingSessionBase(BaseModel):
    pass

class MappingSessionCreate(MappingSessionBase):
    user_id: UUID

class MappingSession(MappingSessionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    expires_at: datetime
    mappings: Optional[List[Mapping]] = None
    
    class Config:
        from_attributes = True

# Pseudonymization request/response schemas
class PseudonymizationRequest(BaseModel):
    text: str
    session_id: Optional[UUID] = None  # Если None, создается новая сессия
    data_types: Optional[List[str]] = None  # Какие типы данных псевдонимизировать

class PseudonymizationResponse(BaseModel):
    pseudonymized_text: str
    session_id: UUID
    mappings_created: int
    expires_at: datetime

class DePseudonymizationRequest(BaseModel):
    text: str
    session_id: UUID

class DePseudonymizationResponse(BaseModel):
    original_text: str
    session_id: UUID
    mappings_found: int