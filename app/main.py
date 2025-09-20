"""
Основное приложение дневника на Streamlit

Этот файл содержит:
1. Веб-интерфейс приложения (Streamlit)
2. Логику работы с данными
3. Систему уведомлений
4. Аналитику и статистику

Streamlit - это фреймворк для создания веб-приложений на Python.
Он позволяет создавать интерактивные веб-приложения без знания HTML/CSS/JavaScript.
"""

# Настройка путей для импорта модулей
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорты основных библиотек
import streamlit as st  # Веб-фреймворк
from datetime import date, datetime, timedelta  # Работа с датами
import calendar  # Работа с календарем

# Импорты наших модулей
from app.db import init_db, get_session  # Работа с базой данных
from app.models import Task, Show, Book, LearningLog, Notification  # Модели данных
from sqlmodel import select  # SQL-запросы

# Инициализация базы данных при запуске приложения
init_db()

# Настройка страницы Streamlit
st.set_page_config(page_title="Мой дневник", page_icon="📔", layout="wide")

# Инициализация базы данных
# Все данные теперь хранятся в SQLite базе данных

# =============================================================================
# СИСТЕМА УВЕДОМЛЕНИЙ
# =============================================================================
# Эти функции автоматически создают уведомления на основе ваших данных

def check_deadline_reminders():
    """
    Проверяет приближающиеся дедлайны и создает уведомления
    
    Логика работы:
    1. Находит задачи с дедлайнами в ближайшие 3 дня
    2. Создает уведомления в зависимости от количества дней до дедлайна
    3. Проверяет, не создано ли уже уведомление для этой задачи сегодня
    """
    today = date.today()
    with get_session() as session:
        # Задачи с дедлайнами в ближайшие 3 дня
        upcoming_tasks = session.exec(
            select(Task).where(
                Task.due.isnot(None),
                Task.due >= today,
                Task.due <= today + timedelta(days=3),
                Task.done == False
            )
        ).all()
        
        for task in upcoming_tasks:
            days_left = (task.due - today).days
            if days_left == 0:
                message = f"⏰ Сегодня дедлайн задачи: {task.title}"
                notification_type = "deadline"
            elif days_left == 1:
                message = f"⚠️ Завтра дедлайн задачи: {task.title}"
                notification_type = "deadline"
            else:
                message = f"📅 Через {days_left} дней дедлайн задачи: {task.title}"
                notification_type = "deadline"
            
            # Проверяем, не создано ли уже уведомление
            existing = session.exec(
                select(Notification).where(
                    Notification.type == notification_type,
                    Notification.related_id == task.id,
                    Notification.created_date == today
                )
            ).first()
            
            if not existing:
                notification = Notification(
                    type=notification_type,
                    title="Напоминание о дедлайне",
                    message=message,
                    related_id=task.id
                )
                session.add(notification)
                session.commit()

def check_achievements():
    """
    Проверяет достижения и создает мотивационные сообщения
    
    Отслеживает:
    1. Выполнение множественных задач в день (3+ задач)
    2. Завершение книг (прочитано 100% страниц)
    3. Интенсивное обучение (60+ минут в день)
    """
    today = date.today()
    with get_session() as session:
        # Проверяем выполненные задачи за сегодня
        today_tasks = session.exec(
            select(Task).where(
                Task.done == True,
                Task.due == today
            )
        ).all()
        
        if len(today_tasks) >= 3:
            message = f"🎉 Отлично! Вы выполнили {len(today_tasks)} задач сегодня!"
            notification_type = "achievement"
            
            # Проверяем, не создано ли уже уведомление
            existing = session.exec(
                select(Notification).where(
                    Notification.type == notification_type,
                    Notification.title == "Множественные задачи выполнены",
                    Notification.created_date == today
                )
            ).first()
            
            if not existing:
                notification = Notification(
                    type=notification_type,
                    title="Множественные задачи выполнены",
                    message=message
                )
                session.add(notification)
                session.commit()
        
        # Проверяем завершенные книги
        completed_books = session.exec(
            select(Book).where(
                Book.pages_read >= Book.pages_total,
                Book.pages_total > 0
            )
        ).all()
        
        for book in completed_books:
            message = f"📚 Поздравляем! Вы завершили книгу '{book.title}'!"
            notification_type = "achievement"
            
            # Проверяем, не создано ли уже уведомление
            existing = session.exec(
                select(Notification).where(
                    Notification.type == notification_type,
                    Notification.related_id == book.id
                )
            ).first()
            
            if not existing:
                notification = Notification(
                    type=notification_type,
                    title="Книга завершена",
                    message=message,
                    related_id=book.id
                )
                session.add(notification)
                session.commit()
        
        # Проверяем обучение
        learning_logs = session.exec(
            select(LearningLog).where(LearningLog.log_date == today)
        ).all()
        
        total_today_minutes = sum(log.minutes for log in learning_logs)
        if total_today_minutes >= 60:
            message = f"🐍 Потрясающе! Вы изучали Python {total_today_minutes} минут сегодня!"
            notification_type = "motivation"
            
            # Проверяем, не создано ли уже уведомление
            existing = session.exec(
                select(Notification).where(
                    Notification.type == notification_type,
                    Notification.title == "Интенсивное обучение",
                    Notification.created_date == today
                )
            ).first()
            
            if not existing:
                notification = Notification(
                    type=notification_type,
                    title="Интенсивное обучение",
                    message=message
                )
                session.add(notification)
                session.commit()

