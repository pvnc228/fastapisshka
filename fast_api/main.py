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

Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()
app.include_router(auth_router)

async def get_current_user(token: str = Cookie(None, alias="access_token"), db: Session = Depends(get_db)):
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

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Главная страница",
        "user": user
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
        "products": products  # Передаем список продуктов
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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_count = db.query(Cart).filter_by(user_id=user.id).count()
    return templates.TemplateResponse("base.html", {"request": request, "cart_items_count": cart_count})

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
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="Lax")
    return response

@app.get("/profile", response_model=UserResponse)
async def profile(request: Request, user: UserResponse = Depends(get_current_profile)):
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

    if query:
        query_filter = query_filter.filter(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.category.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%")
            )
        )

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
        "max_price": max_price
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
        "title": "Корзина"
    })

@app.get("/debug/users", response_class=HTMLResponse)
async def debug_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("debug_users.html", {
        "request": request,
        "users": users
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
        "request": request
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
        "cart_items": cart_items
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
        "product": product
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