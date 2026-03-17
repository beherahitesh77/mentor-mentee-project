from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ---------------- DB ----------------
def create_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS tasks (mentor TEXT, mentee TEXT, task TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (sender TEXT, receiver TEXT, msg TEXT)")

    conn.commit()
    conn.close()

create_db()

# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?)", (name, role))
        conn.commit()
        conn.close()

        if role == "mentor":
            return redirect('/mentor?user=' + name)
        else:
            return redirect('/mentee?user=' + name)

    return render_template('login.html')


# ---------------- MENTOR DASHBOARD ----------------
@app.route('/mentor', methods=['GET', 'POST'])
def mentor():
    user = request.args.get('user')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        mentee = request.form['mentee']
        task = request.form['task']
        c.execute("INSERT INTO tasks VALUES (?, ?, ?, ?)", (user, mentee, task, 'pending'))
        conn.commit()

    c.execute("SELECT mentee, task, status FROM tasks WHERE mentor=?", (user,))
    tasks = c.fetchall()

    conn.close()

    return render_template('mentor.html', user=user, tasks=tasks)


# ---------------- MENTEE DASHBOARD ----------------
@app.route('/mentee')
def mentee():
    user = request.args.get('user')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT task, status FROM tasks WHERE mentee=?", (user,))
    tasks = c.fetchall()

    conn.close()

    return render_template('mentee.html', user=user, tasks=tasks)


# ---------------- MARK DONE ----------------
@app.route('/done')
def done():
    task = request.args.get('task')
    user = request.args.get('user')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET status='done' WHERE task=? AND mentee=?", (task, user))
    conn.commit()
    conn.close()

    return redirect('/mentee?user=' + user)


# ---------------- CHAT ----------------
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user = request.args.get('user')
    other = request.args.get('other')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        msg = request.form['msg']
        c.execute("INSERT INTO messages VALUES (?, ?, ?)", (user, other, msg))
        conn.commit()

    c.execute("SELECT sender, msg FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)",
              (user, other, other, user))
    messages = c.fetchall()

    conn.close()

    return render_template('chat.html', user=user, other=other, messages=messages)


# ---------------- RUN ----------------
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)