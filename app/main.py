import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import date
from app.db import init_db, get_session
from app.models import Task, Show, Book, LearningLog
from sqlmodel import select

init_db()

st.set_page_config(page_title="Мой дневник", page_icon="📔", layout="wide")

# Инициализация простого "хранилища" в сессии
if "tasks" not in st.session_state:
	st.session_state.tasks = []
if "shows" not in st.session_state:
	st.session_state.shows = []
if "books" not in st.session_state:
	st.session_state.books = []
if "learning" not in st.session_state:
	st.session_state.learning = []

st.title("Мой дневник")
st.caption("Задачи . Сериалы . Книги . Обучение Python")

tabs = st.tabs(["✅ Задачи", "🎬 Сериалы", "📚 Книги", "🐍 Обучение Python"])

with tabs[0]:
	st.subheader("Задачи")

	# Форма добавления/обновления
	with st.form("task_form_db", clear_on_submit=True):
		col1, col2, col3 = st.columns([3, 1.2, 1.2])
		with col1:
			title = st.text_input("Название задачи")
		with col2:
			priority = st.selectbox("Приоритет", ["Низкий", "Средний", "Высокий"])
		with col3:
			due = st.date_input("Дедлайн", value=date.today())
		desc = st.text_area("Описание", height=80)
		submit = st.form_submit_button("Сохранить")
		if submit and title.strip():
			with get_session() as session:
				task = Task(title=title.strip(), priority=priority, due=due, desc=desc.strip(), done=False)
				session.add(task)
				session.commit()
			st.success("Задача сохранена")
			st.rerun()

	st.divider()

	# Список задач из БД
	with get_session() as session:
	    tasks = session.exec(
		    select(Task).order_by(Task.done.asc(), Task.due.is_(None), Task.due.asc())
	    ).all()

	if tasks:
		for t in tasks:
			col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
			with col1:
				meta = f"{t.priority}"
				if t.due:
					meta += f" · до {t.due}"
				st.markdown(f"**{t.title}** — {meta}")
				if t.desc:
					st.caption(t.desc)
			with col2:
				if st.button("Готово" if not t.done else "Снять", key=f"task_done_{t.id}"):
					with get_session() as session:
						obj = session.get(Task, t.id)
						if obj:
							obj.done = not obj.done
							session.add(obj)
							session.commit()
					st.rerun()
			with col3:
				if st.button("Удалить", key=f"task_del_{t.id}"):
					with get_session() as session:
						obj = session.get(Task, t.id)
						if obj:
							session.delete(obj)
							session.commit()
					st.rerun()
			with col4:
				st.write("✅" if t.done else "—")
	else:
		st.info("Пока нет задач.")

with tabs[1]:
	st.subheader("Сериалы")
	with st.form("show_form", clear_on_submit=True):
		col1, col2, col3 = st.columns([3, 1, 1])
		with col1:
			title = st.text_input("Название сериала")
		with col2:
			season = st.number_input("Сезон", min_value=1, value=1, step=1)
		with col3:
			episode = st.number_input("Серия (текущая)", min_value=0, value=0, step=1)
		total_episodes = st.number_input("Всего серий в сезоне", min_value=0, value=0, step=1)
		submit = st.form_submit_button("Добавить/Обновить")
		if submit and title.strip():
			st.session_state.shows.append({
				"title": title.strip(),
				"season": int(season),
				"episode": int(episode),
				"total": int(total_episodes)
			})
	if st.session_state.shows:
		for i, s in enumerate(st.session_state.shows):
			progress = f"{s['episode']}/{s['total']}" if s["total"] else f"{s['episode']}"
			col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
			with col1:
				st.markdown(f"**{s['title']}** — S{s['season']} E{progress}")
			with col2:
				if st.button("➕ Серия", key=f"show_next_{i}"):
					st.session_state.shows[i]["episode"] += 1
					st.rerun()
			with col3:
				if st.button("Новый сезон", key=f"show_new_season_{i}"):
					st.session_state.shows[i]["season"] += 1
					st.session_state.shows[i]["episode"] = 0
					st.rerun()
			with col4:
				if st.button("Удалить", key=f"show_del_{i}"):
					st.session_state.shows.pop(i)
					st.rerun()
	else:
		st.info("Пока нет сериалов.")

with tabs[2]:
	st.subheader("Книги")
	with st.form("book_form", clear_on_submit=True):
		col1, col2, col3 = st.columns([3, 1, 1])
		with col1:
			title = st.text_input("Название книги")
			author = st.text_input("Автор")
		with col2:
			pages_total = st.number_input("Страниц всего", min_value=0, value=0, step=1)
		with col3:
			pages_read = st.number_input("Прочитано страниц", min_value=0, value=0, step=1)
		submit = st.form_submit_button("Добавить/Обновить")
		if submit and title.strip():
			st.session_state.books.append({
				"title": title.strip(),
				"author": author.strip(),
				"pages_total": int(pages_total),
				"pages_read": int(pages_read)
			})
	if st.session_state.books:
		for i, b in enumerate(st.session_state.books):
			ratio = (b["pages_read"] / b["pages_total"] * 100) if b["pages_total"] else 0
			col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
			with col1:
				st.markdown(f"**{b['title']}** — {b['author']}")
				st.progress(min(1.0, ratio / 100.0), text=f"{b['pages_read']} из {b['pages_total']} ({ratio:.0f}%)")
			with col2:
				new_read = st.number_input("Добавить страниц", min_value=0, value=0, step=1, key=f"book_add_{i}")
			with col3:
				if st.button("➕ Прогресс", key=f"book_inc_{i}"):
					st.session_state.books[i]["pages_read"] += int(new_read)
					st.rerun()
			with col4:
				if st.button("Удалить", key=f"book_del_{i}"):
					st.session_state.books.pop(i)
					st.rerun()
	else:
		st.info("Пока нет книг.")

with tabs[3]:
	st.subheader("Обучение Python")
	with st.form("learning_form", clear_on_submit=True):
		topic = st.text_input("Тема/курс/глава")
		time_spent = st.number_input("Время (мин)", min_value=0, value=30, step=10)
		notes = st.text_area("Заметки", height=80)
		submit = st.form_submit_button("Добавить запись")
		if submit and topic.strip():
			st.session_state.learning.append({
				"topic": topic.strip(),
				"minutes": int(time_spent),
				"notes": notes.strip(),
				"date": str(date.today())
			})
	if st.session_state.learning:
		total_min = sum(r["minutes"] for r in st.session_state.learning)
		st.metric("Всего времени", f"{total_min} мин")
		for i, r in enumerate(st.session_state.learning):
			col1, col2, col3 = st.columns([3, 2, 1])
			with col1:
				st.markdown(f"**{r['topic']}** — {r['date']}")
				if r["notes"]:
					st.caption(r["notes"])
			with col2:
				st.write(f"{r['minutes']} мин")
			with col3:
				if st.button("Удалить", key=f"learn_del_{i}"):
					st.session_state.learning.pop(i)
					st.rerun()
	else:
		st.info("Пока нет записей обучения.")