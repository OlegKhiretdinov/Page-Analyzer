import psycopg2
import psycopg2.extras
from datetime import datetime


def urls_list_query(connections):
    conn = connections.getconn()
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
    connections.putconn(conn)
    return urls


def add_url_query(url_string, connections):
    conn = connections.getconn()
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute("""
                            INSERT INTO urls (name, created_at)
                            values(%(url)s, %(date_time)s)
                            RETURNING id
                        """,
                       {
                           'url': url_string,
                           'date_time': datetime.today()
                       })
        url_id = cursor.fetchone()
        conn.commit()
    connections.putconn(conn)

    return url_id


def get_url_data_query(fields, condition, connections):
    conn = connections.getconn()
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute(f"SELECT {', '.join(fields)} FROM urls WHERE {condition}")
        url_data = cursor.fetchone()

    connections.putconn(conn)
    return url_data


def get_url_checks_query(url_id, connections):
    conn = connections.getconn()
    with conn.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
    ) as cursor:
        cursor.execute(f'SELECT * FROM url_checks WHERE url_id={url_id}')
        url_checks = cursor.fetchall()

    connections.putconn(conn)
    return url_checks


def insert_check_result_query(url_id, code, h1, title, description, connections):
    conn = connections.getconn()
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
    connections.putconn(conn)
