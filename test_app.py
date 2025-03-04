# tests/test_app.py
import pytest
from app import create_app, db
from app.models import User

@pytest.fixture(scope='module')
def test_client():
    # Создаем тестовое приложение
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Используем базу данных в памяти для тестов
    app.config['TESTING'] = True

    # Создаем все таблицы в базе данных для тестов
    with app.app_context():
        db.create_all()

    # Создаем тестовый клиент
    yield app.test_client()

    # Очистка после завершения тестов
    with app.app_context():
        db.drop_all()

def test_user_login(test_client):
    # Тестирование страницы входа
    response = test_client.post('/login', data={'username': 'testuser', 'password': 'password'})
    assert response.status_code == 200
    assert 'Добро пожаловать в личный дневник' in response.data.decode('utf-8')  # Используем обычную строку

def test_register_new_user(test_client):
    # Тестирование регистрации нового пользователя
    response = test_client.post('/register', data={'username': 'newuser', 'password': 'password'})
    assert response.status_code == 302  # Проверка редиректа после успешной регистрации

def test_journal_page(test_client):
    # Тестирование страницы дневника
    response = test_client.get('/journal')
    assert response.status_code == 200  # Проверка успешного ответа
