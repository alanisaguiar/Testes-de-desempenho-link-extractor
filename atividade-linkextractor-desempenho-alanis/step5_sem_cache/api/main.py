from flask import Flask
from flask import request
import json
from linkextractor import extract_links

app = Flask(__name__)

@app.route("/")
def index():
    return "Usage: http://<hostname>[:<prt>]/api/<url>"

@app.route("/api/<path:url>")
def api(url):
    qs = request.query_string.decode("utf-8")

    if qs != "":
        url += "?" + qs

    # SEM CACHE:
    # Sempre extrai os links diretamente da URL,
    # sem consultar nem salvar no Redis.
    links = extract_links(url)
    jsonlinks = json.dumps(links, indent=2)

    response = app.response_class(
        status=200,
        mimetype="application/json",
        response=jsonlinks
    )

    return response

app.run(host="0.0.0.0")