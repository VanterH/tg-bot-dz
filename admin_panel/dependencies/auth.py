from fastapi import Request
from fastapi.responses import RedirectResponse
from functools import wraps
from state import sessions

def get_current_user(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in sessions:
        return None
    return sessions[session_token]

def require_auth(func):
    """Декоратор для проверки аутентификации"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = get_current_user(request)
        if not user:
            return RedirectResponse(url="/admin/login", status_code=302)
        return await func(request, *args, **kwargs)
    return wrapper