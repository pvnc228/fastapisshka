// Обновление навигации
function updateNav() {
    const token = localStorage.getItem('token');
    const loginLink = document.getElementById('login-link');
    const registerLink = document.getElementById('register-link');
    const profileLink = document.getElementById('profile-link');
    const logoutBtn = document.getElementById('logout-btn');

    if (token) {
        loginLink.style.display = 'none';
        registerLink.style.display = 'none';
        profileLink.style.display = 'inline';
        logoutBtn.style.display = 'inline';
    } else {
        loginLink.style.display = 'inline';
        registerLink.style.display = 'inline';
        profileLink.style.display = 'none';
        logoutBtn.style.display = 'none';
    }
}

// Логин
async function login(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('token', data.access_token);
            updateNav();
            window.location.href = '/profile';
        } else {
            document.getElementById('login-error').textContent = data.detail;
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Регистрация
async function register(event) {
    event.preventDefault();
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        if (response.ok) {
            alert('Registration successful! Please login.');
            window.location.href = '/login';
        } else {
            const error = await response.json();
            document.getElementById('register-error').textContent = error.detail;
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Загрузка профиля
async function loadProfile() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        const response = await fetch('/users/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('profile-email').textContent = user.email;
        } else {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Выход
function logout() {
    localStorage.removeItem('token');
    updateNav();
    window.location.href = '/';
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    updateNav();
    if (window.location.pathname === '/profile') {
        loadProfile();
    }
});