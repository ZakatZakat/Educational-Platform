import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import json
import pymupdf

app = Flask(__name__)

app.secret_key = 'your_secret_key'

# Папка для загрузки файлов (вы можете использовать отдельную папку для PDF и превью)
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Папка для сохранения превью, указываем её как static/app/education/
PREVIEW_FOLDER = os.path.join(app.root_path, 'static', 'app', 'education')
if not os.path.exists(PREVIEW_FOLDER):
    os.makedirs(PREVIEW_FOLDER)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
TEXTBOOKS_JSON_PATH = os.path.join(app.root_path, 'textbooks.json')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_textbook_entry(new_entry):
    try:
        with open(TEXTBOOKS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = []
    data.append(new_entry)
    with open(TEXTBOOKS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_pdf_preview(filepath, preview_path):
    try:
        doc = pymupdf.open(filepath)
        page = doc.load_page(0)  # первая страница
        pix = page.get_pixmap()
        pix.save(preview_path)
        return True
    except Exception as e:
        print("Ошибка при генерации превью с помощью PyMuPDF:", e)
        return False
    
# Пример данных — можно вынести в JSON-файл или базу данных
def get_textbooks():
    # Если данные хранятся в файле, можно использовать:
    with open('textbooks.json', 'r', encoding='utf-8') as f:
         textbooks = json.load(f)
    return textbooks

@app.route('/')
def index():
    textbooks = get_textbooks()
    return render_template('main-page.html', textbooks=textbooks)

@app.route('/course_list')
def course_list():
    return render_template('course-list.html')

@app.route('/course/<subject_slug>')
def course_page(subject_slug):
    textbooks = get_textbooks()
    pdf_file = None
    # Ищем учебник, у которого route заканчивается на subject_slug
    # или slug можно сравнить с преобразованным названием.
    for book in textbooks:
        # Предположим, что route выглядит как "/course/some-slug"
        route = book.get("route", "")
        # Удалим префикс '/course/' и сравним с subject_slug
        if route.startswith("/course/"):
            book_slug = route[len("/course/"):]
            print(f'Book Slug: {book_slug}')
            print(f'Subject Slug: {subject_slug}')
            if book_slug == subject_slug:
                pdf_file = book.get("pdf", None)
                break
    # Если pdf_file не найден, можно задать значение по умолчанию (например, пустую строку)
    if pdf_file is None:
        pdf_file = ""
    print()
    print(f'PDF File: {pdf_file}')
    return render_template('math-page.html', pdf_file=pdf_file, subject_slug=subject_slug)

@app.route('/math_page')
def math_page():
    return render_template('math-page.html')

def generate_pdf_preview(filepath, preview_path):
    try:
        doc = pymupdf.open(filepath)
        page = doc.load_page(0)  # первая страница (индекс 0)
        pix = page.get_pixmap()
        pix.save(preview_path)
        return True
    except Exception as e:
        print("Ошибка при генерации превью с помощью PyMuPDF:", e)
        return False

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_course_page', methods=['GET', 'POST'])
def add_course_page():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не найден')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Файл не выбран')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            flash('Файл успешно загружен')
            
            ext = filename.rsplit('.', 1)[1].lower()
            pdf_path = ""
            if ext == 'pdf':
                try:
                    preview_filename = "preview_" + os.path.splitext(filename)[0] + ".png"
                    preview_path = os.path.join(PREVIEW_FOLDER, preview_filename)
                    success = generate_pdf_preview(filepath, preview_path)
                    if success:
                        image_for_json = "static/app/education/" + preview_filename
                    else:
                        flash("Не удалось создать превью PDF.")
                        image_for_json = "uploads/" + filename
                    # Формируем URL для PDF через маршрут uploaded_file
                    pdf_path = url_for('uploaded_file', filename=filename)
                    if not pdf_path.startswith('/'):
                        pdf_path = '/' + pdf_path
                except Exception as e:
                    flash("Ошибка при конвертации PDF: " + str(e))
                    image_for_json = "uploads/" + filename
                    pdf_path = url_for('uploaded_file', filename=filename)
                    if not pdf_path.startswith('/'):
                        pdf_path = '/' + pdf_path
            else:
                image_for_json = "uploads/" + filename
                        
            subject_name = os.path.splitext(filename)[0][:10]
            subject_slug = subject_name.replace(" ", "-").lower()
            
            new_entry = {
                "subject": subject_name,
                "image": image_for_json,
                "pdf": pdf_path,
                "rating": [0, 0, 0, 0, 0],
                "progress": "Новый учебник",
                "route": "/course/" + subject_slug
            }
            add_textbook_entry(new_entry)
            return redirect(url_for('add_course_page'))
        else:
            flash('Неподдерживаемый формат файла')
            return redirect(request.url)
    return render_template('add-course-page.html')

@app.route('/my_courses')
def my_courses():
    return render_template('my-courses.html')

if __name__ == '__main__':
    app.run(debug=True)

    