from flask import Flask
import psycopg2
import os

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', 'postgres'),
        database=os.environ.get('POSTGRES_DB', 'dev_db'),
        user=os.environ.get('POSTGRES_USER', 'user'),
        password=os.environ.get('POSTGRES_PASSWORD', 'password')
    )
    return conn

@app.route('/')
def hello():
    return "Hello World from Backend!"

@app.route('/db')
def db_test():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1;')
        result = cur.fetchone()
        cur.close()
        conn.close()
        return f"Database Connected! Result: {result[0]}"
    except Exception as e:
        return f"Database Connection Failed: {e}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