def get_unread_notifications():
    """
    Получает непрочитанные уведомления
    
    Возвращает список уведомлений, отсортированных по дате создания (новые первыми)
    """
    with get_session() as session:
        notifications = session.exec(
            select(Notification).where(Notification.is_read == False).order_by(Notification.created_date.desc())
        ).all()
        return notifications

def mark_notification_read(notification_id):
    """
    Отмечает уведомление как прочитанное
    
    Args:
        notification_id: ID уведомления для отметки как прочитанное
    """
    with get_session() as session:
        notification = session.get(Notification, notification_id)
        if notification:
            notification.is_read = True
            session.add(notification)
            session.commit()

# =============================================================================
# МИГРАЦИЯ ДАННЫХ
# =============================================================================
# Эта функция обновляет существующие данные при изменении структуры базы

def migrate_show_data():
    """
    Обновляет total_watched_episodes для существующих сериалов
    
    Это нужно при добавлении нового поля в модель Show.
    Для существующих записей устанавливает базовое значение на основе текущих серий.
    """
    with get_session() as session:
        shows = session.exec(select(Show)).all()
        for show in shows:
            if show.total_watched_episodes == 0:  # Если поле не заполнено
                # Примерная оценка: (сезон - 1) * среднее_количество_серий + текущие_серии
                # Для простоты используем текущие серии как базовое значение
                show.total_watched_episodes = show.episode
                session.add(show)
        session.commit()

# Выполняем миграцию
migrate_show_data()

# Проверяем уведомления при загрузке страницы
check_deadline_reminders()
check_achievements()

st.title("📔 Мой дневник")
st.caption("Задачи . Сериалы . Книги . Обучение Python")

# =============================================================================
# ПАНЕЛЬ УВЕДОМЛЕНИЙ
# =============================================================================
# Показывает непрочитанные уведомления в верхней части страницы
notifications = get_unread_notifications()
if notifications:
    st.subheader("🔔 Уведомления")
    
    # Группируем уведомления по типам
    deadline_notifications = [n for n in notifications if n.type == "deadline"]
    achievement_notifications = [n for n in notifications if n.type == "achievement"]
    motivation_notifications = [n for n in notifications if n.type == "motivation"]
    
    # Показываем уведомления о дедлайнах
    if deadline_notifications:
        st.warning("⏰ **Приближающиеся дедлайны:**")
        for notif in deadline_notifications:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {notif.message}")
            with col2:
                if st.button("✓", key=f"read_deadline_{notif.id}", help="Отметить как прочитанное"):
                    mark_notification_read(notif.id)
                    st.rerun()
    
    # Показываем достижения
    if achievement_notifications:
        st.success("🎉 **Достижения:**")
        for notif in achievement_notifications:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {notif.message}")
            with col2:
                if st.button("✓", key=f"read_achievement_{notif.id}", help="Отметить как прочитанное"):
                    mark_notification_read(notif.id)
                    st.rerun()
    
    # Показываем мотивационные сообщения
    if motivation_notifications:
        st.info("💪 **Мотивация:**")
        for notif in motivation_notifications:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {notif.message}")
            with col2:
                if st.button("✓", key=f"read_motivation_{notif.id}", help="Отметить как прочитанное"):
                    mark_notification_read(notif.id)
                    st.rerun()
    
    # Кнопка "Отметить все как прочитанные"
    if st.button("📭 Отметить все как прочитанные"):
        for notif in notifications:
            mark_notification_read(notif.id)
        st.rerun()
    
    st.divider()

