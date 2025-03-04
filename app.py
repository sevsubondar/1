from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy import or_
from flask_wtf.csrf import CSRFProtect
# Инициализация объектов
app = Flask(__name__)
# csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'  # База данных для дневника
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)
# Модели данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    entries = db.relationship('Entry', backref='author', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    morning_mood = db.Column(db.String(10), nullable=True)  # Эмоция утра (смайлик)
    afternoon_mood = db.Column(db.String(10), nullable=True)  # Эмоция дня (смайлик)
    evening_mood = db.Column(db.String(10), nullable=True)  # Эмоция вечера (смайлик)
    night_mood = db.Column(db.String(10), nullable=True)  # Эмоция ночи (смайлик)
    note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Entry by {self.author.username} on {self.date}>"


# Функция загрузки пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Основные маршруты
@app.route('/journal', methods=['GET', 'POST'])
@login_required
def journal():
    today = datetime.today().date()  # Получаем сегодняшнюю дату

    # Получаем выбранное настроение из параметров
    selected_mood = request.args.get('mood')  # Получаем выбранное настроение

    # Фильтрация записей по сегодняшней дате
    entries = Entry.query.filter_by(user_id=current_user.id, date=today)

    # Если есть фильтрация по настроению
    if selected_mood:
        entries = entries.filter(or_(
            Entry.morning_mood == selected_mood,
            Entry.afternoon_mood == selected_mood,
            Entry.evening_mood == selected_mood,
            Entry.night_mood == selected_mood
        ))

    entries = entries.all()

    # Собираем данные для графика по каждому настроению
    moods = {'morning': [], 'afternoon': [], 'evening': [], 'night': []}
    for entry in entries:
        moods['morning'].append(entry.morning_mood)
        moods['afternoon'].append(entry.afternoon_mood)
        moods['evening'].append(entry.evening_mood)
        moods['night'].append(entry.night_mood)

    # Подсчитываем количество каждого настроения для разных времен суток
    mood_data = {
        '😊': {'morning': moods['morning'].count('😊'), 'afternoon': moods['afternoon'].count('😊'),
               'evening': moods['evening'].count('😊'), 'night': moods['night'].count('😊')},
        '🙂': {'morning': moods['morning'].count('🙂'), 'afternoon': moods['afternoon'].count('🙂'),
               'evening': moods['evening'].count('🙂'), 'night': moods['night'].count('🙂')},
        '😐': {'morning': moods['morning'].count('😐'), 'afternoon': moods['afternoon'].count('😐'),
               'evening': moods['evening'].count('😐'), 'night': moods['night'].count('😐')},
        '😕': {'morning': moods['morning'].count('😕'), 'afternoon': moods['afternoon'].count('😕'),
               'evening': moods['evening'].count('😕'), 'night': moods['night'].count('😕')},
        '😞': {'morning': moods['morning'].count('😞'), 'afternoon': moods['afternoon'].count('😞'),
               'evening': moods['evening'].count('😞'), 'night': moods['night'].count('😞')}
    }

    return render_template('journal.html', entries=entries, selected_mood=selected_mood, mood_data=mood_data)


@app.route('/edit_entry', methods=['POST'])
@login_required
def edit_entry():
    entry_id = request.form['entry_id']
    morning_mood = request.form['morning_mood']
    afternoon_mood = request.form['afternoon_mood']
    evening_mood = request.form['evening_mood']
    night_mood = request.form['night_mood']
    note = request.form['note']

    # Находим запись по ID
    entry = Entry.query.get(entry_id)

    if entry:
        # Обновляем данные в базе
        entry.morning_mood = morning_mood
        entry.afternoon_mood = afternoon_mood
        entry.evening_mood = evening_mood
        entry.night_mood = night_mood
        entry.note = note

        db.session.commit()  # Сохраняем изменения

    return redirect(url_for('journal'))  # Перенаправляем на страницу дневника

@app.route('/journal/new', methods=['GET', 'POST'])
@login_required
def new_entry():
    if request.method == 'POST':
        morning_mood = request.form['morning_mood']
        afternoon_mood = request.form['afternoon_mood']
        evening_mood = request.form['evening_mood']
        night_mood = request.form['night_mood']
        note = request.form['note']

        new_entry = Entry(
            user_id=current_user.id,
            morning_mood=morning_mood,
            afternoon_mood=afternoon_mood,
            evening_mood=evening_mood,
            night_mood=night_mood,
            note=note
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('journal'))
    return render_template('new_entry.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('journal'))
        else:
            return 'Неверный логин или пароль', 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Стартовая страница (редирект на дневник, если пользователь авторизован)
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('journal'))
    return redirect(url_for('login'))

# Маршрут для отображения календаря с эмоциями
@app.route('/calendar')
@login_required
def calendar():
    entries = Entry.query.filter_by(user_id=current_user.id).all()
    calendar_data = {}
    for entry in entries:
        calendar_data[entry.date] = entry.mood
    return render_template('calendar.html', calendar_data=calendar_data)


@app.route('/day', methods=['GET', 'POST'])
@login_required
def day():
    day_number = request.args.get('day')  # Получаем день из параметров URL
    month_number = request.args.get('month', str(datetime.today().month))  # Получаем месяц из параметров URL, или текущий месяц по умолчанию

    # Преобразуем day_number и month_number в нужный формат
    day_number = day_number.zfill(2)  # Добавляем ведущий ноль, если день состоит из 1 цифры
    month_number = month_number.zfill(2)  # Добавляем ведущий ноль, если месяц состоит из 1 цифры

    # Получаем текущую дату для сравнения (используем текущий год)
    current_year = datetime.today().year  # Текущий год
    date_str = f'{current_year}-{month_number}-{day_number}'  # Форматируем дату (например, 2025-02-22)

    # Преобразуем строку в объект datetime
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    mood = Entry.query.filter_by(user_id=current_user.id, date=date_obj).first()

    if request.method == 'POST':
        # Получаем значения настроений для каждого времени суток
        morning_mood = request.form['morning_mood']
        afternoon_mood = request.form['afternoon_mood']
        evening_mood = request.form['evening_mood']
        night_mood = request.form['night_mood']
        note = request.form['note']  # Получаем заметку

        # Если запись существует, обновляем её, иначе создаем новую запись
        if mood:
            mood.morning_mood = morning_mood
            mood.afternoon_mood = afternoon_mood
            mood.evening_mood = evening_mood
            mood.night_mood = night_mood
            mood.note = note
        else:
            new_entry = Entry(
                user_id=current_user.id,
                date=date_obj,
                morning_mood=morning_mood,
                afternoon_mood=afternoon_mood,
                evening_mood=evening_mood,
                night_mood=night_mood,
                note=note  # Записываем заметку
            )
            db.session.add(new_entry)

        db.session.commit()
        return redirect(url_for('journal'))

    return render_template('day.html', day=day_number, month=month_number, mood=mood)
@app.route('/save_note', methods=['POST'])
@login_required
def save_note():
    note = request.form['note']
    # Тут логика для сохранения заметки в базе данных
    # Например, создаем или обновляем запись в базе для текущего дня
    today = datetime.today().date()
    entry = Entry.query.filter_by(user_id=current_user.id, date=today).first()

    if entry:
        entry.note = note
    else:
        new_entry = Entry(user_id=current_user.id, date=today, note=note)
        db.session.add(new_entry)

    db.session.commit()
    return redirect(url_for('journal'))

# Запуск приложения
if __name__ == '__main__':
    # Создание базы данных, если она не существует
    with app.app_context():
        db.create_all()
    app.run(debug=True)
