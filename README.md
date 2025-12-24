# FastAPI Notes

Небольшое приложение для заметок (PostgreSQL + красивый UI на Tailwind CDN).

## Запуск (Windows / PowerShell)

1) Создать виртуальное окружение и установить зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Поднять PostgreSQL (Docker):

```powershell
docker compose up -d
```

3) Убедиться, что в `.env` задан `DATABASE_URL` (пример):

```dotenv
DATABASE_URL=postgresql+psycopg://notes:notespass@localhost:5433/notes
```

4) Запустить сервер:

```powershell
uvicorn app.main:app --reload
```

Открыть в браузере: http://127.0.0.1:8000

## Что умеет
- Список заметок
- Создание заметки
- Редактирование
- Удаление

База данных: PostgreSQL (настройка через `DATABASE_URL`).
