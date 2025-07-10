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

# Обновленная модель Payment
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # Изменено на Integer с autoincrement
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    credits = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # pending, success, failed
    payment_id = Column(String)  # Можно удалить, если не используется
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="payments")

class LetterGeneration(Base):  # НЕ BaseModel, а Base!
    __tablename__ = "letter_generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(String, nullable=False)
    vacancy_title = Column(String, nullable=False)
    resume_id = Column(String)
    letter_content = Column(String, nullable=False)
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
    last_searched_at = Column(DateTime, server_default=func.now())  # Последний раз появлялась в поиске
    
    # Relationships
    applications = relationship("Application", back_populates="vacancy")

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(String, ForeignKey("vacancies.id"), nullable=False)
    resume_id = Column(String)  # ID резюме которое использовалось
    message = Column(Text, nullable=False)  # Сопроводительное письмо
    prompt_filename = Column(String)  # Какой промпт использовался для генерации
    ai_model = Column(String)  # Какая модель использовалась
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="applications")
    vacancy = relationship("Vacancy", back_populates="applications")