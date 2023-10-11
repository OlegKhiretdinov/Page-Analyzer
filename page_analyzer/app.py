import os
import psycopg2
from datetime import datetime
from validators.url import url as url_validator
from urllib.parse import urlparse
from flask import Flask, render_template, redirect, request, url_for, flash, get_flashed_messages
from dotenv import dotenv_values

app = Flask(__name__)

# todo wtf и как по уму
app.secret_key = "secret_key"

DATABASE_URL = os.getenv("DATABASE_URL")


@app.route('/')
def home_page():
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'pages/home.html',
        messages=messages
    )


@app.get('/urls')
def urls_list():
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cursor:
        cursor.execute('SELECT id, name FROM URLS ORDER BY created_at ASC')
        urls = cursor.fetchall()

    messages = get_flashed_messages(with_categories=True)

    return render_template(
        'pages/urls.html',
        messages=messages,
        urls_list=urls
    )


@app.post('/urls')
def add_urls():
    # config = dotenv_values(".env")
    url = request.form.get('url')
    # todo типизация
    if url == "":
        flash('URL обязателен', 'danger')
        return redirect(url_for('home_page'), 302)
    elif len(url) > 255:
        flash('URL превышает 255 символов', 'danger')
        return redirect(url_for('home_page'), 301)
    elif url_validator(url) == True:
        u_s = urlparse(url)
        url_string = f'{u_s.scheme}://{u_s.hostname}'
    else:
        flash('Некорректный URL', 'danger')
        return redirect(url_for('home_page'), 301)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO urls (name, created_at) values(%(url)s, %(date_time)s)
                ON CONFLICT (name) DO UPDATE
                SET created_at=%(date_time)s;
                """,
                           {'url': url_string, 'date_time': datetime.today()})
        conn.commit()
        conn.close()
    except OSError:
        print("bolt")

    return redirect(url_for('urls_list'), 302)


@app.route('/urls/<int:url_id>')
def url_profile(url_id):
    messages = get_flashed_messages(with_categories=True)
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cursor:
        cursor.execute(f'SELECT * FROM urls WHERE id={url_id}')
        url_data = cursor.fetchone()
    conn.close()

    return render_template(
        'pages/url_info.html',
        messages=messages,
        url_data=url_data
    )