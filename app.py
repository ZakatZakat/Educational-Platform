import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import json
import pymupdf
import re

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

def natural_key(string_):
    """Возвращает список чисел и строк для естественной сортировки."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', string_)]

import re
@app.route('/course/<subject_slug>')
def course_page(subject_slug):
    textbooks = get_textbooks()
    selected_book = None
    for book in textbooks:
        route = book.get("route", "")
        if route.startswith("/course/"):
            book_slug = route[len("/course/"):]
            if book_slug == subject_slug:
                selected_book = book
                break
    if not selected_book:
        flash("Учебник не найден")
        return redirect(url_for("index"))

    # Получаем папку с PNG файлами
    book_png_folder = selected_book.get("book_png", "")
    images = []
    folder_name = ""
    if book_png_folder:
        folder_name = os.path.basename(os.path.normpath(book_png_folder))
        abs_folder_path = os.path.join(app.root_path, book_png_folder.lstrip("/"))
        try:
            images = [f for f in os.listdir(abs_folder_path) if f.lower().endswith('.png')]
            # Сортировка изображений естественным способом
            images = sorted(images, key=natural_key)
            assert False, images
        except Exception as e:
            flash("Ошибка при чтении папки с изображениями: " + str(e))
    else:
        flash("Учебник не содержит извлечённых изображений.")

    # Передаем отсортированный список изображений в шаблон
    return render_template('math-page.html',
                           images=images,
                           folder_name=folder_name,
                           subject_slug=subject_slug,
                           selected_book=selected_book,
                           image_preview=selected_book.get("image", ""),
                           type=selected_book.get("type", ""))

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

def extract_all_pages_from_pdf(filepath, output_folder):
    """
    Извлекает все страницы PDF в формате PNG и сохраняет их в output_folder.
    Возвращает список относительных путей к сохранённым изображениям.
    """
    try:
        doc = pymupdf.open(filepath)
        image_paths = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            output_filename = f"page_{page_num+1}.png"
            output_path = os.path.join(output_folder, output_filename)
            pix.save(output_path)
            # Формируем относительный путь относительно папки static
            rel_path = os.path.relpath(output_path, os.path.join(app.root_path, "static"))
            rel_path = "/" + rel_path.replace(os.path.sep, "/")
            image_paths.append(rel_path)
        doc.close()
        return image_paths
    except Exception as e:
        print("Ошибка при извлечении изображений из PDF:", e)
        return None

@app.route('/add_course_page', methods=['GET', 'POST'])
def add_course_page():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не найден')
            return redirect(request.url)
        file = request.files['file']
        type_version = request.form.get('type')
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
            book_png = ""
            if ext == 'pdf':
                try:
                    # Создаем папку для извлечённых PNG-страниц
                    folder_name = os.path.splitext(filename)[0]
                    output_folder = os.path.join(PREVIEW_FOLDER, folder_name)
                    os.makedirs(output_folder, exist_ok=True)
                    image_paths = extract_all_pages_from_pdf(filepath, output_folder)
                    if image_paths and len(image_paths) > 0:
                        # Используем первую страницу как превью
                        image_for_json = "/static/app/education/" + folder_name + "/" + os.path.basename(image_paths[0])
                        # Сохраняем путь к папке с PNG
                        book_png = "/static" + os.path.dirname(image_paths[0]) + "/"
                    else:
                        flash("Не удалось извлечь изображения из PDF.")
                        image_for_json = url_for('uploaded_file', filename=filename)
                        book_png = ""
                    # Формируем URL для оригинального PDF через маршрут uploaded_file
                    pdf_path = url_for('uploaded_file', filename=filename)
                    if not pdf_path.startswith('/'):
                        pdf_path = '/' + pdf_path
                except Exception as e:
                    flash("Ошибка при извлечении изображений из PDF: " + str(e))
                    image_for_json = url_for('uploaded_file', filename=filename)
                    pdf_path = url_for('uploaded_file', filename=filename)
                    if not pdf_path.startswith('/'):
                        pdf_path = '/' + pdf_path
                    book_png = ""
            else:
                # Если загружено изображение, конвертируем в PNG, если нужно
                if ext != 'png':
                    try:
                        from PIL import Image
                        img = Image.open(filepath)
                        converted_filename = "converted_" + os.path.splitext(filename)[0] + ".png"
                        converted_path = os.path.join(PREVIEW_FOLDER, converted_filename)
                        img.save(converted_path, "PNG")
                        image_for_json = "/static/app/education/" + converted_filename
                    except Exception as e:
                        flash("Ошибка при конвертации изображения: " + str(e))
                        image_for_json = url_for('uploaded_file', filename=filename)
                else:
                    image_for_json = url_for('uploaded_file', filename=filename)
                pdf_path = ""  # Для изображений поле pdf оставляем пустым
                book_png = ""  # И также поле book_png
        
            subject_name = os.path.splitext(filename)[0][:10]
            subject_slug = subject_name.replace(" ", "-").lower()
            
            new_entry = {
                "subject": subject_name,
                "image": image_for_json,
                "pdf": pdf_path,         # URL оригинального PDF
                "book_png": book_png,    # URL к папке с PNG-изображениями
                "rating": [0, 0, 0, 0, 0],
                "progress": "Новый учебник",
                "route": "/course/" + subject_slug,
                "type": type_version
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

    