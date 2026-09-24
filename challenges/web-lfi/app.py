from flask import Flask, request
app = Flask(__name__)

@app.route("/")
def home():
    page = request.args.get("page", "home")
    try:
        content = open("/var/www/pages/" + page).read()
    except Exception as e:
        content = "No se pudo leer la pagina: " + str(e)
    return "<h1>Visor de paginas</h1><pre>" + content + "</pre>"

app.run(host="0.0.0.0", port=5000)
