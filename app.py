from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# ---------------- DATABASE PATH ----------------
DB_PATH = "database.db"

# if running on Render with disk
if os.path.exists("/data"):
    DB_PATH = "/data/database.db"


# ---------------- DB SETUP ----------------
def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT, role TEXT)")

    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        mentor TEXT,
        mentee TEXT,
        task TEXT,
        status TEXT,
        points INTEGER DEFAULT 0
    )""")

    # ensure points column exists (prevents crash)
    try:
        c.execute("ALTER TABLE tasks ADD COLUMN points INTEGER DEFAULT 0")
    except:
        pass

    c.execute("CREATE TABLE IF NOT EXISTS messages (sender TEXT, receiver TEXT, msg TEXT)")

    conn.commit()
    conn.close()


create_db()


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')

        if not name or not role:
            return redirect('/')

        name = name.lower().strip()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # avoid duplicate users
        c.execute("SELECT * FROM users WHERE name=?", (name,))
        if not c.fetchone():
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

    if not user:
        return redirect('/')

    user = user.lower().strip()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # assign task
    if request.method == 'POST':
        mentee = request.form.get('mentee')
        task = request.form.get('task')

        if mentee and task:
            mentee = mentee.lower().strip()

            c.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)",
                      (user, mentee, task, 'pending', 0))
            conn.commit()

    # get tasks
    c.execute("SELECT mentee, task, status, points FROM tasks WHERE mentor=?", (user,))
    tasks = c.fetchall()

    # leaderboard
    c.execute("SELECT mentee, SUM(points) FROM tasks WHERE mentor=? GROUP BY mentee", (user,))
    leaderboard = c.fetchall()

    conn.close()

    return render_template('mentor.html', user=user, tasks=tasks, leaderboard=leaderboard)


# ---------------- MENTEE DASHBOARD ----------------
@app.route('/mentee')
def mentee():
    user = request.args.get('user')

    if not user:
        return redirect('/')

    user = user.lower().strip()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT task, status, points FROM tasks WHERE mentee=?", (user,))
    tasks = c.fetchall()

    c.execute("SELECT SUM(points) FROM tasks WHERE mentee=?", (user,))
    total_points = c.fetchone()[0]

    if total_points is None:
        total_points = 0

    conn.close()

    return render_template('mentee.html', user=user, tasks=tasks, total_points=total_points)


# ---------------- MARK TASK DONE ----------------
@app.route('/done')
def done():
    task = request.args.get('task')
    user = request.args.get('user')

    if not task or not user:
        return redirect('/')

    user = user.lower().strip()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("UPDATE tasks SET status='done', points=10 WHERE task=? AND mentee=?",
              (task, user))

    conn.commit()
    conn.close()

    return redirect('/mentee?user=' + user)


# ---------------- CHAT ----------------
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user = request.args.get('user')
    other = request.args.get('other')

    if not user or not other:
        return redirect('/')

    user = user.lower().strip()
    other = other.lower().strip()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == 'POST':
        msg = request.form.get('msg')

        if msg:
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
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)