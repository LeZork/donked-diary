"""
Модели данных для приложения дневника
Этот файл определяет структуру таблиц в базе данных с помощью SQLModel.

SQLModel - это библиотека, которая объединяет Pydantic (валидация данных) 
и SQLAlchemy (работа с базой данных).
"""

from __future__ import annotations

import datetime as dt
from typing import Optional
from sqlmodel import SQLModel, Field


class Task(SQLModel, table=True, extend_existing=True):
    """
    Модель задачи
    
    Параметры:
    - table=True: создает таблицу в базе данных
    - extend_existing=True: позволяет переопределять существующую таблицу (для миграций)
    
    Поля:
    - id: уникальный идентификатор (первичный ключ)
    - title: название задачи (с индексом для быстрого поиска)
    - priority: приоритет задачи
    - due: дата выполнения (может быть пустой)
    - desc: описание задачи
    - done: выполнена ли задача (булево значение)
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)  # index=True создает индекс для быстрого поиска
    priority: str = Field(default="Средний")
    due: Optional[dt.date] = Field(default=None)
    desc: str = Field(default="")
    done: bool = Field(default=False)


class Show(SQLModel, table=True, extend_existing=True):
    """
    Модель сериала
    
    Отслеживает прогресс просмотра сериала:
    - В каком сезоне находимся
    - Какую серию смотрим
    - Общее количество просмотренных серий
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    season: int = Field(default=1)  # Текущий сезон
    episode: int = Field(default=0)  # Текущая серия в сезоне
    total: int = Field(default=0)  # Общее количество серий в сезоне
    total_watched_episodes: int = Field(default=0)  # Общее количество просмотренных серий


class Book(SQLModel, table=True, extend_existing=True):
    """
    Модель книги
    
    Отслеживает прогресс чтения книги:
    - Сколько страниц всего в книге
    - Сколько страниц прочитано
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    author: str = Field(default="")
    pages_total: int = Field(default=0)  # Общее количество страниц
    pages_read: int = Field(default=0)  # Прочитано страниц


class LearningLog(SQLModel, table=True, extend_existing=True):
    """
    Модель записи обучения
    
    Логирует время, потраченное на изучение Python:
    - Тема изучения
    - Количество минут
    - Заметки
    - Дата изучения
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str = Field(index=True)
    minutes: int = Field(default=0)
    notes: str = Field(default="")
    log_date: dt.date = Field(default_factory=dt.date.today)  # По умолчанию сегодняшняя дата


class Notification(SQLModel, table=True, extend_existing=True):
    """
    Модель уведомления
    
    Система уведомлений для:
    - Напоминаний о дедлайнах
    - Достижений
    - Мотивационных сообщений
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(index=True)  # Тип уведомления: "deadline", "achievement", "motivation"
    title: str = Field(index=True)
    message: str = Field(default="")
    is_read: bool = Field(default=False)  # Прочитано ли уведомление
    created_date: dt.date = Field(default_factory=dt.date.today)
    related_id: Optional[int] = Field(default=None)  # ID связанного объекта (задача, книга и т.д.)