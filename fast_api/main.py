from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from database import engine, Base, SessionLocal
from auth import get_db, router as auth_router
from utils import SECRET_KEY, ALGORITHM, verify_password
from models import User
from sqlalchemy.orm import Session
# Создание таблиц в БД
Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI()

app.include_router(auth_router)


# Добавьте в зависимости
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Защищенный эндпоинт для примера
@app.get("/secure-data", dependencies=[Depends(oauth2_scheme)])
async def secure_data():
    return {"message": "This is protected data!"}



# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Ваши существующие эндпоинты API...
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Главная страница"
    })

@app.get("/catalog")
async def catalog(request: Request):
    return templates.TemplateResponse("page1.html", {
        "request": request,
        "title": "Каталог услуг"
    })

@app.get("/contacts")
async def contacts(request: Request):
    return templates.TemplateResponse("page2.html", {
        "request": request,
        "title": "Контакты"
    })

@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("page3.html", {
        "request": request,
        "title": "О компании"
    })
# Добавляем роуты для HTML страниц
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

# @app.get("/login", response_class=HTMLResponse)
# async def login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


# Новый эндпоинт
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email}


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Ищем пользователя в базе данных
    user = db.query(User).filter(User.email == username).first()
    
    # Если пользователь не найден
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким логином не найден"
        )
    
    # Проверяем пароль
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Неверный пароль"
        )
    
    # Если всё успешно, перенаправляем на главную страницу
    return RedirectResponse("/", status_code=303)

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})