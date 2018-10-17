from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register')
def register():
    return ''

@app.route('/login')
def login():
    return ''


app.run(debug=True)
