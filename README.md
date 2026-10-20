# Portfolio de Nick Kakaye — projet Django

Portfolio personnel en Django (modèles + vues + templates), en trois écrans :
un accueil cinématique avec vidéo, un univers 3D navigable (WebGL/Three.js)
où l'on pilote un vaisseau, puis un atelier classique (bande défilante +
sections en grands titres) que l'on atteint en franchissant un trou noir.

Tout le contenu se modifie depuis l'espace d'administration : aucun texte n'est
figé dans le code.

## Démarrage rapide

```bash
python -m venv venv
venv\Scripts\activate           # Windows
source venv/bin/activate        # macOS / Linux
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_portfolio  # remplit la base avec le contenu réel
python manage.py runserver
```

- Site : http://127.0.0.1:8000/
- Administration : http://127.0.0.1:8000/admin/

Sous Windows, `start.bat` fait tout cela (activation du venv + `runserver`).

## Espace d'administration

L'accès est protégé par authentification : `/admin/` renvoie vers la page de
connexion tant que l'on n'est pas identifié. Le compte superutilisateur :

- utilisateur : `nicko`
- adresse : `nickkakaye4@gmail.com`
- mot de passe : celui fourni au moment de la création du compte

Pour créer ou réinitialiser le compte :

```bash
python manage.py createsuperuser
```

Ou, sans interaction (utile sur un hébergeur) :

```bash
python manage.py seed_portfolio
```

en définissant au préalable `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_EMAIL` et `DJANGO_SUPERUSER_PASSWORD` : la commande
`seed_portfolio` crée alors le compte administrateur et met le mot de passe à
jour.

## Modifier le contenu

Tout vient de la base de données, modifiable dans `/admin/` sans toucher au
code. Les entrées de l'admin sont numérotées dans l'ordre réel du site, pour
s'y retrouver d'un coup d'œil :

| Entrée de l'admin | Ce que ça change sur le site |
| --- | --- |
| **1 · Profil & accueil** | nom, rôle, école, bio, e-mail, photo, chiffres de secours |
| **2 · Accueil — étapes du hero** | les états du nuage (titre, texte, bouton) |
| **3 · Accueil — phrases qui défilent** | les phrases de l'étape « dispersion » |
| **Libellés & textes du site** | tous les libellés, filtrés par groupe : Accueil, Univers 3D, Atelier, Navigation, Pied de page |
| **4 · Atelier — Compétences** | les groupes de la boîte à outils |
| **5 · Atelier — Travaux récents** | les cartes de projets |
| **6 · Atelier — Reconnaissances** | les certifications (image via le « fichier image ») |
| **7 · Atelier — Formation (matière)** | les lignes de la section Formation |
| **8 · Atelier — bandeau défilant** | les mots du bandeau en tête de l'atelier |
| **9 · Atelier — chiffres animés** | les compteurs animés du manifeste |
| **10 · Atelier — « Ce qui m'anime »** | les lignes de la section « Ce qui m'anime » |
| **11 · Atelier — Contact** | les blocs de la grille de contact |
| **Navigation — liens** | les liens de l'en-tête et du menu latéral |

Les contenus de l'univers 3D (textes de la quête, radar, HUD, commandes)
se règlent eux aussi depuis « Libellés & textes du site », groupe **Univers 3D**.

Après une modification dans l'admin, il suffit de recharger la page. Pour
changer les valeurs que `seed_portfolio` installe, modifier
`portfolio/management/commands/seed_portfolio.py` puis relancer la commande
(elle met à jour les lignes existantes, elle ne duplique pas).

## Déploiement sur PythonAnywhere

PythonAnywhere héberge le code et le service web, mais **la base SQLite ne
persiste pas de façon fiable** sur les comptes gratuits si tu recrées le
dossier : prévois de garder une copie de `db.sqlite3` (ou de repasser par
`seed_portfolio`), et note que les fichiers statiques doivent être déclarés
séparément (voir plus bas).

### 1. Créer le compte

1. Crée un compte gratuit sur https://www.pythonanywhere.com/
2. Ouvre un **Bash console** depuis le tableau de bord.

### 2. Récupérer le projet

Envoie le code sur GitHub, puis dans la console :

```bash
git clone https://github.com/<ton-compte>/<ton-depot>.git portfolio
cd portfolio
```

