import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from validators.url import url as url_validator
from urllib.parse import urlparse
from flask import Flask, render_template, redirect, request, url_for, flash, get_flashed_messages
from dotenv import dotenv_values
import requests

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
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute('''SELECT DISTINCT ON (urls.id) urls.id, urls.name, url_checks.created_at, url_checks.status_code
        FROM urls
        LEFT JOIN url_checks ON urls.id = url_checks.url_id
        ORDER BY urls.id, url_checks.created_at DESC;
        ''')
        urls = cursor.fetchall()

    conn.close()
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
        return redirect(url_for('home_page'), 302)
    elif url_validator(url) == True:
        u_s = urlparse(url)
        url_string = f'{u_s.scheme}://{u_s.hostname}'
    else:
        flash('Некорректный URL', 'danger')
        return redirect(url_for('home_page'), 302)

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO urls (name, created_at) values(%(url)s, %(date_time)s)
                    ON CONFLICT (name) DO UPDATE
                    SET created_at=%(date_time)s;
                    """,
                               {'url': url_string, 'date_time': datetime.today()})
        conn.close()
    except OSError:
        print("bolt")

    return redirect(url_for('urls_list'), 302)


# страница профиля
@app.route('/urls/<int:url_id>')
def url_profile(url_id):
    messages = get_flashed_messages(with_categories=True)
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(f'SELECT * FROM urls WHERE id={url_id}')
        url_data = cursor.fetchone()
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(f'SELECT * FROM url_checks WHERE url_id={url_id}')
        url_checks = cursor.fetchall()
    conn.close()
    return render_template(
        'pages/url_info.html',
        messages=messages,
        url_data=url_data,
        url_checks=url_checks
    )


@app.post('/urls/<int:url_id>/checks')
def url_checker(url_id):
    # request.form.
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cursor:
        cursor.execute("SELECT name FROM urls WHERE id = %s", (int(url_id),))
        url = cursor.fetchone()[0]
    code = 0
    try:
        r = requests.get(url)
        code = r.status_code
    except:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_profile', url_id=url_id), 302)

    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO url_checks (url_id, created_at, status_code) values(%(url_id)s, %(date_time)s, %(status_code)s)
        """,
                       {'url_id': int(url_id), 'date_time': datetime.today(), 'status_code': int(code)}
                       )
    conn.commit()
    conn.close()

    return redirect(url_for('url_profile', url_id=url_id), 302)
