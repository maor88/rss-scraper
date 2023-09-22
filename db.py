"""
RSS scraper app - sendCloud

db module that contains 3 main tables
1. users (id:pk)
2. feeds (id:pk, user_id:fk)
3. items (id:pk, feed_id:fk)

using sqlalchemy and sqllite, sendcloud db file attached to app directory
the tables will create in case are not existing when app starting

Author: Maor Avitan
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from auth import create_token

# Define the SQLite database URI
DATABASE_URL = "sqlite:///./sendCloud.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    token = Column(String, nullable=False)


class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(String, unique=True, index=True)
    follow = Column(Boolean, default=True)
    failed_cnt = Column(Integer, default=0)
    status = Column(String, default="")
    sync = Column(Boolean, default=True)

# Define a relationship to the 'items' table
    items = relationship("Item", back_populates="feed")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=False)
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    url = Column(String, unique=True)
    title = Column(String)
    description = Column(String)
    unread = Column(Boolean, default=True)

    # Define a relationship to the 'feeds' table
    feed = relationship("Feed", back_populates="items")


# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def get_session():
    try:
        # Check if a session is already active
        session = SessionLocal()
        if not session.is_active:
            session.begin()
        return session
    except Exception as e:
        print("Failed getting db session")
        raise e


def add_user(db, email, token):
    try:
        user = User(email=email, token=token)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def get_user_by_id(user_id: int):
    db = get_session()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        return user
    finally:
        db.close()


def get_user_by_email(email: str):
    db = get_session()
    try:
        user = db.query(User).filter_by(email=email).first()
        return user
    finally:
        db.close()


"""
RSS scraper app - sendCloud

initial part adding user to db runs only when the app started for first time
in order to have users in db

Author: Maor Avitan
"""

db_startup = SessionLocal()

# Add the first user entity if it does not exist
user1_email = "user1@sendcloud.com"
user1 = db_startup.query(User).filter_by(email=user1_email).first()
if not user1:
    user1_token = create_token({"email": user1_email, "id": 1})  # Replace with the actual token generation logic
    add_user(db_startup, user1_email, user1_token)

# Add the second user entity if it does not exist
user2_email = "user2@sendcloud.com"
user2 = db_startup.query(User).filter_by(email=user2_email).first()
if not user2:
    user2_token = create_token({"email": user2_email, "id": 2})  # Replace with the actual token generation logic
    add_user(db_startup, user2_email, user2_token)

# Close the session
db_startup.close()




