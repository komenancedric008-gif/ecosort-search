"""
app/ui/demo_fallback.py
------------------------
Ce module NE FAIT PAS partie du travail final de scraping (app/scraping/) ni
du modèle de Deep Learning (app/model/) — il sert uniquement de repli pour que
le frontend soit développable et démontrable de façon autonome, avant que les
PR de Neville (scraping) et de l'équipe Deep Learning ne soient fusionnées
dans main.

`app/ui/main.py` importe en priorité les vrais modules (`app.scraping...`,
`app.model...`) ; ce fichier n'est utilisé qu'en repli automatique (import
échoué). Une fois les vrais modules mergés, ce fichier n'est plus jamais
appelé — inutile de le supprimer, il ne fait aucun mal et reste utile pour
travailler en local en cas d'indisponibilité temporaire d'un module.
"""
import json
import os

_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "demo_products.json")

# Référentiel simplifié des 5 catégories (doit rester synchronisé avec
# app/model/label_mapping.py une fois ce module disponible).
CATEGORY_MAPPING = {
    "plastic": {
        "bin": "JAUNE", "color": "#FACC15", "text_on": "dark", "label": "Poubelle jaune", "icon": "package",
        "matiere": "plastique", "recyclable": True,
        "conseil": "Videz et rincez le contenant, puis remettez le bouchon avant de le jeter.",
    },
    "metal": {
        "bin": "JAUNE", "color": "#FACC15", "text_on": "dark", "label": "Poubelle jaune", "icon": "package",
        "matiere": "métal", "recyclable": True,
        "conseil": "Rincez la canette ou la boîte de conserve, inutile de retirer l'étiquette.",
    },
    "cardboard": {
        "bin": "JAUNE", "color": "#FACC15", "text_on": "dark", "label": "Poubelle jaune", "icon": "package",
        "matiere": "carton", "recyclable": True,
        "conseil": "Aplatissez le carton et retirez le scotch ou le film plastique.",
    },
    "glass": {
        "bin": "VERTE", "color": "#22C55E", "text_on": "light", "label": "Poubelle verte", "icon": "wine",
        "matiere": "verre", "recyclable": True,
        "conseil": "Videz complètement le contenant ; inutile de retirer les étiquettes.",
    },
    "paper": {
        "bin": "BLEUE", "color": "#2563EB", "text_on": "light", "label": "Poubelle bleue", "icon": "newspaper",
        "matiere": "papier", "recyclable": True,
        "conseil": "Retirez les élastiques ou pochettes plastiques avant de recycler.",
    },
    "trash": {
        "bin": "MARRON/NOIRE", "color": "#8B5E3C", "text_on": "light", "label": "Poubelle marron / noire", "icon": "trash-2",
        "matiere": "déchet non recyclable", "recyclable": False,
        "conseil": "Ce type de déchet n'est pas recyclable : jetez-le avec les ordures ménagères.",
    },
    "electronic": {
        "bin": "D3E", "color": "#6B7280", "text_on": "light", "label": "Bac électronique (D3E)", "icon": "cpu",
        "matiere": "appareil électrique", "recyclable": True,
        "conseil": "Retirez les piles ou la batterie avant de déposer l'appareil en point de collecte D3E.",
    },
}

ELECTRONIC_KEYWORDS = [
    "smartphone", "telephone", "téléphone", "chargeur", "ecouteur", "écouteur",
    "casque", "batterie", "montre connectee", "mixeur", "ordinateur", "tablette",
]

KEYWORD_FALLBACK = {
    "plastic":   ["bouteille", "plastique", "bidon", "flacon", "gobelet"],
    "metal":     ["canette", "conserve", "boite metal", "boîte métal"],
    "cardboard": ["carton", "colis"],
    "glass":     ["verre", "bocal", "pot", "vin", "confiture"],
    "paper":     ["papier", "journal", "magazine", "livre", "cahier", "revue"],
    "trash":     ["sachet", "sac plastique", "restes", "alimentaire", "dechets", "déchets"],
}


def _load_catalog():
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def search_products_demo(keyword, max_results=5):
    """Repli de app.scraping.jumia_scraper.search_products — catalogue local."""
    catalog = _load_catalog()
    keyword_low = (keyword or "").strip().lower()

    if keyword_low:
        matches = [
            p for p in catalog
            if keyword_low in p["name"].lower()
            or any(keyword_low in kw for kw in p.get("keywords", []))
        ]
    else:
        matches = []

    results = matches if matches else catalog
    return [
        {"name": p["name"], "price": p["price"], "image": p["image"], "link": p["link"], "source": "demo"}
        for p in results[:max_results]
    ]


def predict_category_demo(image_url, product_name=""):
    """Repli de app.model.inference.predict_category — classification par mots-clés."""
    name_low = (product_name or "").lower()

    if any(kw in name_low for kw in ELECTRONIC_KEYWORDS):
        info = CATEGORY_MAPPING["electronic"]
        return {"classe": "electronique", "mode": "keywords", **info}

    for category, keywords in KEYWORD_FALLBACK.items():
        if any(kw in name_low for kw in keywords):
            info = CATEGORY_MAPPING[category]
            return {"classe": category, "mode": "demo", **info}

    info = CATEGORY_MAPPING["trash"]
    return {"classe": "trash", "mode": "demo", **info}
