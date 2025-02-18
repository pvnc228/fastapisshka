from fastapi import FastAPI, Request, HTTPException, Depends, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from database import engine, Base, SessionLocal
from auth import get_db, router as auth_router
from utils import SECRET_KEY, ALGORITHM, verify_password, create_access_token, hash_password
from models import User, Product, Cart
from sqlalchemy.orm import Session
from datetime import timedelta
import datetime
from datetime import datetime
from sqlalchemy import or_

# Создание таблиц в БД
Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI()

app.include_router(auth_router)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
async def index(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Главная страница",
        "user": user
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

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
     return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Проверяем, существует ли пользователь с таким email
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    # Хешируем пароль
    hashed_password = hash_password(password)
    
    # Создаем нового пользователя
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Создаем JWT-токен для автоматического входа после регистрации
    access_token = create_access_token(data={"sub": new_user.email})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

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
    user = db.query(User).filter(User.email == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Пользователь не найден")
    
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный пароль")
    
    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/profile")
async def profile(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "title": "Профиль",
        "user": user
    })

@app.post("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@app.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    query: str = Query(None),
    category: str = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None),
    db: Session = Depends(get_db)
):
    # Если запрос пустой, возвращаем пустой список результатов
    if not query:
        return templates.TemplateResponse("search.html", {
            "request": request,
            "results": [],  # Пустой список
            "query": query,
            "category": category,
            "min_price": min_price,
            "max_price": max_price
        })
    # Базовый запрос
    query_filter = db.query(Product)

    # Фильтр по ключевым словам
    if query:
        query_filter = query_filter.filter(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.category.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%")
            )
        )

    # Фильтр по категории
    if category:
        query_filter = query_filter.filter(Product.category == category)

    # Фильтр по цене
    if min_price is not None:
        query_filter = query_filter.filter(Product.price >= min_price)
    if max_price is not None:
        query_filter = query_filter.filter(Product.price <= max_price)

    # Получаем результаты
    results = query_filter.all()

    return templates.TemplateResponse("search.html", {
        "request": request,
        "results": results,
        "query": query,
        "category": category,
        "min_price": min_price,
        "max_price": max_price
    })
@app.post("/cart/add/{product_id}")
async def add_to_cart(
    product_name: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        return JSONResponse({"detail": "Необходима авторизация"}, status_code=401)

  # Ищем продукт по имени
    product = db.query(Product).filter(Product.name == product_name).first()
    if not product:
        return JSONResponse({"detail": "Продукт не найден"}, status_code=404)
                            
    cart_item = db.query(Cart).filter(
        Cart.user_id == user.id,
        Cart.product_id == product.id
    ).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=user.id, product_id=product.id, products_name=product.name)
        db.add(cart_item)
    
    db.commit()
    return JSONResponse({"message": "Товар добавлен в корзину"})
@app.post("/cart/remove/{product_id}")
async def remove_from_cart(
    product_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(Cart).filter(
        Cart.user_id == user.id,
        Cart.product_id == product_id
    ).first()

    if cart_item:
        if cart_item.quantity > 1:
            # Если количество больше 1, уменьшаем на 1
            cart_item.quantity -= 1
        else:
            # Если количество 1, удаляем продукт из корзины
            db.delete(cart_item)
        
        db.commit()
        return {"message": "Продукт удален из корзины"}
    else:
        raise HTTPException(status_code=404, detail="Продукт не найден в корзине")
@app.get("/cart")
async def view_cart(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_items = db.query(Cart).filter(Cart.user_id == user.id).all()
    return templates.TemplateResponse("cart.html", {
        "request": Request,
        "cart_items": cart_items,
        "title": "Корзина"
    })