# =============================================================================
# ПОИСК ПО ВСЕМ РАЗДЕЛАМ
# =============================================================================
# Глобальный поиск по задачам, сериалам, книгам и обучению
search_query = st.text_input("🔍 Поиск по всем разделам", placeholder="Введите название задачи, книги, сериала или темы обучения...")

# Если есть поисковый запрос, показываем результаты
if search_query:
    st.subheader(f"Результаты поиска: '{search_query}'")
    
    with get_session() as session:
        # Поиск в задачах
        tasks = session.exec(select(Task).where(Task.title.contains(search_query))).all()
        # Поиск в сериалах
        shows = session.exec(select(Show).where(Show.title.contains(search_query))).all()
        # Поиск в книгах
        books = session.exec(select(Book).where(Book.title.contains(search_query) | Book.author.contains(search_query))).all()
        # Поиск в обучении
        learning_logs = session.exec(select(LearningLog).where(LearningLog.topic.contains(search_query) | LearningLog.notes.contains(search_query))).all()
    
    # Показываем результаты поиска
    if tasks:
        st.write("**📋 Задачи:**")
        for task in tasks:
            status = "✅" if task.done else "⏰"
            st.write(f"- {status} {task.title} ({task.priority})")
    
    if shows:
        st.write("**🎬 Сериалы:**")
        for show in shows:
            st.write(f"- {show.title} - S{show.season} E{show.episode}")
    
    if books:
        st.write("**📚 Книги:**")
        for book in books:
            progress = f"{book.pages_read}/{book.pages_total}" if book.pages_total > 0 else f"{book.pages_read} стр."
            st.write(f"- {book.title} ({book.author}) - {progress}")
    
    if learning_logs:
        st.write("**🐍 Обучение:**")
        for log in learning_logs:
            st.write(f"- {log.topic} - {log.minutes} мин ({log.log_date})")
    
    if not any([tasks, shows, books, learning_logs]):
        st.info("Ничего не найдено")
    
    st.divider()

# =============================================================================
# БЫСТРЫЕ ДЕЙСТВИЯ
# =============================================================================
# Кнопки для быстрого добавления данных без перехода в соответствующие вкладки
st.subheader("⚡ Быстрые действия")
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

with col1:
    if st.button("📝 Быстрая задача", use_container_width=True):
        st.session_state.quick_task = True
        st.rerun()

with col2:
    if st.button("📚 Добавить книгу", use_container_width=True):
        st.session_state.quick_book = True
        st.rerun()

with col3:
    if st.button("🎬 Новый сериал", use_container_width=True):
        st.session_state.quick_show = True
        st.rerun()

with col4:
    if st.button("🐍 Запись обучения", use_container_width=True):
        st.session_state.quick_learning = True
        st.rerun()

with col5:
    if st.button("❌ Закрыть все", use_container_width=True):
        st.session_state.quick_task = False
        st.session_state.quick_book = False
        st.session_state.quick_show = False
        st.session_state.quick_learning = False
        st.rerun()

