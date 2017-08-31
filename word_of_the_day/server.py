import datetime
import os
import sqlite3
import schedule
import time
from flask import Flask, jsonify, g
from threading import Thread


app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'wod.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
))

app.config.from_envvar('WOD_SETTINGS', silent=True)

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def init_db_command():
    init_db()
    print('Initialized the database.')

@app.cli.command('loaddb')
def load_db_command():
    db = get_db()
    f = open('words_stripped.txt', 'r')
    lines = f.readlines()
    for line in lines:
        db.execute("insert into words ('text') values ('" \
        + line.rstrip("\n") + "')")
    db.commit()
    print('Loaded values into datbase.')

def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False 

def word_for_date(date):
    if not validate_date(date):
        return {
            'error': 'Invalid date format. Must be YYYY-MM-DD.'
        }

    db = get_db()
    cur = db.execute(
        "select * from words where date is '" + date + \
        "' order by random() limit 1")
    word = cur.fetchone()

    if not word:
        return {
            'error': 'No word found.'
        }

    return {
        'text': word['text'],
        'date': word['date'],
    }

def word_for_today():
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    return word_for_date(now)

@app.route('/', methods=['GET'])
def word_of_the_day():
    return jsonify(word_for_today())

@app.route('/<date>', methods=['GET'])
def word_from_date(date):
    return jsonify(word_for_date(date))

@app.route('/update', methods=['GET'])
def set_word_of_the_day():
    response = word_for_today()

    if not response.get('error'):
        return jsonify({
            'success': 'Word already up to date!'
        })

    db = get_db()
    cur = db.execute(
        "select * from words where date is null order by random() limit 1")
    word = cur.fetchone()
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    db.execute(
        "update words set date='" + now + "' where id=" + str(word['id']))
    db.commit()
    return jsonify({
        'success': True,
    })

@app.route('/recent', methods=['GET'])
def recent_words_of_the_day():
    db = get_db()
    cur = db.execute(
        "select * from words " \
        "where date is not null order by date desc limit 7")
    words = cur.fetchall()

    response = {
        'words': []
    }

    for w in words:
        response['words'].append({'text': w['text'], 'date': w['date']})

    return jsonify(response)

@app.route('/from/<from_date>/to/<to_date>', methods=['GET'])
def get_words_in_range(from_date, to_date):
    if not validate_date(from_date) or not validate_date(to_date):
        return jsonify({
            'error': 'One or both of the dates provided are invalid. ' \
            'Must be YYYY-MM-DD.'
        })

    if from_date > to_date:
        return jsonify({
            'error': 'From date must occur before to date.'
        })

    db = get_db()
    cur = db.execute(
        "select * from words \
            where date is not null and date between '" +
            from_date + "' and '" + to_date + "' order by date desc")
    words = cur.fetchall()

    response = {
        'words': []
    }

    for w in words:
        response['words'].append({'text': w['text'], 'date': w['date']})

    return jsonify(response)

if __name__ == "__main__":
    app.run()

    # schedule.every().day.at('14:51').do(set_word_of_the_day)

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)