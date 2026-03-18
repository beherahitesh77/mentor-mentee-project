from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ---------------- DB ----------------
def create_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT, role TEXT)")
    
    # Added points column
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
                mentor TEXT, 
                mentee TEXT, 
                task TEXT, 
                status TEXT,
                points INTEGER
                )""")

    c.execute("CREATE TABLE IF NOT EXISTS messages (sender TEXT, receiver TEXT, msg TEXT)")

    conn.commit()
    conn.close()

create_db()

# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].lower()
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
    user = request.args.get('user').lower()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Assign task
    if request.method == 'POST':
        mentee = request.form['mentee'].lower()
        task = request.form['task']

        c.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", 
                  (user, mentee, task, 'pending', 0))
        conn.commit()

    # Get tasks
    c.execute("SELECT mentee, task, status, points FROM tasks WHERE mentor=?", (user,))
    tasks = c.fetchall()

    # Get points per mentee
    c.execute("SELECT mentee, SUM(points) FROM tasks WHERE mentor=? GROUP BY mentee", (user,))
    leaderboard = c.fetchall()

    conn.close()

    return render_template('mentor.html', user=user, tasks=tasks, leaderboard=leaderboard)


# ---------------- MENTEE DASHBOARD ----------------
@app.route('/mentee')
def mentee():
    user = request.args.get('user').lower()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT task, status, points FROM tasks WHERE mentee=?", (user,))
    tasks = c.fetchall()

    # total points
    c.execute("SELECT SUM(points) FROM tasks WHERE mentee=?", (user,))
    total_points = c.fetchone()[0]

    if total_points is None:
        total_points = 0

    conn.close()

    return render_template('mentee.html', user=user, tasks=tasks, total_points=total_points)


# ---------------- MARK DONE ----------------
@app.route('/done')
def done():
    task = request.args.get('task')
    user = request.args.get('user').lower()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # update status + give 10 points
    c.execute("UPDATE tasks SET status='done', points=10 WHERE task=? AND mentee=?", (task, user))

    conn.commit()
    conn.close()

    return redirect('/mentee?user=' + user)


# ---------------- CHAT ----------------
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user = request.args.get('user').lower()
    other = request.args.get('other').lower()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        msg = request.form['msg']
        c.execute("INSERT INTO messages VALUES (?, ?, ?)", (user, other, msg))
        conn.commit()

    c.execute("""SELECT sender, msg FROM messages 
                 WHERE (sender=? AND receiver=?) 
                 OR (sender=? AND receiver=?)""",
              (user, other, other, user))

    messages = c.fetchall()

    conn.close()

    return render_template('chat.html', user=user, other=other, messages=messages)


# ---------------- RUN ----------------
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)