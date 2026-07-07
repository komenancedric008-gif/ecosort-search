# ♻️ EcoSort-Search

Application web d'aide au tri sélectif combinant scraping e-commerce (Jumia) et classification par Deep Learning.

L'utilisateur saisit le nom d'un produit, l'application récupère les résultats sur Jumia, et un CNN classifie le produit sélectionné dans l'une des 5 catégories de tri officielles.

## 🗑️ Catégories de tri

| Catégorie | Couleur | Matières |
|---|---|---|
| Poubelle Jaune | 🟡 | plastic, metal, cardboard |
| Poubelle Verte | 🟢 | glass |
| Poubelle Bleue | 🔵 | paper |
| Bac Électronique (D3E) | ⚫ | appareils électriques |
| Poubelle Marron | 🟤 | trash (non recyclable) |

## 🏗️ Stack technique

- **Deep Learning** : TensorFlow / Keras (CNN + Transfer Learning)
- **Scraping** : BeautifulSoup / Requests (Jumia)
- **Interface Web** : Streamlit
- **Containerisation** : Docker

## 👥 Équipe

- **Wilfried KOMENAN** — Deep Learning & DevOps (Docker, GitHub)
- **[Neville KOUASSI]** — Scraping Jumia
- **[Adirou MFONDOUM]** — Interface Streamlit

## 🚀 Lancer le projet

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

Puis ouvrir : http://localhost:8501

## 📂 Structure