import re
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Query, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from database import engine, Base, SessionLocal
from schemas import UserCreate, UserResponse, Token, EditEmailRequest, EditPasswordRequest
from auth import get_db, router as auth_router
from utils import SECRET_KEY, ALGORITHM, verify_password, create_access_token, hash_password
from models import Review, User, Product, Cart
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from sqlalchemy import or_
from typing import List
Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()
app.include_router(auth_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# Регулярка для разрешенных символов (только буквы, цифры, пробелы и дефисы)
SAFE_SEARCH_PATTERN = re.compile(r'^[a-zA-Zа-яА-Я0-9\s\-]{1,100}$')

# Запрещенные SQL-ключевые слова
BLACKLISTED_KEYWORDS = [
    "drop", "delete", "insert", "update", "truncate",
    "alter", "create", "grant", "revoke", "shutdown"
]

async def get_current_user(request: Request, token: str = Cookie(None, alias="access_token"), db: Session = Depends(get_db) ):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:   
        return RedirectResponse(url="/login", status_code=303)


    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        return RedirectResponse(url="/login", status_code=303)


    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_profile(token: str = Cookie(None, alias="access_token"), db: Session = Depends(get_db)) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return UserResponse(
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        date_of_birth=user.date_of_birth
    )



@app.get("/")
async def index(request: Request,
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)):
    products = db.query(Product).limit(6).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Главная страница",
        "user": user,
        "products": products,
        "show_slider": True
    })

@app.get("/catalog")
async def catalog(
    request: Request,
    db: Session = Depends(get_db)
):
    # Получаем все продукты из базы данных
    products = db.query(Product).all()
    
    # Передаем продукты в шаблон
    return templates.TemplateResponse("page1.html", {
        "request": request,
        "title": "Каталог услуг",
        "products": products,
        "show_slider": False 
    })

@app.get("/contacts")
async def contacts(request: Request):
    return templates.TemplateResponse("page2.html", {
        "request": request,
        "title": "Контакты",
        "show_slider": False 
    })

@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("page3.html", {
        "request": request,
        "title": "О компании",
        "show_slider": False 
    })

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    return templates.TemplateResponse("base.html", {
        "request": request,
        "show_slider": True
        })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request,
        "show_slider": False })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request,
        "show_slider": False })

@app.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    phone_number: str = Form(None),
    date_of_birth: str = Form(None),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    hashed_password = hash_password(password)
    dob = None
    if date_of_birth:
        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректный формат даты рождения. Используйте YYYY-MM-DD.")

    new_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        phone_number=phone_number,
        date_of_birth=dob
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    return response

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
    redirect_url = "/admin" if user.role == "admin" else "/"
    
    response = RedirectResponse(redirect_url, status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="Lax")
    return response

@app.get("/profile", response_model=UserResponse)
async def profile(request: Request, user: UserResponse = Depends(get_current_profile)):
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "title": "Профиль",
        "user": user,
        "show_slider": False 
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
    if not query:
        return templates.TemplateResponse("search.html", {
            "request": request,
            "results": [],
            "query": query,
            "category": category,
            "min_price": min_price,
            "max_price": max_price
        })

    query_filter = db.query(Product)

    # if query:
    #     query_filter = query_filter.filter(
    #         or_(
    #             Product.name.ilike(f"%{query}%"),
    #             Product.category.ilike(f"%{query}%"),
    #             Product.description.ilike(f"%{query}%")
    #         )
    #     )
    # Валидация поискового запроса
    if query:
        # Проверка на запрещенные символы
        if not SAFE_SEARCH_PATTERN.match(query):
            raise HTTPException(
                status_code=400,
                detail="Недопустимые символы в запросе"
            )
        
        # Проверка на SQL-инъекции
        query_lower = query.lower()
        for keyword in BLACKLISTED_KEYWORDS:
            if keyword in query_lower:
                raise HTTPException(
                    status_code=400,
                    detail="Недопустимый запрос"
                )

    # Валидация категории
    valid_categories = ["Автострахование", "Имущество", "Комплексное страхование", "Страхование бизнеса"]
    if category and category not in valid_categories:
        raise HTTPException(status_code=400, detail="Недопустимая категория")

    # Валидация цен
    if min_price and min_price < 0:
        raise HTTPException(status_code=400, detail="Минимальная цена не может быть отрицательной")
    
    if max_price and max_price < 0:
        raise HTTPException(status_code=400, detail="Максимальная цена не может быть отрицательной")

    if category:
        query_filter = query_filter.filter(Product.category == category)

    if min_price is not None:
        query_filter = query_filter.filter(Product.price >= min_price)
    if max_price is not None:
        query_filter = query_filter.filter(Product.price <= max_price)

    results = query_filter.all()

    return templates.TemplateResponse("search.html", {
        "request": request,
        "results": results,
        "query": query,
        "category": category,
        "min_price": min_price,
        "max_price": max_price,
        "show_slider": False 
    })

