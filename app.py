from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('main-page.html')

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

    