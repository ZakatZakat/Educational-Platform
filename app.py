from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('student-overview.html')

@app.route('/create_course')
def create_course():
    return render_template('create-a-course.html')

if __name__ == '__main__':
    app.run(debug=True)