@app.post("/cart/add/{product_name}")
async def add_to_cart(
    request: Request,
    product_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        return JSONResponse({"detail": "Необходима авторизация"}, status_code=401)

    product = db.query(Product).filter(Product.name == product_name).first()
    if not product:
        return JSONResponse({"detail": "Продукт не найден"}, status_code=404)

    cart_item = db.query(Cart).filter(
        Cart.user_id == user.id,
        Cart.product_id == product.id,
        Cart.products_name == product.name
    ).first()

    if not cart_item:
        cart_item = Cart(user_id=user.id, product_id=product.id, products_name=product.name)
        db.add(cart_item)
        db.commit()

    return {
        "message": "Товар добавлен",
        "cart_items_count": db.query(Cart).filter_by(user_id=user.id).count()
    }

@app.post("/cart/remove/{product_name}")
async def remove_from_cart(
    product_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(Cart).filter(
        Cart.user_id == user.id,
        Cart.products_name == product_name
    ).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.delete(cart_item)
        db.commit()
        return {"message": "Продукт удален из корзины"}
    else:
        raise HTTPException(status_code=404, detail="Продукт не найден в корзине")

@app.get("/cart")
async def view_cart(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(Cart).join(Product).filter(Cart.user_id == user.id).all()
    return templates.TemplateResponse("cart.html", {
        "request": request,
        "cart_items": cart_items,
        "title": "Корзина",
        "show_slider": False 
    })

@app.get("/debug/users", response_class=HTMLResponse)
async def debug_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("debug_users.html", {
        "request": request,
        "users": users,
        "show_slider": False 
    })

@app.post("/edit-profile/email")
async def edit_email(
    request: EditEmailRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный пароль")

    existing_user = db.query(User).filter(User.email == request.new_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    user.email = request.new_email
    db.commit()
    db.refresh(user)

    return {"message": "Email успешно изменен"}

@app.post("/edit-profile/password")
async def edit_password(
    request: EditPasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный пароль")

    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    user.hashed_password = hash_password(request.new_password)
    db.commit()
    db.refresh(user)

    return {"message": "Пароль успешно изменен"}

@app.get("/edit-profile/")
async def edit_profile(request: Request):
    return templates.TemplateResponse("edit_profile.html", {
        "request": request,
        "show_slider": False 
    })

@app.get("/_cart_items", response_class=HTMLResponse)
async def get_cart_items(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_items = db.query(Cart).filter(Cart.user_id == user.id).all()
    return templates.TemplateResponse("_cart_items.html", {
        "request": request,
        "cart_items": cart_items,
        "show_slider": False 
    })

@app.post("/debug/delete-users")
async def delete_all_users_except_current(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(User).filter(User.id != user.id).delete()
    db.commit()
    return {"message": "Все пользователи, кроме активного, удалены."}
@app.post("/reviews/add")
async def add_review(
    product_id: int = Form(...),
    text: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_review = Review(
        text=text,
        user_id=user.id,
        product_id=product_id
    )
    db.add(new_review)
    db.commit()
    return RedirectResponse(f"/product/{product_id}", status_code=303)
@app.get("/catalog/{product_id}", response_class=HTMLResponse)
async def product_page(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    # Получаем товар из базы данных по его ID
    product = db.query(Product).filter(Product.id == product_id).first()
    
    # Если товар не найден, возвращаем ошибку 404
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Возвращаем шаблон с данными о товаре
    return templates.TemplateResponse("product.html", {
        "request": request,
        "product": product,
        "show_slider": False 
    })
@app.post("/submit-review")
async def submit_review(
    request: Request,
    product_id: int = Form(...),  # ID товара, к которому относится отзыв
    author: str = Form(...),      # Имя автора отзыва
    text: str = Form(...),        # Текст отзыва,        # Текст отзыва
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем, существует ли товар с таким ID
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Создаем новый отзыв
    new_review = Review(
        user_id=user.id,
        product_id=product_id,
        author=author,
        text=text
    )

    # Сохраняем отзыв в базе данных
    db.add(new_review)
    db.commit()

    # Перенаправляем пользователя обратно на страницу товара
    return RedirectResponse(url=f"/catalog/{product_id}", status_code=303)

# CRUD для корзин
@app.post("/admin/add-cart")
async def add_cart(
    user_id: int = Form(...),
    product_id: int = Form(...),
    quantity: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_cart = Cart(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity
    )
    db.add(new_cart)
    db.commit()
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/edit-cart/{cart_id}")
async def edit_cart(
    cart_id: int,
    quantity: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Запись корзины не найдена")
    cart.quantity = quantity
    db.commit()
    return RedirectResponse("/admin", status_code=303)

# CRUD для отзывов
@app.post("/admin/add-review")
async def add_review(
    author: str = Form(...),
    product_id: int = Form(...),
    text: str = Form(...),
    rating: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_review = Review(
        author=author,
        product_id=product_id,
        text=text,
        rating=rating
    )
    db.add(new_review)
    db.commit()
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/edit-review/{review_id}")
async def edit_review(
    review_id: int,
    text: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    review.text = text
    db.commit()
    return RedirectResponse("/admin", status_code=303)
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка роли пользователя
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    # Получение данных из базы
    users = db.query(User).all()
    products = db.query(Product).all()
    carts = db.query(Cart).all()
    reviews = db.query(Review).all()

    # Возвращаем шаблон с данными
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "products": products,
        "carts": carts,
        "reviews": reviews
    })

# Удаление пользователя
@app.post("/admin/delete-user/{user_id}")
async def delete_user(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка роли пользователя
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    # Поиск пользователя
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Удаление пользователя
    db.delete(db_user)
    db.commit()
    return RedirectResponse("/admin", status_code=303)

# Сброс пароля пользователя
@app.post("/admin/reset-password/{user_id}")
async def reset_password(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка роли пользователя
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    # Поиск пользователя
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Сброс пароля
    db_user.hashed_password = hash_password("0000")
    db.commit()
    return RedirectResponse("/admin", status_code=303)

# Удаление продукта
@app.post("/admin/delete-product/{product_id}")
async def delete_product(
    product_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверка роли пользователя
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    # Поиск продукта
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Удаление продукта
    db.delete(product)
    db.commit()
    return RedirectResponse("/admin", status_code=303)
@app.post("/admin/edit-product/{product_id}")
async def edit_product(
    product_id: int,
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    description: str = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Проверка прав доступа
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    # 2. Поиск продукта в базе данных
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # 3. Обновление данных продукта
    product.name = name
    product.category = category
    product.price = price
    product.description = description
    
    # 4. Сохранение изменений в базе данных
    db.commit()
    
    # 5. Перенаправление обратно на админ-панель
    return RedirectResponse("/admin", status_code=303)