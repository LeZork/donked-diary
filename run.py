#!/usr/bin/env python3
"""
Скрипт для запуска приложения дневника
"""

import subprocess
import sys
import os

def main():
    """Запуск Streamlit приложения"""
    try:
        # Переходим в директорию с приложением
        app_dir = os.path.join(os.path.dirname(__file__), 'app')
        
        # Запускаем Streamlit
        cmd = [sys.executable, '-m', 'streamlit', 'run', 'main.py']
        subprocess.run(cmd, cwd=app_dir, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске приложения: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nПриложение остановлено пользователем")
        sys.exit(0)

if __name__ == "__main__":
    main()
