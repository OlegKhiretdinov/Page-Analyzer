import os
from datetime import datetime
from flask import Flask, render_template, redirect, \
    request, url_for, flash, get_flashed_messages, make_response
from sqlalchemy import create_engine, select, exc
from sqlalchemy.orm import Session
import requests
from dotenv import load_dotenv
from page_analyzer.utils import url_validate, prepare_url, parse_html
from page_analyzer.models import UrlsModel, UrlChecksModel

app = Flask(__name__)
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
app.secret_key = SECRET_KEY

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(f'postgresql://{DATABASE_URL}', echo=True)


@app.route('/')
def home_page():
    return render_template('pages/home.html',)


# список урлов
@app.get('/urls')
def urls_list():
    limit = int(request.values.get("limit", 10))
    page = int(request.values.get("page", 1))
    with Session(engine) as session:
        query = select(UrlsModel.id, UrlsModel.name, UrlChecksModel.status_code, UrlChecksModel.created_at)\
            .distinct(UrlsModel.id)\
            .join(UrlChecksModel, isouter=True)\
            .order_by(UrlsModel.id, UrlChecksModel.created_at.desc())\
            .limit(limit).offset(limit * (page - 1))
        urls = session.execute(query).all()

    messages = get_flashed_messages(with_categories=True)

    return render_template(
        'pages/urls.html',
        messages=messages,
        urls_list=urls
    )


# добавление url
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
        with Session(engine) as session:
            new_url = UrlsModel(name=url_string, created_at=datetime.today())
            session.add(new_url)
            session.commit()

            redirect_url_id = new_url.id
            flash('Страница успешно добавлена', 'success')
    except exc.IntegrityError as ex:
        if "UniqueViolation" in ex.__repr__():
            with Session(engine) as session:
                query = select(UrlsModel.id).where(UrlsModel.name == url_string)
                redirect_url_id = session.scalar(query)
            flash('Страница уже существует', 'info')
        else:
            raise

    return redirect(url_for('url_profile', url_id=redirect_url_id), 302)


# профиль url и список проверок
@app.route('/urls/<int:url_id>')
def url_profile(url_id):
    messages = get_flashed_messages(with_categories=True)

    with Session(engine) as session:
        query_data = select(UrlsModel).where(UrlsModel.id == url_id)
        url_data = session.execute(query_data).fetchone()

        if not url_data:
            return handle_bad_request("404 id not found")

        query_checks = select(UrlChecksModel).where(UrlChecksModel.url_id == url_id)
        url_checks = map(lambda item: item.UrlChecksModel, session.execute(query_checks).fetchall())

    return render_template(
        'pages/url_info.html',
        messages=messages,
        url_data=url_data.UrlsModel,
        url_checks=url_checks
    )


# проверка url
@app.post('/urls/<int:url_id>/checks')
def url_checker(url_id):
    with Session(engine) as session:
        query = select(UrlsModel.name).where(UrlsModel.id == url_id)
        url_name = session.scalar(query)

    try:
        r = requests.get(url_name)
        code = r.status_code

        if code >= 500:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('url_profile', url_id=url_id), 302)

        title, h1, description = parse_html(r.text)

    except OSError:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_profile', url_id=url_id), 302)

    with Session(engine) as session:
        url_check = UrlChecksModel(url_id=url_id,
                                   status_code=code,
                                   h1=h1,
                                   title=title,
                                   description=description,
                                   created_at=datetime.today(),
                                   )
        session.add(url_check)
        session.commit()

    flash('Страница успешно проверена', 'success')
    return redirect(url_for('url_profile', url_id=url_id), 302)


def handle_bad_request(e):
    return render_template('pages/404.html'), 404


app.register_error_handler(404, handle_bad_request)
