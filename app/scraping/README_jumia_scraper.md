# Documentation du Scraper Jumia (`jumia_scraper.py`)

Ce module a pour but d'extraire des informations sur les produits depuis le site [Jumia Côte d'Ivoire](https://www.jumia.ci). 
Il a été conçu pour être robuste, gérer les erreurs réseau, et être facilement intégrable dans une application Flask ou tout autre script Python.

## 🚀 Fonctionnalités

- **Recherche par mot-clé** : Permet de rechercher n'importe quel produit et de récupérer les premiers résultats pertinents.
- **Extraction de données ciblées** : Récupère le nom du produit, son prix, l'URL de son image, et le lien vers la fiche produit.
- **Gestion avancée des erreurs** :
  - **Erreurs réseau** : Gère les timeouts et les indisponibilités du site avec un système de relance (retries) intelligent et progressif (backoff).
  - **Absence de résultats** : Identifie correctement si Jumia renvoie une page "Aucun résultat".
  - **Erreurs de parsing** : Détecte les changements potentiels de structure HTML du site.
- **Testable en CLI** : Peut être exécuté directement en ligne de commande pour des tests rapides.

## 🛠️ Prérequis et Installation

Le script s'appuie sur `requests` et `beautifulsoup4`. Assurez-vous d'avoir installé ces dépendances dans votre environnement :

```bash
pip install requests beautifulsoup4
```

## 💻 Utilisation

### 1. Utilisation comme module (ex: dans une route Flask)

La fonction principale à utiliser est `search_products(keyword, max_results=5)`.

```python
from jumia_scraper import search_products, NetworkError

try:
    # Recherche de "bouteille plastique" avec 3 résultats maximum
    resultats = search_products("bouteille plastique", max_results=3)
    
    if not resultats:
        print("Aucun produit trouvé.")
    else:
        for p in resultats:
            print(f"{p['name']} - {p['price']}")
            print(f"Lien: {p['link']}")
            
except NetworkError as e:
    print(f"Impossible de joindre Jumia : {e}")
```

**Format de retour :**
La fonction retourne une liste de dictionnaires. Chaque dictionnaire possède la structure suivante :
```json
{
  "name": "Nom du produit",
  "price": "Prix affiché (ex: 5,000 FCFA)",
  "image": "https://url-de-l-image.jpg",
  "link": "https://www.jumia.ci/lien-du-produit"
}
```

### 2. Utilisation en Ligne de Commande (CLI)

Vous pouvez lancer le script directement dans le terminal pour tester le scraping sur un mot-clé précis :

```bash
# Exemple de recherche
python jumia_scraper.py "ordinateur portable"
```

## ⚙️ Configuration et Maintenance

Les sélecteurs CSS utilisés pour extraire les données sont centralisés au début du fichier dans le dictionnaire `SELECTORS`. 
Si Jumia modifie la structure de son site web (changement de balises ou de classes CSS), **c'est le seul endroit que vous aurez besoin de mettre à jour**.

```python
SELECTORS = {
    "product_card": "article.prd",
    "name": "h3.name",
    "price": "div.prc",
    "image": "img.img",
    "link": "a.core",
    "no_results": "div.-df",
}
```

D'autres paramètres sont également ajustables selon vos besoins réseau :
- `REQUEST_TIMEOUT` : Temps d'attente maximum pour une requête HTTP (défaut : 10s).
- `MAX_RETRIES` : Nombre de tentatives en cas d'échec de connexion (défaut : 3).
- `RETRY_BACKOFF_SECONDS` : Temps d'attente de base entre deux tentatives (défaut : 1.5s).

## ⚠️ Exceptions personnalisées

Le module lève des exceptions spécifiques pour faciliter le débogage (bien que `search_products` gère la majorité en interne et retourne une liste vide) :
- `ScraperError` : Classe de base pour les erreurs du module.
- `NoResultsFoundError` : Le mot-clé n'a renvoyé aucun résultat sur le site.
- `NetworkError` : Le site Jumia est injoignable, trop lent, ou renvoie une erreur HTTP bloquante (ex: erreur 500). Remonte jusqu'à l'appelant.
- `ParsingError` : La structure HTML ne correspond pas aux sélecteurs attendus.
