# FastAPI Notes

Небольшое приложение для заметок (SQLite + красивый UI на Tailwind CDN).

## Запуск (Windows / PowerShell)

1) Создать виртуальное окружение и установить зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Запустить сервер:

```powershell
uvicorn app.main:app --reload
```

Открыть в браузере: http://127.0.0.1:8000

## Что умеет
- Список заметок
- Создание заметки
- Редактирование
- Удаление

База данных создаётся автоматически: `app/data/notes.db`
