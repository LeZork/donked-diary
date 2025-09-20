from __future__ import annotations

from contextlib import contextmanager
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///./diary.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
	from app.models import Task, Show, Book, LearningLog 
	SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
	with Session(engine) as session:
		yield session