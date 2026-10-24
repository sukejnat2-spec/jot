import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-only-for-home')

def get_connection():
    return sqlite3.connect('../notetakingManager.db')

def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text Text NOT NULL,
        data TEXT NOT NULL,
        user_id INTEGER NOT NULL
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
        )    
    """)
    connection.commit()
    connection.close()
init_db()

def current_user():
    return session.get('user_id')


@app.route('/')
def index():
    if current_user() is None:
        return redirect('/login')

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('select * from users where user_id = ?', (current_user(),))
    rows = cursor.fetchall()
    cursor.close()
    return render_template('html5.html', notes=rows)

@app.route('/add', methods=['POST'])
def add():
    if current_user() is None:
        return redirect('/login')

    text = request.form['note']
    data = datetime.now().strftime('%d.%m.%Y %H:%M')

    if text != '':
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('insert into users (text, data, user_id) values (?, ?, ?)', (text, data, current_user()))
        connection.commit()
        cursor.close()

    return redirect('/')

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete(note_id):
    if current_user() is None:
        return redirect('/login')

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('delete from users where id = ? and user_id = ?', (note_id, current_user(),))
    connection.commit()
    cursor.close()
    return redirect('/')

@app.route('/edit/<int:note_id>')
def edit_from(note_id):
    if current_user() is None:
        return redirect('/login')

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('select * from users where id = ? and user_id = ?', (note_id, current_user(),))
    note = cursor.fetchone()
    cursor.close()
    if note is None:
        return redirect('/')


    return render_template('edit.html', note=note)

@app.route('/edit/<int:note_id>', methods=['POST'])
def edit_to(note_id):
    if current_user() is None:
        return redirect('/login')

    text = request.form['note']
    if text != '':
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('update users set text = ? where id = ? and user_id = ?', (text, note_id, current_user(),))
        connection.commit()
        cursor.close()
    return redirect('/')


@app.route('/register')
def register_from():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    if username == '' or password == '':
        return redirect('register')

    password_hash = generate_password_hash(password)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "insert into accounts (username, password_hash) values (?, ?)",
            (username, password_hash)
        )
        connection.commit()

    except sqlite3.IntegrityError:
        connection.close()
        return redirect('register')
    connection.close()

    return redirect('/')

@app.route('/login')
def login_form():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute('select id, password_hash from accounts where username = ?', (username,))
    accounts = cursor.fetchone()
    cursor.close()

    if accounts is None or not check_password_hash(accounts[1], password):
        return redirect('/login')

    session['user_id'] = accounts[0]
    session['username'] = username
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
