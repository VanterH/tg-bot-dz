from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import uuid

from templates_config import templates
from state import sessions  # 👈 импортируем общий словарь

router = APIRouter(prefix="/admin", tags=["auth"])

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = str(uuid.uuid4())
        sessions[token] = {"username": username, "role": "admin"}
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(key="session_token", value=token, httponly=True)
        return response
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Неверные учетные данные"}
    )

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("session_token")
    return response