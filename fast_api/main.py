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
from sqlalchemy.orm import Session, joinedload
from datetime import timedelta, datetime
from sqlalchemy import or_
from typing import List
from werkzeug.security import check_password_hash
Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()
app.include_router(auth_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SAFE_SEARCH_PATTERN = re.compile(r'^[a-zA-Zа-яА-Я0-9\s\-]{1,100}$')

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

async def get_current_profile(token: str = Cookie(None, alias="access_token"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> UserResponse:
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

    user = db.query(User).options(joinedload(User.reviews)).filter(User.id == current_user.id).first()
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
    products = db.query(Product).all()
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

    
    if query:
        if not SAFE_SEARCH_PATTERN.match(query):
            raise HTTPException(
                status_code=400,
                detail="Недопустимые символы в запросе"
            )
        
        query_lower = query.lower()
        for keyword in BLACKLISTED_KEYWORDS:
            if keyword in query_lower:
                raise HTTPException(
                    status_code=400,
                    detail="Недопустимый запрос"
                )

    valid_categories = ["Автострахование", "Имущество", "Комплексное страхование", "Страхование бизнеса"]
    if category and category not in valid_categories:
        raise HTTPException(status_code=400, detail="Недопустимая категория")

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


@app.post("/cart/increase/{product_name}")
async def increase_quantity(
    product_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(Cart).filter(
        Cart.user_id == user.id,
        Cart.products_name == product_name
    ).first()
    if cart_item:
        cart_item.quantity += 1
        db.commit()
        return {"message": "Количество увеличено"}
    else:
        raise HTTPException(status_code=404, detail="Товар не найден в корзине")

@app.post("/cart/decrease/{product_name}")
async def decrease_quantity(
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
            db.commit()
            return {"message": "Количество уменьшено"}
        else:
            db.delete(cart_item)
            db.commit()
            return {"message": "Товар удален из корзины"}
    else:
        raise HTTPException(status_code=404, detail="Товар не найден в корзине")

@app.get("/cart")
async def view_cart(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(Cart).join(Product).filter(Cart.user_id == user.id).all()
    return templates.TemplateResponse("cart.html", {
        "request": request,
        "cart_items": cart_items,
        "title": "Корзина",
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
async def edit_profile(request: Request,
    user: User = Depends(get_current_profile)):
    return templates.TemplateResponse("edit_profile.html", {
        "request": request,
        "user": user,
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
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return templates.TemplateResponse("product.html", {
        "request": request,
        "product": product,
        "show_slider": False 
    })
@app.post("/submit-review")
async def submit_review(
    request: Request,
    product_id: int = Form(...),  
    author: str = Form(...),     
    text: str = Form(...),        
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    new_review = Review(
        user_id=user.id,
        product_id=product_id,
        author=author,
        text=text
    )

    db.add(new_review)
    db.commit()
    return RedirectResponse(url=f"/catalog/{product_id}", status_code=303)

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

@app.post("/admin/add-review")
async def add_review(
    author: str = Form(...),
    product_id: int = Form(...),
    text: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_review = Review(
        author=author,
        product_id=product_id,
        text=text,
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
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    users = db.query(User).all()
    products = db.query(Product).all()
    carts = db.query(Cart).all()
    reviews = db.query(Review).all()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "products": products,
        "carts": carts,
        "reviews": reviews
    })

@app.post("/admin/delete-user/{user_id}")
async def delete_user(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    db.delete(db_user)
    db.commit()
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/reset-password/{user_id}")
async def reset_password(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
 
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    

    db_user.hashed_password = hash_password("0000")
    db.commit()
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/delete-product/{product_id}")
async def delete_product(
    product_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
  
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
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
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    product.name = name
    product.category = category
    product.price = price
    product.description = description
    db.commit()
    return RedirectResponse("/admin", status_code=303)
@app.post("/admin/add-product")
async def add_product(
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    description: str = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_product = Product(name=name, category=category, price=price, description=description)
    db.add(new_product)
    db.commit()
    return RedirectResponse("/admin", status_code=303)
@app.post("/admin/delete-cart/{cart_id}")
async def delete_cart(
    cart_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Корзина не найдена")
    db.delete(cart)
    db.commit()
    return RedirectResponse("/admin", status_code=303)
@app.post("/admin/delete-review/{review_id}")
async def delete_review(
    review_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    db.delete(review)
    db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.post("/edit-profile/personal-info")
async def edit_personal_info(
    full_name: str = Form(...),
    phone_number: str = Form(...),
    date_of_birth: str = Form(...),
    password: str = Form(...),
    user: User = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    # Проверка текущего пароля
    if not check_password_hash(user.hashed_password, password):
        raise HTTPException(status_code=400, detail="Неверный пароль")
    
    # Обновление данных
    user.full_name = full_name
    user.phone_number = phone_number
    user.date_of_birth = date_of_birth
    db.commit()
    return {"message": "Личные данные обновлены"}