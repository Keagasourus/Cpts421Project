from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from .database import Base

# Many-to-Many relationship table for Image <-> Tag
image_tags = Table(
    "image_tags",
    Base.metadata,
    Column("image_id", Integer, ForeignKey("images.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    citation_text = Column(String, nullable=False)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    tag_name = Column(String(100), unique=True, nullable=False)

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"))
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    image_type = Column(String(50))
    view_type = Column(String(50))
    file_url = Column(String, nullable=False)

    # Relationships
    tags = relationship("Tag", secondary=image_tags, backref="images")
    source = relationship("Source")

class Object(Base):
    __tablename__ = "objects"
    id = Column(Integer, primary_key=True, index=True)
    object_type = Column(String(255), nullable=False)
    material = Column(String(255))
    findspot = Column(String(255))
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    date_discovered = Column(Date)
    inventory_number = Column(String(100), unique=True)
    description = Column(String)
    
    # Fuzzy Dates System
    date_display = Column(String(255), nullable=False)
    date_start = Column(Integer, nullable=False, index=True)
    date_end = Column(Integer, nullable=False, index=True)
    
    # Dimensions
    width = Column(Numeric(10, 2))
    height = Column(Numeric(10, 2))
    depth = Column(Numeric(10, 2))
    unit = Column(String(20), default='cm')

    # Relationships
    images = relationship("Image", backref="object", cascade="all, delete-orphan")

