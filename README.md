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

Перед первым запуском (и после изменений схемы) применить миграции:

```powershell
C:/Users/nurmuhammad/Projects/Uzinfocom/my_project/.venv/Scripts/python.exe -m scripts.migrate
```

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

## Миграции (Alembic)

- Создать новую миграцию (после изменения моделей):

```powershell
alembic revision --autogenerate -m "message"
```

- Применить миграции:

```powershell
alembic upgrade head
```

Если база уже существовала и таблицы были созданы раньше без Alembic, то один раз нужно сделать baseline:

```powershell
alembic stamp head
```

## DigitalOcean App Platform

Чтобы миграции применялись автоматически при деплое, в Run Command можно поставить:

`python -m scripts.migrate && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
