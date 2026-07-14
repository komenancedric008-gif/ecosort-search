"""
tests/test_scraper.py

Tests unitaires pour le module de scraping Jumia.
Ces tests sont mockés (pas d'appels réseau réels).
"""

import pytest
from bs4 import BeautifulSoup
import requests

from jumia_scraper import (
    search_products,
    _build_search_url,
    _extract_product,
    _parse_results,
    NetworkError,
    NoResultsFoundError,
    ParsingError,
    Product
)


# --------------------------------------------------------------------------- #
# Fixtures HTML (Mocks)
# --------------------------------------------------------------------------- #

HTML_VALID_CARDS = """
<html>
<body>
    <article class="prd">
        <a class="core" href="/produit-1.html">
            <img class="img" data-src="https://img.jumia.ci/1.jpg" />
            <div class="info">
                <h3 class="name">Produit 1 - Bouteille Plastique</h3>
                <div class="prc">1 500 FCFA</div>
            </div>
        </a>
    </article>
    <article class="prd">
        <a class="core" href="https://www.jumia.ci/produit-2.html">
            <img class="img" src="https://img.jumia.ci/2.jpg" />
            <div class="info">
                <h3 class="name">Produit 2 - Carton</h3>
                <div class="prc">2 000 FCFA</div>
            </div>
        </a>
    </article>
</body>
</html>
"""

HTML_NO_RESULTS = """
<html>
<body>
    <div class="-df -i-ctr -j-bet -pvs">
        <h2>Aucun résultat trouvé</h2>
    </div>
</body>
</html>
"""

HTML_INVALID_STRUCTURE = """
<html>
<body>
    <div class="random-div">
        <p>Site cassé ou changé</p>
    </div>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# Tests Unitaires
# --------------------------------------------------------------------------- #

def test_build_search_url():
    """Vérifie la construction et l'encodage de l'URL de recherche."""
    url = _build_search_url(" bouteille en plastique ")
    assert url == "https://www.jumia.ci/catalog/?q=bouteille+en+plastique"


def test_extract_product_valid():
    """Vérifie l'extraction d'un produit depuis un noeud HTML valide."""
    soup = BeautifulSoup(HTML_VALID_CARDS, "html.parser")
    cards = soup.select("article.prd")
    
    assert len(cards) == 2
    
    # Produit 1 (lien relatif, image data-src)
    product1 = _extract_product(cards[0])
    assert product1 is not None
    assert product1.name == "Produit 1 - Bouteille Plastique"
    assert product1.price == "1 500 FCFA"
    assert product1.image == "https://img.jumia.ci/1.jpg"
    assert product1.link == "https://www.jumia.ci/produit-1.html"
    
    # Produit 2 (lien absolu, image src)
    product2 = _extract_product(cards[1])
    assert product2 is not None
    assert product2.name == "Produit 2 - Carton"
    assert product2.price == "2 000 FCFA"
    assert product2.image == "https://img.jumia.ci/2.jpg"
    assert product2.link == "https://www.jumia.ci/produit-2.html"


def test_extract_product_missing_name():
    """Vérifie qu'un produit sans nom est ignoré (retourne None)."""
    html = """<article class="prd"><div class="prc">1000</div></article>"""
    soup = BeautifulSoup(html, "html.parser")
    card = soup.select_one("article.prd")
    assert _extract_product(card) is None


def test_parse_results_nominal():
    """Vérifie le parsing complet de plusieurs cartes."""
    products = _parse_results(HTML_VALID_CARDS, max_results=5)
    assert len(products) == 2
    assert isinstance(products[0], Product)


def test_parse_results_max_results():
    """Vérifie que max_results limite bien le nombre de produits retournés."""
    products = _parse_results(HTML_VALID_CARDS, max_results=1)
    assert len(products) == 1
    assert products[0].name == "Produit 1 - Bouteille Plastique"


def test_parse_results_no_results_found():
    """Vérifie qu'une page 'aucun résultat' lève la bonne exception."""
    with pytest.raises(NoResultsFoundError):
        _parse_results(HTML_NO_RESULTS, max_results=5)


def test_parse_results_parsing_error():
    """Vérifie qu'une structure inconnue lève une ParsingError."""
    with pytest.raises(ParsingError):
        _parse_results(HTML_INVALID_STRUCTURE, max_results=5)


# --------------------------------------------------------------------------- #
# Tests de la fonction publique (avec mocker)
# --------------------------------------------------------------------------- #

def test_search_empty_keyword():
    """Vérifie qu'un mot-clé vide retourne immédiatement une liste vide."""
    assert search_products("") == []
    assert search_products("   ") == []


def test_search_products_nominal(mocker):
    """Vérifie le flux complet en mockant _fetch_html."""
    mocker.patch("jumia_scraper._fetch_html", return_value=HTML_VALID_CARDS)
    
    results = search_products("test", max_results=5)
    
    assert len(results) == 2
    assert isinstance(results[0], dict)
    assert results[0]["name"] == "Produit 1 - Bouteille Plastique"


def test_search_products_no_results(mocker):
    """Vérifie que l'erreur 'aucun résultat' est bien attrapée et retourne []"""
    mocker.patch("jumia_scraper._fetch_html", return_value=HTML_NO_RESULTS)
    
    results = search_products("motcleimprobable")
    assert results == []


def test_search_products_parsing_error(mocker):
    """Vérifie que l'erreur de parsing est attrapée et retourne []"""
    mocker.patch("jumia_scraper._fetch_html", return_value=HTML_INVALID_STRUCTURE)
    
    results = search_products("test")
    assert results == []


def test_search_network_error(mocker):
    """Vérifie que l'erreur réseau remonte bien jusqu'à l'appelant."""
    mocker.patch(
        "jumia_scraper._fetch_html", 
        side_effect=NetworkError("Timeout")
    )
    
    with pytest.raises(NetworkError):
        search_products("test")
