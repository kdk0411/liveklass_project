import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from auth import authenticate_user, register_user
from events import emit_event

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "changeme"))

_ALLOWED_EVENTS = {"page_view", "purchase", "error"}
_INDEX_HTML = (Path(__file__).parent / "templates" / "index.html").read_text()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/me")
async def me(request: Request):
    username = request.session.get("username")
    if not username:
        return JSONResponse({"logged_in": False})
    return JSONResponse({"logged_in": True, "username": username})


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(_INDEX_HTML)


@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    try:
        ok, message = register_user(username, password)
        if ok:
            return JSONResponse({"success": True})
        return JSONResponse({"success": False, "message": message}, status_code=400)
    except Exception:
        logger.exception("POST /register error")
        return JSONResponse({"success": False, "message": "server_error"}, status_code=500)


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        ok, message = authenticate_user(username, password)
        if ok:
            request.session["username"] = username
            return JSONResponse({"success": True, "username": username})
        return JSONResponse({"success": False, "message": message}, status_code=401)
    except Exception:
        logger.exception("POST /login error")
        return JSONResponse({"success": False, "message": "server_error"}, status_code=500)


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse({"success": True})


@app.post("/trigger/{event_type}")
async def trigger_event(request: Request, event_type: str):
    username = request.session.get("username")
    if not username:
        return JSONResponse({"success": False, "message": "not_logged_in"}, status_code=401)
    if event_type not in _ALLOWED_EVENTS:
        return JSONResponse({"success": False, "message": "unknown_event_type"}, status_code=400)

    status = "fail" if event_type == "error" else "success"
    emit_event(event_type, username, status, page="/dashboard")
    return JSONResponse({"success": True})
