from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def home_page():
    return render_template('pages/home.html')
    # return "render_template('main_layout.html')"
