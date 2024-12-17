import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.config import Settings

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=False)
    age = Column(Integer, nullable=True)
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, phone_number={self.phone_number})>"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deadline = Column(DateTime, nullable=False)
    description = Column(String(500), nullable=True)
    title = Column(String(500), nullable=True)
    interval_hours = Column(Integer, nullable=True)
    user = relationship("User", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder(id={self.id}, user_id={self.user_id}, deadline={self.deadline}, " \
               f"description={self.description}, interval_hours={self.interval_hours})>"


def create_database():
    conn = psycopg2.connect(
        dbname="postgres",
        user=Settings.POSTGRES_USER,
        password=Settings.POSTGRES_PASSWORD,
        host=Settings.POSTGRES_HOST,
        port=Settings.POSTGRES_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{Settings.DB_NAME}'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(f"CREATE DATABASE {Settings.DB_NAME}")

    cursor.close()
    conn.close()


def init_db():
    create_database()
    engine = create_engine(Settings.DATABASE_URL, connect_args={"options": "-c timezone=utc"})
    Base.metadata.create_all(bind=engine)


init_db()