Sans GitHub, tu peux utiliser l'onglet **Files** pour téléverser une archive
zip du projet, puis la décompresser.

### 3. Créer l'environnement virtuel et installer

```bash
mkvirtualenv --python=/usr/bin/python3.13 portfolio
pip install -r requirements.txt
```

### 4. Configurer et remplir la base

Crée un fichier `.env`-like n'est pas nécessaire : PythonAnywhere permet de
définir des variables d'environnement dans le fichier WSGI (étape 6). Pour
l'instant, en ligne de commande :

```bash
export DJANGO_SUPERUSER_PASSWORD='Nicko10203@'
python manage.py migrate
python manage.py seed_portfolio
python manage.py collectstatic --noinput
```

`collectstatic` remplit `staticfiles/`, qui sera servi par PythonAnywhere.

### 5. Créer l'application web

1. Onglet **Web** → **Add a new web app** → **Manual configuration**.
2. Choisis la même version de Python que le virtualenv (3.13).
3. Dans **Virtualenv**, indique :
   `/home/<ton-compte>/.virtualenvs/portfolio`

### 6. Renseigner le fichier WSGI

Clique sur le lien du fichier WSGI (**Web** → **Code** → *WSGI configuration
file*) et remplace son contenu par :

```python
import os
import sys

path = "/home/<ton-compte>/portfolio"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DEBUG"] = "False"
os.environ["SECRET_KEY"] = "<une-longue-chaine-aleatoire>"
os.environ["ALLOWED_HOSTS"] = "<ton-compte>.pythonanywhere.com"
os.environ["CSRF_TRUSTED_ORIGINS"] = "https://<ton-compte>.pythonanywhere.com"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Remplace `<ton-compte>` par ton identifiant PythonAnywhere.

### 7. Déclarer les fichiers statiques

Dans **Web** → **Static files**, ajoute :

| URL | Directory |
| --- | --- |
| `/static/` | `/home/<ton-compte>/portfolio/staticfiles` |

L'admin Django (CSS/JS) est inclus dans `staticfiles/` après `collectstatic`,
donc il s'affichera correctement.

### 8. Recharger

Clique sur le bouton vert **Reload**, puis ouvre
`https://<ton-compte>.pythonanywhere.com/`.

### À savoir sur l'offre gratuite

- Si tu modifies du contenu en ligne, **exporte régulièrement `db.sqlite3`** :
  l'onglet **Files** permet de le télécharger, ce qui te sert de sauvegarde.
- Le site gratuit s'endort après un moment d'inactivité et se réveille à la
  première visite (quelques secondes).
- Pour republier une modification du code : dans la console, `git pull` puis
  **Reload** dans l'onglet **Web**.

## Structure

```
config/                    réglages du projet (settings.py, urls.py, wsgi.py)
portfolio/
  models.py                les 13 modèles éditables depuis l'admin
  admin.py                 enregistrement et réglages de l'admin
  views.py                 assemble le contexte de la page
  urls.py                  la route du site
  management/commands/
    seed_portfolio.py       remplit la base avec le contenu réel
  templates/portfolio/
    base.html               en-tête, menu mobile, pied de page, visionneuse
    index.html              les trois écrans (accueil, univers, atelier)
  static/portfolio/
    css/style.css            thème sombre, mise en page
    js/hyperspace.js         univers 3D navigable (vaisseau, radar, quête)
    js/core3d.js             fond 3D de l'atelier
    js/main.js               interactions de l'atelier et de l'accueil
    js/three.min.js          Three.js r128 (fichier local, pas de CDN)
    fonts/                    Sora + Inter, fichiers réels
    img/                      photo + certificats (webp)
```

## Notes

- **Base de données** : SQLite (`db.sqlite3`). Pour PostgreSQL, changer
  `DATABASES` dans `config/settings.py` et installer le pilote.
- **Fichiers statiques** : WhiteNoise est activé (`CompressedStaticFilesStorage`),
  ce qui suffit sur la plupart des hébergeurs. Sur PythonAnywhere, la table
  **Static files** (étape 7) reste nécessaire.
- **Sécurité en production** : `SECRET_KEY`, `DEBUG=False` et `ALLOWED_HOSTS`
  sont lus depuis l'environnement ; ne jamais committer une vraie clé.
