from sqlalchemy import Column, String, Integer, DateTime, Numeric, UUID, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hh_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    credits = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    payments = relationship("Payment", back_populates="user")
    letter_generations = relationship("LetterGeneration", back_populates="user")
    applications = relationship("Application", back_populates="user")
    mapping_sessions = relationship("MappingSession", back_populates="user")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    credits = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # pending, success, failed
    payment_id = Column(String)  # External payment ID from Robokassa
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="payments")
    
class LetterGeneration(Base):
    __tablename__ = "letter_generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(String, nullable=False)
    vacancy_title = Column(String, nullable=False)
    resume_id = Column(String)
    letter_content = Column(Text, nullable=False)
    prompt_filename = Column(String)  # Какой промпт использовался
    ai_model = Column(String)  # Какая модель использовалась
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="letter_generations")


class Vacancy(Base):
    __tablename__ = "vacancies"
    
    id = Column(String, primary_key=True)  # HH vacancy ID
    name = Column(String, nullable=False)
    employer_name = Column(String)
    area_name = Column(String)
    salary_from = Column(Integer)
    salary_to = Column(Integer)
    salary_currency = Column(String)
    description = Column(Text)  # Полное текстовое описание
    key_skills = Column(JSON)  # Список навыков
    experience = Column(String)  # Требуемый опыт
    employment = Column(String)  # Тип занятости
    schedule = Column(String)  # График работы
    full_data = Column(JSON)  # Полный ответ от HH API для дополнительных полей
    
    # Метки времени
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_searched_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    applications = relationship("Application", back_populates="vacancy")

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(String, ForeignKey("vacancies.id"), nullable=False)
    resume_id = Column(String)
    message = Column(Text, nullable=False)
    prompt_filename = Column(String)  # Какой промпт использовался для генерации
    ai_model = Column(String)  # Какая модель использовалась
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="applications")
    vacancy = relationship("Vacancy", back_populates="applications")

# Simplified Pseudonymization models
class MappingSession(Base):
    __tablename__ = "mapping_sessions"
    __table_args__ = {'schema': 'pseudonymization'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, server_default=func.now() + func.interval('7 days'))
    
    # Relationships
    user = relationship("User", back_populates="mapping_sessions")
    mappings = relationship("Mapping", back_populates="session", cascade="all, delete-orphan")

class Mapping(Base):
    __tablename__ = "mappings"
    __table_args__ = {'schema': 'pseudonymization'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("pseudonymization.mapping_sessions.id", ondelete="CASCADE"), nullable=False)
    original_value = Column(Text, nullable=True)
    pseudonym = Column(Text, nullable=False)
    data_type = Column(String(50), nullable=False)  # 'company', 'education'
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    session = relationship("MappingSession", back_populates="mappings")