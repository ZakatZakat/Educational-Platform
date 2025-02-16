from flask import Flask, render_template, url_for


app = Flask(__name__)

# Пример данных — можно вынести в JSON-файл или базу данных
def get_textbooks():
    # Если данные хранятся в файле, можно использовать:
    # with open('textbooks.json', 'r', encoding='utf-8') as f:
    #     textbooks = json.load(f)
    # return textbooks

    # Пример статического списка учебников
    return [
        {
            "subject": "Математика 6 класс",
            "image": url_for('static', filename='app/education/math.png'),
            "rating": [1, 1, 1, 1, 0],  # 1 - полная звезда, 0.5 - половина, 0 - пустая
            "progress": "Готово 3 из 5 упражнений",
            "route": url_for('math_page')
        },
        {
            "subject": "Грамматика Английского Языка",
            "image": url_for('static', filename='app/education/gramm.png'),
            "rating": [1, 1, 1, 0.5, 0],
            "progress": "Готово 5 из 5 упражнений",
            "route": "#"
        },
        {
            "subject": "Физика 6 класс",
            "image": url_for('static', filename='app/education/o.png'),
            "rating": [1, 1, 1, 0, 0],
            "progress": "Готово 2 из 5 упражнений",
            "route": "#"
        },
        {
            "subject": "Русский язык 6 класс",
            "image": url_for('static', filename='app/education/russian.png'),
            "rating": [1, 1, 1, 1, 0],
            "progress": "Готово 3 из 5 упражнений",
            "route": "#"
        },
        {
            "subject": "Информатика 6 класс",
            "image": url_for('static', filename='app/education/it.png'),
            "rating": [1, 1, 1, 0, 0],
            "progress": "Готово 4 из 5 упражнений",
            "route": "#"
        },
        {
            "subject": "Литература 6 класс",
            "image": url_for('static', filename='app/education/literature.png'),
            "rating": [1, 1, 1, 0.5, 0],
            "progress": "Готово 2 из 5 упражнений",
            "route": "#"
        }
    ]



@app.route('/')
def index():
    textbooks = get_textbooks()
    return render_template('main-page.html', textbooks=textbooks)

@app.route('/create_course')
def create_course():
    return render_template('create-a-course.html')

@app.route('/course_list')
def course_list():
    return render_template('course-list.html')

@app.route('/math_page')
def math_page():
    return render_template('math-page.html')

@app.route('/add_course_page')
def add_course_page():
    return render_template('add-course-page.html')

@app.route('/my_courses')
def my_courses():
    return render_template('my-courses.html')

if __name__ == '__main__':
    app.run(debug=True)

    