# =============================================================================
# БЫСТРЫЕ ФОРМЫ
# =============================================================================
# Раскрывающиеся формы для быстрого добавления данных
# Каждая форма имеет кнопку закрытия для удобства
if st.session_state.get("quick_task", False):
    with st.expander("📝 Быстрая задача", expanded=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.form("quick_task_form", clear_on_submit=True):
                title = st.text_input("Название задачи")
                priority = st.selectbox("Приоритет", ["Низкий", "Средний", "Высокий"])
                submit = st.form_submit_button("Добавить")
                if submit and title.strip():
                    with get_session() as session:
                        task = Task(title=title.strip(), priority=priority, done=False)
                        session.add(task)
                        session.commit()
                    st.success("Задача добавлена!")
                    st.session_state.quick_task = False
                    st.rerun()
        with col2:
            if st.button("❌ Закрыть", use_container_width=True):
                st.session_state.quick_task = False
                st.rerun()

if st.session_state.get("quick_book", False):
    with st.expander("📚 Быстрая книга", expanded=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.form("quick_book_form", clear_on_submit=True):
                title = st.text_input("Название книги")
                author = st.text_input("Автор")
                submit = st.form_submit_button("Добавить")
                if submit and title.strip():
                    with get_session() as session:
                        book = Book(title=title.strip(), author=author.strip())
                        session.add(book)
                        session.commit()
                    st.success("Книга добавлена!")
                    st.session_state.quick_book = False
                    st.rerun()
        with col2:
            if st.button("❌ Закрыть", use_container_width=True):
                st.session_state.quick_book = False
                st.rerun()

if st.session_state.get("quick_show", False):
    with st.expander("🎬 Быстрый сериал", expanded=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.form("quick_show_form", clear_on_submit=True):
                title = st.text_input("Название сериала")
                submit = st.form_submit_button("Добавить")
                if submit and title.strip():
                    with get_session() as session:
                        show = Show(title=title.strip())
                        session.add(show)
                        session.commit()
                    st.success("Сериал добавлен!")
                    st.session_state.quick_show = False
                    st.rerun()
        with col2:
            if st.button("❌ Закрыть", use_container_width=True):
                st.session_state.quick_show = False
                st.rerun()

if st.session_state.get("quick_learning", False):
    with st.expander("🐍 Быстрое обучение", expanded=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            with st.form("quick_learning_form", clear_on_submit=True):
                topic = st.text_input("Тема")
                minutes = st.number_input("Минуты", min_value=1, value=30)
                submit = st.form_submit_button("Добавить")
                if submit and topic.strip():
                    with get_session() as session:
                        learning_log = LearningLog(topic=topic.strip(), minutes=minutes, log_date=date.today())
                        session.add(learning_log)
                        session.commit()
                    st.success("Запись добавлена!")
                    st.session_state.quick_learning = False
                    st.rerun()
        with col2:
            if st.button("❌ Закрыть", use_container_width=True):
                st.session_state.quick_learning = False
                st.rerun()

st.divider()

# =============================================================================
# ОСНОВНЫЕ ВКЛАДКИ ПРИЛОЖЕНИЯ
# =============================================================================
# Создаем вкладки для разных разделов приложения
tabs = st.tabs(["📊 Аналитика", "✅ Задачи", "🎬 Сериалы", "📚 Книги", "🐍 Обучение Python", "📅 Календарь", "🔔 Уведомления"])

with tabs[0]:
    """
    ВКЛАДКА АНАЛИТИКИ
    Показывает статистику и графики по всем разделам
    """
    st.subheader("📊 Аналитика и статистика")
    
    # Получаем данные для аналитики
    with get_session() as session:
        tasks = session.exec(select(Task)).all()
        shows = session.exec(select(Show)).all()
        books = session.exec(select(Book)).all()
        learning_logs = session.exec(select(LearningLog)).all()
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.done])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        st.metric(
            "Задачи", 
            f"{completed_tasks}/{total_tasks}",
            f"{completion_rate:.1f}% выполнено"
        )
    
    with col2:
        total_shows = len(shows)
        total_episodes = sum(s.total_watched_episodes for s in shows)
        
        st.metric(
            "Сериалы", 
            f"{total_shows} сериалов",
            f"{total_episodes} серий просмотрено"
        )
    
    with col3:
        total_books = len(books)
        total_pages = sum(b.pages_read for b in books)
        
        st.metric(
            "Книги", 
            f"{total_books} книг",
            f"{total_pages} страниц прочитано"
        )
    
    with col4:
        total_learning_time = sum(l.minutes for l in learning_logs)
        learning_days = len(set(l.log_date for l in learning_logs))
        
        st.metric(
            "Обучение", 
            f"{total_learning_time} мин",
            f"{learning_days} дней"
        )
    
    st.divider()
    
    # Детальная аналитика
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Прогресс задач")
        
        # Статистика по приоритетам
        priority_stats = {}
        for task in tasks:
            priority = task.priority
            if priority not in priority_stats:
                priority_stats[priority] = {"total": 0, "completed": 0}
            priority_stats[priority]["total"] += 1
            if task.done:
                priority_stats[priority]["completed"] += 1
        
        for priority, stats in priority_stats.items():
            completion_rate = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            st.write(f"**{priority}**: {stats['completed']}/{stats['total']} ({completion_rate:.1f}%)")
            st.progress(completion_rate / 100)
        
        # График обучения по дням
        st.subheader("📚 Активность чтения")
        if books:
            reading_progress = []
            for book in books:
                if book.pages_total > 0:
                    progress = (book.pages_read / book.pages_total) * 100
                    reading_progress.append({
                        "Книга": book.title[:20] + "..." if len(book.title) > 20 else book.title,
                        "Прогресс": progress
                    })
            
            if reading_progress:
                import pandas as pd
                df = pd.DataFrame(reading_progress)
                st.bar_chart(df.set_index("Книга")["Прогресс"])
    
    with col2:
        st.subheader("🎬 Статистика сериалов")
        
        if shows:
            # Топ сериалов по количеству серий
            show_stats = []
            for show in shows:
                show_stats.append({
                    "Сериал": show.title[:15] + "..." if len(show.title) > 15 else show.title,
                    "Текущий сезон": f"S{show.season} E{show.episode}",
                    "Всего серий": show.total_watched_episodes
                })
            
            import pandas as pd
            df = pd.DataFrame(show_stats)
            st.dataframe(df, use_container_width=True)
        
        st.subheader("🐍 Обучение по дням")
        
        if learning_logs:
            # Группируем по дням
            daily_learning = {}
            for log in learning_logs:
                date_str = str(log.log_date)
                if date_str not in daily_learning:
                    daily_learning[date_str] = 0
                daily_learning[date_str] += log.minutes
            
            # Создаем график
            learning_data = []
            for date_str, minutes in sorted(daily_learning.items()):
                learning_data.append({
                    "Дата": date_str,
                    "Минуты": minutes
                })
            
            if learning_data:
                import pandas as pd
                df = pd.DataFrame(learning_data)
                st.line_chart(df.set_index("Дата")["Минуты"])
    
    # Цели и достижения
    st.divider()
    st.subheader("🎯 Цели и достижения")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if total_tasks > 0:
            st.success(f"✅ Выполнено {completed_tasks} задач")
        if completion_rate >= 80:
            st.success("🏆 Отличная продуктивность!")
        elif completion_rate >= 60:
            st.info("📈 Хороший прогресс")
        else:
            st.warning("💪 Можно лучше!")
    
    with col2:
        if total_learning_time > 0:
            avg_daily = total_learning_time / max(learning_days, 1)
            st.info(f"📚 В среднем {avg_daily:.1f} мин/день")
        if total_pages > 0:
            st.info(f"📖 Прочитано {total_pages} страниц")
    
    with col3:
        if total_episodes > 0:
            st.info(f"🎬 Просмотрено {total_episodes} серий")
        if total_books > 0:
            completed_books = len([b for b in books if b.pages_read >= b.pages_total and b.pages_total > 0])
            st.info(f"📚 Завершено {completed_books} книг")

with tabs[1]:
    """
    ВКЛАДКА ЗАДАЧ
    Управление задачами: добавление, выполнение, удаление
    """
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

with tabs[2]:
    """
    ВКЛАДКА СЕРИАЛОВ
    Отслеживание прогресса просмотра сериалов
    """
    st.subheader("Сериалы")
    
    # Форма добавления/обновления
    with st.form("show_form_db", clear_on_submit=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            title = st.text_input("Название сериала")
        with col2:
            season = st.number_input("Сезон", min_value=1, value=1, step=1)
        with col3:
            episode = st.number_input("Серия (текущая)", min_value=0, value=0, step=1)
        total_episodes = st.number_input("Всего серий в сезоне", min_value=0, value=0, step=1)
        submit = st.form_submit_button("Сохранить")
        if submit and title.strip():
            with get_session() as session:
                show = Show(title=title.strip(), season=int(season), episode=int(episode), total=int(total_episodes))
                session.add(show)
                session.commit()
            st.success("Сериал сохранен")
            st.rerun()
    
    st.divider()
    
    # Список сериалов из БД
    with get_session() as session:
        shows = session.exec(select(Show).order_by(Show.title.asc())).all()
    
    if shows:
        for s in shows:
            progress = f"{s.episode}/{s.total}" if s.total else f"{s.episode}"
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{s.title}** — S{s.season} E{progress} (всего: {s.total_watched_episodes})")
            with col2:
                if st.button("➕ Серия", key=f"show_next_{s.id}"):
                    with get_session() as session:
                        obj = session.get(Show, s.id)
                        if obj:
                            obj.episode += 1
                            obj.total_watched_episodes += 1
                            session.add(obj)
                            session.commit()
                    st.rerun()
            with col3:
                if st.button("Новый сезон", key=f"show_new_season_{s.id}"):
                    with get_session() as session:
                        obj = session.get(Show, s.id)
                        if obj:
                            obj.season += 1
                            obj.episode = 0
                            session.add(obj)
                            session.commit()
                    st.rerun()
            with col4:
                if st.button("Удалить", key=f"show_del_{s.id}"):
                    with get_session() as session:
                        obj = session.get(Show, s.id)
                        if obj:
                            session.delete(obj)
                            session.commit()
                    st.rerun()
    else:
        st.info("Пока нет сериалов.")

with tabs[3]:
    """
    ВКЛАДКА КНИГ
    Отслеживание прогресса чтения книг
    """
    st.subheader("Книги")
    
    # Форма добавления/обновления
    with st.form("book_form_db", clear_on_submit=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            title = st.text_input("Название книги")
            author = st.text_input("Автор")
        with col2:
            pages_total = st.number_input("Страниц всего", min_value=0, value=0, step=1)
        with col3:
            pages_read = st.number_input("Прочитано страниц", min_value=0, value=0, step=1)
        submit = st.form_submit_button("Сохранить")
        if submit and title.strip():
            with get_session() as session:
                book = Book(title=title.strip(), author=author.strip(), pages_total=int(pages_total), pages_read=int(pages_read))
                session.add(book)
                session.commit()
            st.success("Книга сохранена")
            st.rerun()
    
    st.divider()
    
    # Список книг из БД
    with get_session() as session:
        books = session.exec(select(Book).order_by(Book.title.asc())).all()
    
    if books:
        for b in books:
            ratio = (b.pages_read / b.pages_total * 100) if b.pages_total else 0
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.markdown(f"**{b.title}** — {b.author}")
                st.progress(min(1.0, ratio / 100.0), text=f"{b.pages_read} из {b.pages_total} ({ratio:.0f}%)")
            with col2:
                new_read = st.number_input("Добавить страниц", min_value=0, value=0, step=1, key=f"book_add_{b.id}")
            with col3:
                if st.button("➕ Прогресс", key=f"book_inc_{b.id}"):
                    with get_session() as session:
                        obj = session.get(Book, b.id)
                        if obj:
                            obj.pages_read += int(new_read)
                            session.add(obj)
                            session.commit()
                    st.rerun()
            with col4:
                if st.button("Удалить", key=f"book_del_{b.id}"):
                    with get_session() as session:
                        obj = session.get(Book, b.id)
                        if obj:
                            session.delete(obj)
                            session.commit()
                    st.rerun()
    else:
        st.info("Пока нет книг.")

with tabs[4]:
    """
    ВКЛАДКА ОБУЧЕНИЯ PYTHON
    Логирование времени изучения Python
    """
    st.subheader("Обучение Python")
    
    # Форма добавления записи
    with st.form("learning_form_db", clear_on_submit=True):
        topic = st.text_input("Тема/курс/глава")
        time_spent = st.number_input("Время (мин)", min_value=0, value=30, step=10)
        notes = st.text_area("Заметки", height=80)
        submit = st.form_submit_button("Добавить запись")
        if submit and topic.strip():
            with get_session() as session:
                learning_log = LearningLog(topic=topic.strip(), minutes=int(time_spent), notes=notes.strip(), log_date=date.today())
                session.add(learning_log)
                session.commit()
            st.success("Запись добавлена")
            st.rerun()
    
    st.divider()
    
    # Список записей обучения из БД
    with get_session() as session:
        learning_logs = session.exec(select(LearningLog).order_by(LearningLog.log_date.desc())).all()
    
    if learning_logs:
        total_min = sum(r.minutes for r in learning_logs)
        st.metric("Всего времени", f"{total_min} мин")
        for r in learning_logs:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{r.topic}** — {r.log_date}")
                if r.notes:
                    st.caption(r.notes)
            with col2:
                st.write(f"{r.minutes} мин")
            with col3:
                if st.button("Удалить", key=f"learn_del_{r.id}"):
                    with get_session() as session:
                        obj = session.get(LearningLog, r.id)
                        if obj:
                            session.delete(obj)
                            session.commit()
                    st.rerun()
    else:
        st.info("Пока нет записей обучения.")

with tabs[5]:
    """
    ВКЛАДКА КАЛЕНДАРЯ
    Календарный вид с задачами и обучением
    """
    st.subheader("Календарь")
    
    # Выбор месяца и года
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀️ Предыдущий"):
            if "current_month" not in st.session_state:
                st.session_state.current_month = date.today().month
                st.session_state.current_year = date.today().year
            if st.session_state.current_month == 1:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            else:
                st.session_state.current_month -= 1
            st.rerun()
    
    with col2:
        if "current_month" not in st.session_state:
            st.session_state.current_month = date.today().month
            st.session_state.current_year = date.today().year
        
        month_name = calendar.month_name[st.session_state.current_month]
        st.markdown(f"<h3 style='text-align: center;'>{month_name} {st.session_state.current_year}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Следующий ▶️"):
            if "current_month" not in st.session_state:
                st.session_state.current_month = date.today().month
                st.session_state.current_year = date.today().year
            if st.session_state.current_month == 12:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            else:
                st.session_state.current_month += 1
            st.rerun()
    
    # Получаем данные для календаря
    with get_session() as session:
        # Задачи с дедлайнами
        tasks = session.exec(
            select(Task).where(Task.due.isnot(None))
        ).all()
        
        # Записи обучения
        learning_logs = session.exec(
            select(LearningLog)
        ).all()
    
    # Создаем календарь
    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
    
    # Заголовки дней недели с улучшенным дизайном
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    header_cols = st.columns(7)
    for i, day_name in enumerate(days):
        with header_cols[i]:
            st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 8px; text-align: center; font-weight: bold; border-radius: 5px; margin: 2px;'>
                    {day_name}
                </div>
            """, unsafe_allow_html=True)
    
    # Создаем календарную сетку с улучшенным дизайном
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div style='height: 80px; margin: 2px;'></div>", unsafe_allow_html=True)
                else:
                    current_date = date(st.session_state.current_year, st.session_state.current_month, day)
                    is_today = current_date == date.today()
                    is_weekend = i >= 5  # Суббота и воскресенье
                    
                    # Стиль для ячейки дня
                    cell_style = "border: 2px solid #007bff; " if is_today else ""
                    cell_style += "background-color: #fff3cd; " if is_weekend else "background-color: #ffffff; "
                    cell_style += "border: 1px solid #dee2e6; padding: 8px; margin: 2px; border-radius: 8px; min-height: 80px;"
                    
                    # Заголовок дня
                    day_style = "color: #dc3545; font-weight: bold; font-size: 16px;" if is_today else "color: #495057; font-weight: bold;"
                    if is_weekend:
                        day_style = "color: #6c757d; font-weight: bold;"
                    
                    st.markdown(f"""
                        <div style='{cell_style}'>
                            <div style='{day_style}; text-align: center; margin-bottom: 5px;'>{day}</div>
                    """, unsafe_allow_html=True)
                    
                    # Показываем задачи на этот день
                    day_tasks = [t for t in tasks if t.due == current_date]
                    if day_tasks:
                        for task in day_tasks:
                            status = "✅" if task.done else "⏰"
                            priority_color = {
                                "Высокий": "#dc3545",
                                "Средний": "#ffc107", 
                                "Низкий": "#28a745"
                            }.get(task.priority, "#28a745")
                            
                            st.markdown(f"""
                                <div style='background-color: {priority_color}; color: white; padding: 3px; margin: 1px; border-radius: 4px; font-size: 9px; text-align: center;'>
                                    {status} {task.title[:12]}{'...' if len(task.title) > 12 else ''}
                                </div>
                            """, unsafe_allow_html=True)
                    
                    # Показываем записи обучения на этот день
                    day_learning = [l for l in learning_logs if l.log_date == current_date]
                    if day_learning:
                        total_minutes = sum(l.minutes for l in day_learning)
                        st.markdown(f"""
                            <div style='background-color: #6f42c1; color: white; padding: 3px; margin: 1px; border-radius: 4px; font-size: 9px; text-align: center;'>
                                🐍 {total_minutes}м
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Детальная информация по выбранной дате
    st.subheader("Детали по дате")
    selected_date = st.date_input("Выберите дату", value=date.today())
    
    if selected_date:
        # Задачи на выбранную дату
        day_tasks = [t for t in tasks if t.due == selected_date]
        if day_tasks:
            st.write("**Задачи на этот день:**")
            for task in day_tasks:
                status = "✅ Выполнено" if task.done else "⏰ В процессе"
                st.write(f"- {task.title} ({task.priority}) - {status}")
                if task.desc:
                    st.caption(f"  {task.desc}")
        else:
            st.info("Нет задач на этот день")
        
        # Записи обучения на выбранную дату
        day_learning = [l for l in learning_logs if l.log_date == selected_date]
        if day_learning:
            st.write("**Обучение в этот день:**")
            total_minutes = 0
            for log in day_learning:
                st.write(f"- {log.topic}: {log.minutes} минут")
                if log.notes:
                    st.caption(f"  {log.notes}")
                total_minutes += log.minutes
            st.metric("Всего времени обучения", f"{total_minutes} минут")
        else:
            st.info("Нет записей обучения на этот день")

with tabs[6]:
    """
    ВКЛАДКА УВЕДОМЛЕНИЙ
    Управление всеми уведомлениями
    """
    st.subheader("🔔 Уведомления")
    
    # Получаем все уведомления (прочитанные и непрочитанные)
    with get_session() as session:
        all_notifications = session.exec(
            select(Notification).order_by(Notification.created_date.desc())
        ).all()
    
    if all_notifications:
        # Фильтры
        col1, col2, col3 = st.columns(3)
        with col1:
            show_type = st.selectbox("Тип уведомления", ["Все", "Дедлайны", "Достижения", "Мотивация"])
        with col2:
            show_status = st.selectbox("Статус", ["Все", "Непрочитанные", "Прочитанные"])
        with col3:
            if st.button("🗑️ Очистить все прочитанные"):
                with get_session() as session:
                    read_notifications = session.exec(
                        select(Notification).where(Notification.is_read == True)
                    ).all()
                    for notif in read_notifications:
                        session.delete(notif)
                    session.commit()
                st.rerun()
        
        # Фильтруем уведомления
        filtered_notifications = all_notifications
        
        if show_type != "Все":
            type_mapping = {"Дедлайны": "deadline", "Достижения": "achievement", "Мотивация": "motivation"}
            filtered_notifications = [n for n in filtered_notifications if n.type == type_mapping[show_type]]
        
        if show_status != "Все":
            if show_status == "Непрочитанные":
                filtered_notifications = [n for n in filtered_notifications if not n.is_read]
            else:
                filtered_notifications = [n for n in filtered_notifications if n.is_read]
        
        # Показываем уведомления
        for notif in filtered_notifications:
            # Определяем цвет и иконку в зависимости от типа
            if notif.type == "deadline":
                if notif.is_read:
                    st.info(f"⏰ {notif.message} - {notif.created_date}")
                else:
                    st.warning(f"⏰ {notif.message} - {notif.created_date}")
            elif notif.type == "achievement":
                if notif.is_read:
                    st.info(f"🎉 {notif.message} - {notif.created_date}")
                else:
                    st.success(f"🎉 {notif.message} - {notif.created_date}")
            else:  # motivation
                if notif.is_read:
                    st.info(f"💪 {notif.message} - {notif.created_date}")
                else:
                    st.info(f"💪 {notif.message} - {notif.created_date}")
            
            # Кнопки действий
            col1, col2, col3 = st.columns([1, 1, 8])
            with col1:
                if not notif.is_read:
                    if st.button("✓ Прочитано", key=f"mark_read_{notif.id}"):
                        mark_notification_read(notif.id)
                        st.rerun()
                else:
                    if st.button("↩️ Непрочитано", key=f"mark_unread_{notif.id}"):
                        with get_session() as session:
                            notification = session.get(Notification, notif.id)
                            if notification:
                                notification.is_read = False
                                session.add(notification)
                                session.commit()
                        st.rerun()
            
            with col2:
                if st.button("🗑️ Удалить", key=f"delete_{notif.id}"):
                    with get_session() as session:
                        notification = session.get(Notification, notif.id)
                        if notification:
                            session.delete(notification)
                            session.commit()
                    st.rerun()
            
            st.divider()
        
        # Статистика
        st.subheader("📊 Статистика уведомлений")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_notifications = len(all_notifications)
            st.metric("Всего уведомлений", total_notifications)
        
        with col2:
            unread_count = len([n for n in all_notifications if not n.is_read])
            st.metric("Непрочитанных", unread_count)
        
        with col3:
            deadline_count = len([n for n in all_notifications if n.type == "deadline"])
            st.metric("Дедлайны", deadline_count)
        
        with col4:
            achievement_count = len([n for n in all_notifications if n.type == "achievement"])
            st.metric("Достижения", achievement_count)
    
    else:
        st.info("Пока нет уведомлений. Добавьте задачи с дедлайнами или выполните несколько задач, чтобы получить уведомления!")
        
        # Показываем подсказки
        st.subheader("💡 Как получить уведомления:")
        st.write("• **Дедлайны**: Добавьте задачи с датами выполнения")
        st.write("• **Достижения**: Выполните 3+ задач в день или завершите книгу")
        st.write("• **Мотивация**: Изучайте Python 60+ минут в день")