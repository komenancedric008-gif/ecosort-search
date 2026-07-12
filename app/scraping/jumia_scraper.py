"""
scraper/jumia_scraper.py

Module de scraping de la plateforme Jumia pour le projet
EcoSort-Search.

Responsable : kouassi Neville 

Ce module expose une fonction unique destinée à être consommée par les
routes Flask (app.py) :

    search_products(keyword, max_results=5) -> list[dict]

Chaque résultat est un dictionnaire :
    {
        "name":  str,   # nom du produit
        "price": str,   # prix affiché tel quel 
        "image": str,   # URL de l'image produit
        "link":  str,   # URL de la fiche produit
    }

Gestion des cas d'erreur couverts:
    - Timeout réseau / site injoignable
    - Aucun résultat trouvé pour le mot-clé recherché
    - Changement de structure HTML du site (sélecteurs CSS obsolètes)

"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

logger = logging.getLogger("ecosort.scraper")
logging.basicConfig(level=logging.INFO)

# Domaine Jumia ciblé 
BASE_URL = "https://www.jumia.ci/catalog/?q="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

REQUEST_TIMEOUT = 10          # secondes
MAX_RETRIES = 3                # tentatives en cas d'échec réseau
RETRY_BACKOFF_SECONDS = 1.5    # délai entre deux tentatives (progressif)
DEFAULT_MAX_RESULTS = 5

# Sélecteurs CSS regroupés ici pour être mis à jour facilement en un seul
# endroit si Jumia modifie la structure de ses pages.
SELECTORS = {
    "product_card": "article.prd",
    "name": "h3.name",
    "price": "div.prc",
    "image": "img.img",
    "link": "a.core",
    # Bloc affiché par Jumia lorsque la recherche ne renvoie rien.
    "no_results": "div.-df",
}


# --------------------------------------------------------------------------- #
# Exceptions dédiées
# --------------------------------------------------------------------------- #

class ScraperError(Exception):
    """Erreur générique du module de scraping."""


class NoResultsFoundError(ScraperError):
    """Aucun produit trouvé pour le mot-clé recherché."""


class NetworkError(ScraperError):
    """Le site Jumia est injoignable, trop lent, ou renvoie une erreur HTTP."""


class ParsingError(ScraperError):
    """La structure HTML de la page ne correspond plus aux sélecteurs attendus."""


# --------------------------------------------------------------------------- #
# Modèle de données
# --------------------------------------------------------------------------- #

@dataclass
class Product:
    name: str
    price: str
    image: str
    link: str

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Récupération HTML avec gestion des erreurs réseau et retries
# --------------------------------------------------------------------------- #

def _build_search_url(keyword: str) -> str:
    
    return BASE_URL + quote_plus(keyword.strip())


def _fetch_html(url: str) -> str:

    last_exception: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text # Le texte de la page

        except requests.exceptions.Timeout as exc:
            last_exception = exc
            logger.warning("Timeout (tentative %s/%s) sur %s", attempt, MAX_RETRIES, url)

        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            # Une 4xx (hors 429) ne se réglera pas en réessayant : on sort tout de suite.
            if exc.response is not None and exc.response.status_code not in (429, 500, 502, 503, 504):
                raise NetworkError(f"Erreur HTTP {status} sur {url}") from exc
            last_exception = exc
            logger.warning("Erreur HTTP %s (tentative %s/%s) sur %s", status, attempt, MAX_RETRIES, url)

        except requests.exceptions.ConnectionError as exc:
            last_exception = exc
            logger.warning("Erreur de connexion (tentative %s/%s) sur %s", attempt, MAX_RETRIES, url)

        except requests.exceptions.RequestException as exc:
            # Filet de sécurité pour toute autre erreur requests non prévue explicitement.
            last_exception = exc
            logger.warning("Erreur requests (tentative %s/%s) : %s", attempt, MAX_RETRIES, exc)

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)  # backoff progressif

    raise NetworkError(
        f"Impossible de joindre Jumia après {MAX_RETRIES} tentatives : {last_exception}"
    ) from last_exception


# --------------------------------------------------------------------------- #
# Extraction des résultats depuis le HTML
# --------------------------------------------------------------------------- #

def _extract_product(card) -> Optional[Product]:
    name_tag = card.select_one(SELECTORS["name"])
    if not name_tag:
        return None

    price_tag = card.select_one(SELECTORS["price"])
    image_tag = card.select_one(SELECTORS["image"])
    link_tag = card.select_one(SELECTORS["link"])

    image_url = ""
    if image_tag:
        image_url = image_tag.get("data-src") or image_tag.get("src") or ""

    link_url = ""
    if link_tag and link_tag.get("href"):
        href = link_tag["href"]
        link_url = href if href.startswith("http") else f"https://www.jumia.ci{href}"

    return Product(
        name=name_tag.get_text(strip=True),
        price=price_tag.get_text(strip=True) if price_tag else "N/A",
        image=image_url,
        link=link_url,
    )


def _parse_results(html: str, max_results: int) -> list[Product]:

    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select(SELECTORS["product_card"])

    if not cards:
        """
         On distingue "recherche sans résultat" (Jumia affiche un bloc
         dédié) d'un "site cassé" (ni cartes produit, ni bloc "aucun
         résultat" détecté -> la structure a probablement changé, ou le
         contenu est chargé dynamiquement en JS -> on tente Selenium).
        """
        if soup.select_one(SELECTORS["no_results"]):
            raise NoResultsFoundError("Aucun produit trouvé pour cette recherche.")
        raise ParsingError(
            "La page reçue ne correspond pas à la structure HTML attendue "
            "(ni cartes produit, ni bloc 'aucun résultat' détecté). Le site "
            "a peut-être changé, ou le contenu est chargé en JavaScript : "
            "vérifier les sélecteurs CSS."
        )

    products: list[Product] = []
    for card in cards:
        product = _extract_product(card)
        if product is not None:
            products.append(product)
        if len(products) >= max_results:
            break

    if not products:
        raise ParsingError(
            "Des cartes produit ont été détectées mais aucune n'a pu être "
            "extraite correctement. Vérifier les sélecteurs name/price/image/link."
        )

    return products





# --------------------------------------------------------------------------- #
# Fonction publique principale
# --------------------------------------------------------------------------- #

def search_products(
    keyword: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> list[dict]:
    """
    Recherche un produit sur Jumia et retourne jusqu'à max_results résultats.

    Args:
        keyword: terme recherché par l'utilisateur (ex: "bouteille plastique").
        max_results: nombre maximum de résultats à retourner (3 à 5 selon
            le cahier des charges).

    Returns:
        Liste de dictionnaires {name, price, image, link}. Liste vide si
        aucun résultat trouvé (l'appelant / la route Flask décide de
        l'affichage : message "aucun résultat", etc.).

    Raises:
        NetworkError: site injoignable après plusieurs tentatives.
    """
    if not keyword or not keyword.strip():
        logger.info("Recherche avec mot-clé vide : retour d'une liste vide.")
        return []

    url = _build_search_url(keyword)
    logger.info("Recherche Jumia : %r -> %s", keyword, url)

    html = _fetch_html(url)

    try:
        products = _parse_results(html, max_results)

    except NoResultsFoundError:
        logger.info("Aucun résultat pour %r.", keyword)
        return []

    except ParsingError as exc:
        logger.error("Echec du parsing : %s", exc)
        return []

    return [p.to_dict() for p in products]


# --------------------------------------------------------------------------- #
# tests rapides
# --------------------------------------------------------------------------- #
"""
utiliser "object_search" pour lancer un test
"""

object_search= "voitures" # le l'objet rechercher

if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or object_search
    try:
        results = search_products(query)
        if not results:
            print(f"Aucun résultat pour « {query} ».")
        else:
            for i, produit in enumerate(results, start=1):
                print(f"{i}. {produit['name']} — {produit['price']}")
                print(f"   image: {produit['image']}")
                print(f"   lien:  {produit['link']}")
    except NetworkError as e:
        print(f"Erreur réseau : {e}")
