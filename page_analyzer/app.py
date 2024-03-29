import os
import psycopg2
from psycopg2 import pool
from psycopg2.errorcodes import UNIQUE_VIOLATION
from flask import Flask, render_template, redirect, \
    request, url_for, flash, get_flashed_messages, make_response
import requests
from dotenv import load_dotenv
from page_analyzer.utils import url_validate, prepare_url, parse_html
from page_analyzer.bd_query import urls_list_query, add_url_query, \
    get_url_data_query, get_url_checks_query, insert_check_result_query


app = Flask(__name__)
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
app.secret_key = SECRET_KEY

DATABASE_URL = os.getenv('DATABASE_URL')
connections = pool.SimpleConnectionPool(1, 100, DATABASE_URL)


@app.route('/')
def home_page():
    return render_template('pages/home.html',)


@app.get('/urls')
def urls_list():
    urls = urls_list_query(connections)
    messages = get_flashed_messages(with_categories=True)

    return render_template(
        'pages/urls.html',
        messages=messages,
        urls_list=urls
    )


@app.post('/urls')
def add_urls():
    url = request.form.get('url')
    is_valid, error_txt = url_validate(url)

    if not is_valid:
        flash(error_txt, 'danger')
        return make_response(render_template('pages/home.html', url_name=url), 422)
    else:
        url_string = prepare_url(url)

    try:
        url_data = add_url_query(url_string, connections)
        flash('Страница успешно добавлена', 'success')
    except psycopg2.errors.lookup(UNIQUE_VIOLATION):
        url_data = get_url_data_query(['id'], f"name='{url_string}'", connections)
        flash('Страница уже существует', 'info')

    return redirect(url_for('url_profile', url_id=url_data.id), 302)


# страница профиля
@app.route('/urls/<int:url_id>')
def url_profile(url_id):
    messages = get_flashed_messages(with_categories=True)
    url_data = get_url_data_query(['*'], f"id={url_id}", connections)
    url_checks = get_url_checks_query(url_id, connections)

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
    url_data = get_url_data_query(['name'], f"id={url_id}", connections)

    try:
        r = requests.get(url_data.name)
        code = r.status_code

        if code >= 500:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('url_profile', url_id=url_id), 302)

        title, h1, description = parse_html(r.text)

    except OSError:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_profile', url_id=url_id), 302)

    insert_check_result_query(url_id, code, h1, title, description, connections)
    flash('Страница успешно проверена', 'success')

    return redirect(url_for('url_profile', url_id=url_id), 302)


def handle_bad_request(e):
    return render_template('pages/404.html'), 404


app.register_error_handler(404, handle_bad_request)
