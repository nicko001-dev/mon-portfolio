# Portfolio de Nick Kakaye — projet Django

Site portfolio en Django (modèles + vues + templates). Design inspiré d'une
référence « Dala » : particules qui se transforment en cerveau / ampoule /
globe au défilement, projets qui défilent en cartes, certifications en liste
éparpillée, tout en thème sombre violet/or.

## Démarrage rapide

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_portfolio  # remplit la base avec le contenu du portfolio
python manage.py createsuperuser # pour accéder à /admin/
python manage.py runserver
```

Le site est sur http://127.0.0.1:8000/ et l'administration sur
http://127.0.0.1:8000/admin/.

## Modifier le contenu

Tout le texte du site (hero, compétences, projets, certifications, formation)
vient de la base de données, modifiable dans `/admin/` sans toucher au code :

- **Profil** — nom, bio, email, statistiques de la section « À propos »
- **Étape du hero** — les 5 états du cerveau/ampoule/globe (texte + forme)
- **Phrases (dispersion)** — les phrases qui défilent pendant l'état « dissolve »
- **Groupe de compétences**, **Projets**, **Certifications**, **Point de formation**

Après une modification dans l'admin, il suffit de recharger la page — aucun
redémarrage du serveur n'est nécessaire.

Pour changer le texte de départ (celui que `seed_portfolio` installe), modifier
`portfolio/management/commands/seed_portfolio.py` et relancer la commande
(elle met à jour les lignes existantes, elle ne duplique pas).

## Structure

```
config/                 réglages du projet (settings.py, urls.py)
portfolio/
  models.py              Profile, HeroStage, ProblemStatement, SkillGroup,
                          Project, Certification, TrainingItem
  admin.py                enregistrement de tous les modèles
  views.py / urls.py      une vue qui assemble le contexte pour le template
  management/commands/
    seed_portfolio.py      remplit la base avec le contenu réel
  templates/portfolio/
    base.html               en-tête, menu mobile, pied de page, visionneuse
    index.html               toutes les sections de la page d'accueil
  static/portfolio/
    css/style.css            thème sombre, mise en page
    js/main.js                particules, défilement, visionneuse
    fonts/                    Sora (titres) + Inter (texte), fichiers réels
    img/                      photo + certificats, fichiers réels (webp)
```

## Notes

- **Base de données** : SQLite par défaut (`db.sqlite3`), suffisant pour un
  site de ce type. Pour PostgreSQL, changer `DATABASES` dans
  `config/settings.py`.
- **Avant une mise en ligne réelle** : passer `DEBUG = False` dans
  `config/settings.py`, remplacer `SECRET_KEY` par une valeur fraîche et
  secrète, et renseigner `ALLOWED_HOSTS` avec le nom de domaine. Prévoir aussi
  un vrai serveur (gunicorn/uwsgi derrière nginx, ou une plateforme comme
  Render/Railway/PythonAnywhere) — le serveur `runserver` est réservé au
  développement.
- **Fichiers statiques en production** : lancer `python manage.py
  collectstatic` et servir le dossier `staticfiles/` (ou utiliser
  WhiteNoise, non installé ici pour rester minimal).
- Le champ « EAR » dans la pile technique du projet « Contrôle par gestes »
  correspond à l'Eye Aspect Ratio — à ajuster si la description doit encore
  changer.
