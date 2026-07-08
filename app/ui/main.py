"""
app/ui/main.py
----------------
Application Flask EcoSort-Search — point d'entrée utilisé par Gunicorn
(voir Dockerfile : CMD gunicorn ... app.ui.main:app).

⚠️ Ne renommez pas la variable `app` ni ce fichier : Gunicorn cible
   précisément `app.ui.main:app`.

Imports défensifs :
Le scraping (app/scraping/) et le modèle de Deep Learning (app/model/) sont
développés en parallèle par d'autres membres de l'équipe, sur d'autres
branches. Pour pouvoir développer et démontrer le frontend sans attendre la
fusion de leurs PR, ce fichier tente d'abord d'importer les vrais modules et,
en cas d'échec (module pas encore présent sur cette branche), bascule sur un
repli local (app/ui/demo_fallback.py). Dès que les PR de scraping/model seront
fusionnées dans main, les vrais modules seront utilisés automatiquement, sans
modification de ce fichier.
"""
import logging

from flask import Flask, jsonify, render_template, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# --- Scraping : app.scraping.jumia_scraper (Neville) ---
try:
    from app.scraping.jumia_scraper import search_products
    logger.info("Module de scraping réel chargé (app.scraping.jumia_scraper).")
except ImportError:
    from app.ui.demo_fallback import search_products_demo as search_products
    logger.warning(
        "app.scraping.jumia_scraper introuvable — utilisation du catalogue de "
        "démonstration (app/ui/demo_fallback.py) en attendant la fusion de la "
        "branche feature/scraping."
    )

# --- Deep Learning : app.model.inference (équipe Deep Learning) ---
try:
    from app.model.inference import predict_category
    logger.info("Module d'inférence réel chargé (app.model.inference).")
except ImportError:
    from app.ui.demo_fallback import predict_category_demo as predict_category
    logger.warning(
        "app.model.inference introuvable — utilisation du classificateur par "
        "mots-clés (app/ui/demo_fallback.py) en attendant la fusion de la "
        "branche feature/deep-learning."
    )


STATS = {
    "total_analyses": 15842,
    "accuracy": 97.3,
    "breakdown": [
        {"bin": "JAUNE", "color": "#FACC15", "label": "Jaune", "percent": 45},
        {"bin": "BLEUE", "color": "#2563EB", "label": "Bleue", "percent": 20},
        {"bin": "VERTE", "color": "#22C55E", "label": "Verte", "percent": 18},
        {"bin": "D3E", "color": "#6B7280", "label": "D3E", "percent": 9},
        {"bin": "MARRON", "color": "#8B5E3C", "label": "Marron", "percent": 8},
    ],
}

TEAM = [
    {"name": "Wilfried KOMENAN", "role": "Deep Learning & DevOps (Docker, GitHub)"},
    {"name": "Neville KOUASSI", "role": "Scraping Jumia"},
    {"name": "Adirou MFONDOUM", "role": "Interface Flask"},
]


@app.route("/")
def index():
    return render_template("index.html", stats=STATS)


@app.route("/guide")
def guide():
    return render_template("guide.html")


@app.route("/statistiques")
def statistiques():
    return render_template("stats.html", stats=STATS)


@app.route("/a-propos")
def a_propos():
    return render_template("about.html", team=TEAM)


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    keyword = (data.get("keyword") or request.form.get("keyword") or "").strip()

    if not keyword:
        return jsonify({"error": "Merci de saisir le nom d'un produit à rechercher.", "produits": []}), 400

    produits = search_products(keyword, max_results=6)
    source = produits[0].get("source", "jumia") if produits else "demo"
    return jsonify({"produits": produits, "keyword": keyword, "source": source})


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    image_url = data.get("image_url", "")
    product_name = data.get("product_name", "")

    if not product_name:
        return jsonify({"error": "product_name est requis"}), 400

    category = predict_category(image_url, product_name)
    return jsonify(category)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "EcoSort-Search"})


if __name__ == "__main__":
    # Utilisé uniquement en exécution directe (python app/ui/main.py), hors
    # Docker : Gunicorn ignore ce bloc et importe directement `app`.
    app.run(host="0.0.0.0", port=8501, debug=True)
