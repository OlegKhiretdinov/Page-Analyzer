import os
import psycopg2
import psycopg2.extras
import psycopg2.errors
from psycopg2.errorcodes import UNIQUE_VIOLATION
from datetime import datetime
from validators.url import url as url_validator
from urllib.parse import urlparse
from flask import Flask, render_template, redirect, \
    request, url_for, flash, get_flashed_messages, make_response
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

app = Flask(__name__)

app.secret_key = "secret_key"

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


@app.route('/')
def home_page():
    return render_template('pages/home.html',)


@app.get('/urls')
def urls_list():
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute('''
            SELECT DISTINCT ON (urls.id)
            urls.id,
            urls.name,
            url_checks.created_at,
            url_checks.status_code
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
    url = request.form.get('url')

    if url == "":
        flash('URL обязателен', 'danger')
        return make_response(render_template('pages/home.html', url_name=url), 422)
    elif len(url) > 255:
        flash('URL превышает 255 символов', 'danger')
        return make_response(render_template('pages/home.html', url_name=url), 422)
    elif url_validator(url) is True:
        u_s = urlparse(url)
        url_string = f'{u_s.scheme}://{u_s.hostname}'
        if u_s.port:
            url_string += f':{u_s.port}'
    else:
        flash('Некорректный URL', 'danger')
        return make_response(render_template('pages/home.html', url_name=url), 422)

    correct_url_flash_text = 'Страница успешно добавлена'
    correct_url_flash_status = 'success'

    conn = psycopg2.connect(DATABASE_URL)

    with conn.cursor() as cursor:
        cursor.execute(f"SELECT id FROM urls WHERE name='{url_string}'")
        req_data = cursor.fetchone()

        if req_data is not None:
            url_id = req_data[0]
            correct_url_flash_text = 'Страница уже существует'
            correct_url_flash_status = 'info'
        else:
            cursor.execute("""
                            INSERT INTO urls (name, created_at)
                            values(%(url)s, %(date_time)s)
                            RETURNING id
                        """,
                           {
                               'url': url_string,
                               'date_time': datetime.today()
                           })
            url_id = cursor.fetchone()[0]
            conn.commit()

    conn.close()

    flash(correct_url_flash_text, correct_url_flash_status)
    return redirect(url_for('url_profile', url_id=url_id), 302)


# страница профиля
@app.route('/urls/<int:url_id>')
def url_profile(url_id):
    messages = get_flashed_messages(with_categories=True)
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute(f'SELECT * FROM urls WHERE id={url_id}')
        url_data = cursor.fetchone()
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute(f'SELECT * FROM url_checks WHERE url_id={url_id}')
        url_checks = cursor.fetchall()
    conn.close()

    if not url_data:
        return handle_bad_request("404 id not found")

    return render_template(
        'pages/url_info.html',
        messages=messages,
        url_data=url_data,
        url_checks=url_checks
    )


@app.post('/urls/<int:url_id>/checks')
def url_checker(url_id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cursor:
        cursor.execute("SELECT name FROM urls WHERE id = %s", (int(url_id),))
        url = cursor.fetchone()[0]

    try:
        r = requests.get(url)
        code = r.status_code

        if code >= 500:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('url_profile', url_id=url_id), 302)

        page_content = BeautifulSoup(r.text, features="html.parser")

        title = ''
        h1 = ''
        description = ''

        title_element = page_content.title
        if title_element:
            title = title_element.text

        h1_element = page_content.h1
        if h1_element:
            h1 = h1_element.text

        page_meta = page_content.findAll('meta')
        for el in page_meta:
            if el.get('name') == 'description':
                description = el.get('content')
    except OSError:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_profile', url_id=url_id), 302)

    with conn.cursor() as cursor:
        cursor.execute("""INSERT INTO url_checks (
                            url_id,
                            created_at,
                            status_code,
                            h1,
                            title,
                            description
                        ) values (
                            %(url_id)s,
                            %(date_time)s,
                            %(status_code)s,
                            %(h1)s,
                            %(title)s,
                            %(description)s
                        )""",
                       {
                           'url_id': int(url_id),
                           'date_time': datetime.today(),
                           'status_code': int(code),
                           'h1': h1,
                           'title': title,
                           'description': description
                       }
                       )
    conn.commit()
    conn.close()
    flash('Страница успешно проверена', 'success')

    return redirect(url_for('url_profile', url_id=url_id), 302)


def handle_bad_request(e):
    return render_template('pages/404.html'), 404


app.register_error_handler(404, handle_bad_request)
