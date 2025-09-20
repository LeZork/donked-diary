"""
Модуль для работы с базой данных
Этот файл содержит настройки подключения к базе данных и функции для работы с ней.
"""

from __future__ import annotations

from contextlib import contextmanager
from sqlmodel import SQLModel, Session, create_engine

# URL подключения к базе данных SQLite
# SQLite - это легкая файловая база данных, которая хранится в одном файле
DATABASE_URL = "sqlite:///./diary.db"

# Создаем движок базы данных
# echo=False означает, что SQL-запросы не будут выводиться в консоль (для отладки можно поставить True)
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """
    Инициализация базы данных
    Эта функция создает все таблицы в базе данных на основе наших моделей
    """
    # Импортируем все модели, чтобы SQLModel знал о них
    from app.models import Task, Show, Book, LearningLog, Notification
    
    # Создаем все таблицы в базе данных
    # Если таблицы уже существуют, ничего не произойдет
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
    """
    Контекстный менеджер для работы с сессией базы данных
    
    Контекстный менеджер автоматически:
    1. Открывает сессию с базой данных
    2. Передает её в блок кода
    3. Автоматически закрывает сессию после выполнения блока
    
    Использование:
    with get_session() as session:
        # работа с базой данных
        session.add(object)
        session.commit()
    """
    with Session(engine) as session:
        yield session