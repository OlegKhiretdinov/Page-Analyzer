import os
import requests
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from page_analyzer.celery_config import celery_app
from page_analyzer.utils import parse_html
from page_analyzer.models import UrlChecksModel


DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(f'postgresql://{DATABASE_URL}', echo=True)


@celery_app.task
def url_check_task(url, id):
    try:
        r = requests.get(url)
        code = r.status_code
        title, h1, description = parse_html(r.text)
        print(code, title, h1)
    except requests.RequestException as e:
        print(e)

    with Session(engine) as session:
        url_check = UrlChecksModel(url_id=id,
                                   status_code=code,
                                   h1=h1,
                                   title=title,
                                   description=description,
                                   created_at=datetime.today(),
                                   )
        session.add(url_check)
        session.commit()
