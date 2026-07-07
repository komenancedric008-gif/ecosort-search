"""
Stub minimal Flask pour valider le pipeline Docker.
Ce fichier sera remplacé par la vraie app par le coéquipier frontend.
"""
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <html>
      <head>
        <title>EcoSort-Search</title>
        <style>
          body {
            font-family: system-ui, sans-serif;
            background: #f4f4f4;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
          }
          .card {
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            text-align: center;
          }
          h1 { color: #2c7a2c; }
          p { color: #555; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>♻️ EcoSort-Search</h1>
          <p>Pipeline Docker opérationnel ✅</p>
          <p><small>Stub temporaire — en attente de l'app Flask complète</small></p>
        </div>
      </body>
    </html>
    """


@app.route("/health")
def health():
    return {"status": "ok"}