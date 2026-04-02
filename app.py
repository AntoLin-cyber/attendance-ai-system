from flask import Flask, render_template, request, redirect
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import os

app = Flask(__name__)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        attendance INTEGER,
        total_days INTEGER
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()

    return render_template('index.html', students=students)

# ---------- ADD STUDENT ----------
@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    email = request.form['email']

    if name.strip() == "" or email.strip() == "":
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "INSERT INTO students (name,email,attendance,total_days) VALUES (?,?,0,0)",
        (name, email)
    )

    conn.commit()
    conn.close()

    return redirect('/')

# ---------- MARK PRESENT ----------
@app.route('/mark/<int:id>')
def mark(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "UPDATE students SET attendance = attendance + 1, total_days = total_days + 1 WHERE id=?",
        (id,)
    )
    conn.commit()

    conn.close()
    return redirect('/')

# ---------- MARK ABSENT ----------
@app.route('/absent/<int:id>')
def absent(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "UPDATE students SET total_days = total_days + 1 WHERE id=?",
        (id,)
    )
    conn.commit()

    conn.close()
    return redirect('/')

# ---------- PREDICTION (AI PART) ----------
@app.route('/predict/<int:id>')
def predict(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT attendance, total_days FROM students WHERE id=?", (id,))
    data = c.fetchone()

    if not data:
        return "No data"

    attendance = int(data[0])
    total = int(data[1])

    if total == 0:
        return "Not enough data"

    current_percent = (attendance / total) * 100

    # ML Model
    X = []
    y = []

    for i in range(1, total + 1):
        X.append([i])
        y.append(current_percent)

    model = LinearRegression()
    model.fit(X, y)

    future = [[total + 5]]
    predicted = model.predict(future)[0]

    conn.close()

    return f"""
    <h2 style='text-align:center'>Prediction</h2>
    <p style='text-align:center'>Current: {round(current_percent,2)}%</p>
    <p style='text-align:center'>After 5 days: {round(predicted,2)}%</p>
    <div style='text-align:center'><a href='/'>Back</a></div>
    """

# ---------- GRAPH ----------
@app.route('/graph')
def graph():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query("SELECT name,attendance,total_days FROM students", conn)

    if len(df) == 0:
        return "No data"

    df['percent'] = df.apply(
        lambda row: (row['attendance']/row['total_days']*100) if row['total_days'] != 0 else 0,
        axis=1
    )

    if not os.path.exists("static"):
        os.makedirs("static")

    plt.bar(df['name'], df['percent'])
    plt.title("Attendance Analysis")
    plt.xlabel("Students")
    plt.ylabel("Percentage")

    plt.savefig("static/graph.png")
    plt.close()

    return render_template('graph.html')

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)