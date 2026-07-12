"""
app/model/inference.py
----------------------
Module d'inférence du modèle EcoSort.

Charge le modèle MobileNetV2 fine-tuné une seule fois au démarrage,
puis expose la fonction predict_category(image_url, product_name)
utilisée par app/ui/main.py.

Stratégie de classification :
1. Détection D3E par mots-clés sur product_name (smartphones, chargeurs, etc.)
   → renvoyée directement, sans passer par le CNN
2. Sinon, téléchargement de l'image, prétraitement, inférence CNN
3. Mapping matière (6 classes) → poubelle (4 poubelles hors D3E)
"""
from __future__ import annotations

import logging
import os
from io import BytesIO
from typing import Dict, Any

import numpy as np
import requests
from PIL import Image

import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

# Chemin absolu du modèle (résolu depuis l'emplacement de ce fichier)
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(_CURRENT_DIR, "modele_eco_sort.keras")

IMG_SIZE = (224, 224)

# Ordre des classes tel qu'appris par le CNN (ordre alphabétique)
CLASS_NAMES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# Mapping matière → poubelle finale
MATIERE_TO_BIN = {
    "cardboard": "JAUNE",
    "metal":     "JAUNE",
    "plastic":   "JAUNE",
    "glass":     "VERTE",
    "paper":     "BLEUE",
    "trash":     "MARRON",
}

# Métadonnées UI par poubelle
BIN_METADATA = {
    "JAUNE":  {"color": "#FACC15", "label": "Poubelle Jaune"},
    "VERTE":  {"color": "#22C55E", "label": "Poubelle Verte"},
    "BLEUE":  {"color": "#2563EB", "label": "Poubelle Bleue"},
    "D3E":    {"color": "#6B7280", "label": "Bac Électronique (D3E)"},
    "MARRON": {"color": "#8B5E3C", "label": "Poubelle Marron / Noire"},
}

# Mots-clés pour la détection D3E (appareils électriques/électroniques)
D3E_KEYWORDS = {
    "smartphone", "telephone", "téléphone", "phone", "iphone", "samsung",
    "tablette", "tablet", "ipad",
    "ecouteur", "écouteur", "casque", "headphone", "earphone", "airpods",
    "chargeur", "charger", "cable", "câble", "usb",
    "batterie", "battery", "pile", "power bank", "powerbank",
    "montre", "watch", "smartwatch",
    "mixeur", "blender", "grille-pain", "toaster", "cafetière", "cafetiere",
    "ordinateur", "laptop", "pc", "computer",
    "television", "télévision", "tv", "ecran", "écran", "monitor",
    "clavier", "keyboard", "souris", "mouse",
    "console", "playstation", "xbox", "nintendo",
    "appareil photo", "camera", "caméra",
    "electromenager", "électroménager",
}


# ============================================================
# CHARGEMENT DU MODÈLE (une seule fois au démarrage)
# ============================================================

_model: tf.keras.Model | None = None


def _get_model() -> tf.keras.Model:
    """Charge le modèle de manière paresseuse au premier appel."""
    global _model
    if _model is None:
        logger.info("Chargement du modèle depuis %s ...", MODEL_PATH)
        _model = load_model(MODEL_PATH)
        logger.info("Modèle chargé ✅")
    return _model


# ============================================================
# HELPERS
# ============================================================

def _is_electronic(product_name: str) -> bool:
    """Retourne True si le nom de produit contient un mot-clé D3E."""
    if not product_name:
        return False
    name_lower = product_name.lower()
    return any(keyword in name_lower for keyword in D3E_KEYWORDS)


def _download_and_preprocess(image_url: str) -> np.ndarray:
    """Télécharge une image depuis une URL et la prépare pour le CNN."""
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()

    img = Image.open(BytesIO(response.content)).convert("RGB")
    img = img.resize(IMG_SIZE)

    img_array = np.array(img, dtype=np.float32)
    img_array = preprocess_input(img_array)          # -> plage [-1, 1]
    img_array = np.expand_dims(img_array, axis=0)    # ajouter dim batch
    return img_array


def _build_result(bin_code: str, matiere: str, confidence: float, source: str) -> Dict[str, Any]:
    """Construit le dict de retour attendu par le frontend."""
    meta = BIN_METADATA[bin_code]
    return {
        "bin": bin_code,
        "color": meta["color"],
        "label": meta["label"],
        "matiere": matiere,
        "confidence": round(confidence, 4),
        "source": source,
    }


# ============================================================
# API PUBLIQUE
# ============================================================

def predict_category(image_url: str, product_name: str) -> Dict[str, Any]:
    """
    Détermine la poubelle correspondant à un produit.

    Paramètres :
        image_url    : URL de l'image du produit (issue du scraping Jumia)
        product_name : nom textuel du produit (issu du scraping Jumia)

    Retourne :
        Dict avec bin, color, label, matiere, confidence, source
    """

    # --- 1. Détection D3E par mots-clés (prioritaire, court-circuite le CNN)
    if _is_electronic(product_name):
        logger.info("D3E détecté par mot-clé pour : %s", product_name)
        return _build_result(
            bin_code="D3E",
            matiere="electronic",
            confidence=1.0,
            source="keywords",
        )

    # --- 2. Inférence CNN
    try:
        img_array = _download_and_preprocess(image_url)
        model = _get_model()
        probas = model.predict(img_array, verbose=0)[0]

        predicted_idx = int(np.argmax(probas))
        matiere = CLASS_NAMES[predicted_idx]
        confidence = float(probas[predicted_idx])
        bin_code = MATIERE_TO_BIN[matiere]

        logger.info(
            "Prédiction CNN : %s (%.2f%%) → poubelle %s",
            matiere, confidence * 100, bin_code
        )
        return _build_result(bin_code, matiere, confidence, source="cnn")

    except Exception as exc:
        logger.error("Échec inférence CNN : %s", exc)
        # Fallback : on renvoie Marron par défaut (déchet résiduel non identifié)
        return _build_result(
            bin_code="MARRON",
            matiere="unknown",
            confidence=0.0,
            source="fallback_error",
        )