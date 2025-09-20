from __future__ import annotations

import datetime as dt
from typing import Optional
from sqlmodel import SQLModel, Field


class Task(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	title: str = Field(index=True)
	priority: str = Field(default="Средний")
	due: Optional[dt.date] = Field(default=None)
	desc: str = Field(default="")
	done: bool = Field(default=False)


class Show(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	title: str = Field(index=True)
	season: int = Field(default=1)
	episode: int = Field(default=0)
	total: int = Field(default=0)


class Book(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	title: str = Field(index=True)
	author: str = Field(default="")
	pages_total: int = Field(default=0)
	pages_read: int = Field(default=0)


class LearningLog(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	topic: str = Field(index=True)
	minutes: int = Field(default=0)
	notes: str = Field(default="")
	log_date: dt.date = Field(default_factory=dt.date.today)