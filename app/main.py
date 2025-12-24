from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.models import Note

app = FastAPI(title="Notes", version="1.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def session_dep() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session


@app.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(session_dep)):
    notes = session.exec(select(Note).order_by(Note.updated_at.desc())).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notes": notes,
        },
    )


@app.get("/export/json")
def export_notes_json(session: Session = Depends(session_dep)):
    notes = session.exec(select(Note).order_by(Note.updated_at.desc())).all()
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
    title: str = Form(...),
    content: str = Form(""),
    session: Session = Depends(session_dep),
):
    now = datetime.utcnow()
    note = Note(title=title.strip(), content=content, created_at=now, updated_at=now)
    session.add(note)
    session.commit()
    return RedirectResponse(url="/?created=1", status_code=303)


@app.get("/notes/{note_id}", response_class=HTMLResponse)
def edit_note_page(
    request: Request,
    note_id: int,
    session: Session = Depends(session_dep),
):
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return templates.TemplateResponse(
        "edit.html",
        {
            "request": request,
            "note": note,
        },
    )


@app.post("/notes/{note_id}")
def update_note(
    note_id: int,
    title: str = Form(...),
    content: str = Form(""),
    session: Session = Depends(session_dep),
):
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = title.strip()
    note.content = content
    note.updated_at = datetime.utcnow()

    session.add(note)
    session.commit()
    return RedirectResponse(url="/?updated=1", status_code=303)


@app.post("/notes/{note_id}/delete")
def delete_note(note_id: int, session: Session = Depends(session_dep)):
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    session.delete(note)
    session.commit()
    return RedirectResponse(url="/?deleted=1", status_code=303)
