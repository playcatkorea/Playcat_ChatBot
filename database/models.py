from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Consultation(Base):
    """상담 정보"""
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100))
    contact = Column(String(100))
    channel = Column(String(50))  # kakao, instagram, web
    consultation_type = Column(String(50))  # detailed_quote, rough_quote, other_inquiry
    status = Column(String(50), default="pending")  # pending, processing, quoted, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    installation = relationship("Installation", back_populates="consultation", uselist=False)
    cats = relationship("Cat", back_populates="consultation")
    quote = relationship("Quote", back_populates="consultation", uselist=False)


class Installation(Base):
    """설치 정보"""
    __tablename__ = "installations"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"))

    # 설치 장소 정보
    region = Column(String(200))  # 설치 지역
    location_type = Column(String(100))  # 가정집, 유기묘 카페 등
    space_photos = Column(JSON)  # 사진 경로들

    # 공간 사이즈
    width = Column(Float)  # cm
    height = Column(Float)  # cm
    ceiling_height = Column(Float)  # cm

    # 벽 재질
    wall_material = Column(String(100))  # 콘크리트, 석고보드 등

    # 제품 컬러
    product_color = Column(String(50))

    # 추가 정보
    concerns = Column(Text)
    problems_to_solve = Column(Text)
    additional_comments = Column(Text)

    # 합성된 이미지 경로
    composite_image_path = Column(String(500))

    # 설치 예정일
    installation_date = Column(DateTime, nullable=True)

    consultation = relationship("Consultation", back_populates="installation")


class Cat(Base):
    """고양이 정보"""
    __tablename__ = "cats"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"))

    name = Column(String(100), nullable=True)
    age = Column(String(50))
    weight = Column(Float)  # kg
    breed = Column(String(100))
    gender = Column(String(50))  # 수컷/암컷, 중성화 여부
    personality = Column(Text)
    health_issues = Column(Text, nullable=True)
    problem_behavior = Column(Text, nullable=True)
    incompatible_cats = Column(String(200), nullable=True)  # 사이 안 좋은 아이

    consultation = relationship("Consultation", back_populates="cats")


class Quote(Base):
    """견적서"""
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"))

    # 제품 구성
    products = Column(JSON)  # [{"id": "wall_walker_30", "quantity": 6, "price": 210000}, ...]

    # 가격 정보
    product_total = Column(Float)
    installation_fee = Column(Float)
    regional_surcharge = Column(Float)
    color_surcharge = Column(Float)
    total_price = Column(Float)

    # 견적서 파일
    pdf_path = Column(String(500))

    # 할인 정보
    discount_rate = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="quote")


class Product(Base):
    """제품 마스터 데이터"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(100), unique=True, index=True)
    name = Column(String(200))
    category = Column(String(100))

    # 사이즈
    width = Column(Float, nullable=True)
    depth = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    diameter = Column(Float, nullable=True)

    base_price = Column(Float)
    description = Column(Text)
    usage = Column(Text)

    # 제품 이미지 경로
    image_path = Column(String(500))

    # 활성화 여부
    is_active = Column(Boolean, default=True)


class ChatHistory(Base):
    """대화 기록"""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)

    session_id = Column(String(200), index=True)
    role = Column(String(50))  # user, assistant, system
    message = Column(Text)
    message_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
