from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
import os
from urllib.parse import parse_qsl, urlencode, urlparse

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import or_
from sqlmodel import Session, select

from app.db import get_session
from app.models import Note, User
from app.security import hash_password, verify_password

app = FastAPI(title="Notes", version="1.0.0")

SECRET_KEY = os.getenv("SECRET_KEY") or "dev-secret-key-change-me"
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def _redirect_back_with_params(request: Request, default: str, **params: str) -> RedirectResponse:
    ref = request.headers.get("referer")
    if not ref:
        url = default
    else:
        parsed = urlparse(ref)
        # Avoid open redirects: allow relative or same-host URLs only
        if parsed.scheme and parsed.netloc and parsed.netloc != request.url.netloc:
            url = default
        else:
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            query.update({k: v for k, v in params.items() if v is not None})
            url = parsed.path or default
            if query:
                url = f"{url}?{urlencode(query)}"

    return RedirectResponse(url=url, status_code=303)


def session_dep() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session


def get_current_user(request: Request, session: Session) -> User | None:
    user_id = None
    try:
        user_id = request.session.get("user_id")
    except Exception:
        user_id = None
    if not user_id:
        return None
    return session.get(User, int(user_id))


def _require_user(request: Request, session: Session) -> User:
    user = get_current_user(request, session)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def _can_access_note(user: User, note: Note) -> bool:
    if user.is_superuser:
        return True
    return note.user_id == user.id


@app.on_event("startup")
def ensure_admin_user() -> None:
    # Create default superuser if missing
    with get_session() as session:
        admin = session.exec(select(User).where(User.username == "admin")).first()
        if admin:
            return
        admin = User(username="admin", password_hash=hash_password("admin"), is_superuser=True)
        session.add(admin)
        session.commit()


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: str | None = None,
    archived: int = 0,
    session: Session = Depends(session_dep),
):
    user = _require_user(request, session)
    archived_view = archived == 1
    stmt = select(Note)
    stmt = stmt.where(Note.archived == archived_view)

    if not user.is_superuser:
        stmt = stmt.where(Note.user_id == user.id)

    q_clean = (q or "").strip()
    if q_clean:
        like = f"%{q_clean}%"
        stmt = stmt.where(or_(Note.title.ilike(like), Note.content.ilike(like)))

    stmt = stmt.order_by(Note.pinned.desc(), Note.updated_at.desc())
    notes = session.exec(stmt).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notes": notes,
            "q": q_clean,
            "archived_view": archived_view,
            "user": user,
        },
    )


@app.get("/export/json")
def export_notes_json(request: Request, session: Session = Depends(session_dep)):
    user = _require_user(request, session)
    stmt = select(Note).order_by(Note.updated_at.desc())
    if not user.is_superuser:
        stmt = stmt.where(Note.user_id == user.id)
    notes = session.exec(stmt).all()
    payload = [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "created_at": n.created_at.isoformat() + "Z",
            "updated_at": n.updated_at.isoformat() + "Z",
        }
        for n in notes
    ]

    return JSONResponse(
        content={"notes": payload},
        headers={"Content-Disposition": "attachment; filename=notes.json"},
    )


@app.post("/notes")
def create_note(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    session: Session = Depends(session_dep),
):
    user = _require_user(request, session)
    now = datetime.utcnow()
    note = Note(
        user_id=user.id,
        title=title.strip(),
        content=content,
        pinned=False,
        archived=False,
        created_at=now,
        updated_at=now,
    )
    session.add(note)
    session.commit()
    return RedirectResponse(url="/?created=1", status_code=303)


@app.get("/notes/{note_id}", response_class=HTMLResponse)
def edit_note_page(
    request: Request,
    note_id: int,
    session: Session = Depends(session_dep),
):
    user = _require_user(request, session)
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not _can_access_note(user, note):
        raise HTTPException(status_code=403, detail="Forbidden")
    return templates.TemplateResponse(
        "edit.html",
        {
            "request": request,
            "note": note,
            "user": user,
        },
    )


@app.post("/notes/{note_id}")
def update_note(
    note_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    session: Session = Depends(session_dep),
):
    user = _require_user(request, session)
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not _can_access_note(user, note):
        raise HTTPException(status_code=403, detail="Forbidden")

    note.title = title.strip()
    note.content = content
    note.updated_at = datetime.utcnow()

    session.add(note)
    session.commit()
    return RedirectResponse(url="/?updated=1", status_code=303)


@app.post("/notes/{note_id}/delete")
def delete_note(note_id: int, request: Request, session: Session = Depends(session_dep)):
    user = _require_user(request, session)
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not _can_access_note(user, note):
        raise HTTPException(status_code=403, detail="Forbidden")
    session.delete(note)
    session.commit()
    return RedirectResponse(url="/?deleted=1", status_code=303)


@app.post("/notes/{note_id}/pin")
def toggle_pin(note_id: int, request: Request, session: Session = Depends(session_dep)):
    user = _require_user(request, session)
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not _can_access_note(user, note):
        raise HTTPException(status_code=403, detail="Forbidden")

    note.pinned = not bool(note.pinned)
    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()

    return _redirect_back_with_params(
        request,
        default="/",
        pinned="1" if note.pinned else None,
        unpinned="1" if not note.pinned else None,
    )


@app.post("/notes/{note_id}/archive")
def toggle_archive(note_id: int, request: Request, session: Session = Depends(session_dep)):
    user = _require_user(request, session)
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not _can_access_note(user, note):
        raise HTTPException(status_code=403, detail="Forbidden")

    note.archived = not bool(note.archived)
    # Keep archive list clean: archived notes are not pinned
    if note.archived:
        note.pinned = False
    note.updated_at = datetime.utcnow()
    session.add(note)
    session.commit()

    return _redirect_back_with_params(
        request,
        default="/",
        archived_action="1" if note.archived else None,
        unarchived_action="1" if not note.archived else None,
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(session_dep),
):
    username_clean = username.strip()
    user = session.exec(select(User).where(User.username == username_clean)).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль", "username": username_clean},
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(session_dep),
):
    username_clean = username.strip()
    if len(username_clean) < 3:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Логин должен быть минимум 3 символа", "username": username_clean},
            status_code=400,
        )
    if len(password) < 4:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароль должен быть минимум 4 символа", "username": username_clean},
            status_code=400,
        )

    existing = session.exec(select(User).where(User.username == username_clean)).first()
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Такой логин уже занят", "username": username_clean},
            status_code=400,
        )

    user = User(username=username_clean, password_hash=hash_password(password), is_superuser=False)
    session.add(user)
    session.commit()
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    try:
        request.session.clear()
    except Exception:
        pass
    return RedirectResponse(url="/login", status_code=303)
