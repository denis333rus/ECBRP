from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory
import sqlite3
import json
from datetime import datetime
import os
import hashlib
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Railway оптимизация - получение настроек из переменных окружения
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['ENV'] = os.environ.get('FLASK_ENV', 'development')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Настройки для загрузки файлов
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max file size

# Создаем папку для загрузок
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Простая аутентификация (в реальном проекте используйте более безопасные методы)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # В реальном проекте используйте хеширование

# Функции для работы с файлами
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def get_file_icon(extension):
    icons = {
        'pdf': '📄',
        'txt': '📝',
        'doc': '📄',
        'docx': '📄',
        'png': '🖼️',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'gif': '🖼️'
    }
    return icons.get(extension, '📎')

# Инициализация базы данных
def init_database():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT DEFAULT 'Общие',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_published BOOLEAN DEFAULT FALSE,
            attachment_filename TEXT,
            attachment_original_name TEXT
        )
    ''')
    
    # Проверяем и добавляем новые колонки если их нет
    cursor.execute("PRAGMA table_info(news)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'attachment_filename' not in columns:
        cursor.execute('ALTER TABLE news ADD COLUMN attachment_filename TEXT')
        print("Добавлена колонка attachment_filename")
    
    if 'attachment_original_name' not in columns:
        cursor.execute('ALTER TABLE news ADD COLUMN attachment_original_name TEXT')
        print("Добавлена колонка attachment_original_name")
    
    conn.commit()
    conn.close()
    print("База данных инициализирована успешно!")

# Получение всех новостей для админ панели
def get_all_news():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news ORDER BY created_at DESC')
    news = cursor.fetchall()
    conn.close()
    return news

# Получение новости по ID
def get_news_by_id(news_id):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news WHERE id = ?', (news_id,))
    news = cursor.fetchone()
    conn.close()
    return news

# Добавление новости
def add_news(title, content, author, category, attachment_filename=None, attachment_original_name=None):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO news (title, content, author, category, is_published, attachment_filename, attachment_original_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, content, author, category, True, attachment_filename, attachment_original_name))
    conn.commit()
    news_id = cursor.lastrowid
    conn.close()
    return news_id

# Обновление новости
def update_news(news_id, title, content, author, category, is_published, attachment_filename=None, attachment_original_name=None):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE news 
        SET title = ?, content = ?, author = ?, category = ?, is_published = ?, 
            attachment_filename = ?, attachment_original_name = ?
        WHERE id = ?
    ''', (title, content, author, category, is_published, attachment_filename, attachment_original_name, news_id))
    conn.commit()
    conn.close()

# Удаление новости
def delete_news(news_id):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM news WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()

# Проверка авторизации
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Страница достопримечательностей
@app.route('/attractions')
def attractions():
    return render_template('attractions.html')

# Страница истории города
@app.route('/history')
def history():
    return render_template('history.html')

# Страница новостей
@app.route('/news')
def news():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news WHERE is_published = TRUE ORDER BY created_at DESC LIMIT 20')
    news_data = cursor.fetchall()
    conn.close()
    
    # Преобразуем данные в удобный формат
    news_list = []
    for item in news_data:
        news_item = {
            'id': item[0],
            'title': item[1],
            'content': item[2],
            'author': item[3],
            'category': item[4],
            'created_at': item[5]
        }
        # Добавляем информацию о файлах если есть
        if len(item) > 7:
            news_item['attachment_filename'] = item[7]
            news_item['attachment_original_name'] = item[8]
        news_list.append(news_item)
    
    return render_template('news.html', news=news_list)

# Страница контактов
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Страница официальных ссылок
@app.route('/officials')
def officials():
    return render_template('officials.html')

# Админ панель - авторизация
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Успешный вход в админ панель!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверные учетные данные!', 'error')
    
    return render_template('admin/login.html')

# Выход из админ панели
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Вы вышли из админ панели', 'info')
    return redirect(url_for('admin_login'))

# Главная страница админ панели
@app.route('/admin')
@login_required
def admin_dashboard():
    news = get_all_news()
    return render_template('admin/dashboard.html', news=news)

# Добавление новости
@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_add_news():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        category = request.form['category']
        
        if title and content and author:
            attachment_filename = None
            attachment_original_name = None
            
            # Обработка загруженного файла
            if 'attachment' in request.files:
                file = request.files['attachment']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Добавляем timestamp для уникальности
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    attachment_filename = filename
                    attachment_original_name = file.filename
                    flash(f'Файл "{file.filename}" успешно загружен!', 'success')
                elif file and file.filename:
                    flash('Неподдерживаемый тип файла!', 'error')
            
            news_id = add_news(title, content, author, category, attachment_filename, attachment_original_name)
            flash(f'Новость #{news_id} успешно добавлена!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Все поля обязательны для заполнения!', 'error')
    
    return render_template('admin/add_news.html')

# Редактирование новости
@app.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_news(news_id):
    news = get_news_by_id(news_id)
    if not news:
        flash('Новость не найдена!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        category = request.form['category']
        is_published = 'is_published' in request.form
        
        if title and content and author:
            attachment_filename = news[7] if len(news) > 7 else None  # Сохраняем существующий файл
            attachment_original_name = news[8] if len(news) > 8 else None
            
            # Обработка нового загруженного файла
            if 'attachment' in request.files:
                file = request.files['attachment']
                if file and file.filename and allowed_file(file.filename):
                    # Удаляем старый файл если есть
                    if attachment_filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename)):
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename))
                    
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    attachment_filename = filename
                    attachment_original_name = file.filename
                    flash(f'Файл "{file.filename}" успешно загружен!', 'success')
                elif file and file.filename:
                    flash('Неподдерживаемый тип файла!', 'error')
            
            update_news(news_id, title, content, author, category, is_published, attachment_filename, attachment_original_name)
            flash(f'Новость #{news_id} успешно обновлена!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Все поля обязательны для заполнения!', 'error')
    
    return render_template('admin/edit_news.html', news=news)

# Удаление новости
@app.route('/admin/news/delete/<int:news_id>')
@login_required
def admin_delete_news(news_id):
    news = get_news_by_id(news_id)
    if news:
        # Удаляем прикрепленный файл если есть
        if len(news) > 7 and news[7]:  # attachment_filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], news[7])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        delete_news(news_id)
        flash(f'Новость #{news_id} удалена!', 'success')
    else:
        flash('Новость не найдена!', 'error')
    
    return redirect(url_for('admin_dashboard'))

# Скачивание файлов
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# API для получения статистики
@app.route('/api/stats')
def api_stats():
    news = get_all_news()
    total = len(news)
    published = len([n for n in news if n[6]])  # is_published поле
    
    categories = {}
    for n in news:
        cat = n[4]  # category поле
        categories[cat] = categories.get(cat, 0) + 1
    
    return jsonify({
        'total_news': total,
        'published_news': published,
        'pending_news': total - published,
        'categories': categories
    })

# Инициализация базы данных при запуске
if __name__ == '__main__':
    init_database()
    # Railway оптимизация - получение порта из переменной окружения
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)