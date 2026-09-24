from flask import Flask, request
import sqlite3
app = Flask(__name__)

con = sqlite3.connect("/tmp/app.db", check_same_thread=False)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)")
cur.execute("DELETE FROM users")
cur.execute("INSERT INTO users VALUES ('admin','S3cr3t-no-la-necesitas')")
con.commit()

@app.route("/")
def index():
    u = request.args.get("u", "")
    p = request.args.get("p", "")
    q = "SELECT * FROM users WHERE username='%s' AND password='%s'" % (u, p)
    try:
        rows = cur.execute(q).fetchall()
    except Exception as e:
        return "<pre>SQL error: %s\nQuery: %s</pre>" % (e, q)
    if rows:
        return "<h1>Bienvenido admin</h1><pre>" + open("/flag.txt").read() + "</pre>"
    return "<h1>Login fallido</h1><pre>Query: %s</pre>" % q

app.run(host="0.0.0.0", port=5000)
