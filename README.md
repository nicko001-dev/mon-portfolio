# Portfolio de Nick Kakaye — projet Django

Portfolio personnel en Django, en trois écrans : un accueil cinématique avec
vidéo, un univers 3D navigable (Three.js) où l'on pilote un vaisseau, puis un
atelier classique que l'on atteint en franchissant un trou noir. Une bulle de
chat permet aussi de discuter avec un **assistant IA (OpenRouter)** qui connaît
Nick et le met en valeur.

Tout le contenu se modifie depuis l'espace d'administration : textes du site,
astres de l'univers 3D, projets, certifications, messages et réglages du chat.
(Seuls quelques messages d'erreur techniques du chat restent dans le code.)

## Démarrage rapide (en local)

```bash
python -m venv venv
venv\Scripts\activate           # Windows
source venv/bin/activate        # macOS / Linux
pip install -r requirements.txt

cp .env.example .env            # puis colle ta clé OpenRouter dans .env (voir plus bas)
python manage.py migrate
python manage.py seed_portfolio # remplit la base (ne détruit jamais l'existant)
python manage.py runserver
```

- Site : http://127.0.0.1:8000/
- Administration : http://127.0.0.1:8000/admin/ (compte : `python manage.py createsuperuser`)
- Tests : `python manage.py test portfolio`

Sous Windows, `start.bat` active le venv et lance `runserver`.

## Espace d'administration — les blocs suivent la page

La page d'accueil de l'admin est découpée en six blocs, **dans l'ordre réel du
site**, avec les mêmes noms que sur la page :

| Bloc de l'admin | Ce que ça change |
| --- | --- |
| **① Général** | Profil (nom, rôle, bio, e-mail, **photo téléversable**), titre de l'onglet, description Google, **vidéo d'accueil** |
| **② Écran 1 · Accueil** | textes et boutons de l'écran vidéo |
| **③ Écran 2 · Univers 3D** | **astres** (nom, sous-titre et transmission du soleil, des 5 planètes, du trou noir et des lieux), quête, radar, commandes PC/tactiles, messages affichés en vol. Les planètes-projets viennent de « Atelier 05 · Travaux récents » |
| **④ Écran 3 · Atelier** | de haut en bas : bandeau défilant → *01 L'atelier* (chiffres) → *02 Ce qui m'anime* → *03 Boîte à outils* → *04 Diplôme en cours* → *05 Travaux récents* → *06 Reconnaissances* (**images de certificats téléversables**) → *07 Contact* |
| **⑤ Navigation et pied de page** | liens de l'en-tête et du menu, textes du pied de page |
| **⑥ Assistant IA** | réglages et instructions, connaissances, journal des conversations |

Après une modification, recharge la page du site. `seed_portfolio` ne crée que
ce qui **manque** : relancer la commande ne touche jamais à tes modifications.
(`--reset` réécrit tout avec les valeurs du code — à n'utiliser qu'en
connaissance de cause.)

## Assistant IA (OpenRouter, modèles gratuits avec secours automatique)

**Ce qu'il fait** : répond à n'importe quelle question comme une IA généraliste,
mais son rôle principal est de présenter et valoriser Nick. Sur Nick, il ne
s'appuie que sur les informations fournies (il n'invente rien : il invite à
écrire à Nick quand il ne sait pas).

**Ce qu'il sait** — assemblé automatiquement avant chaque conversation :

1. des règles fixes (rôle, honnêteté, sécurité) ;
2. tes **instructions** : admin → *Assistant IA · réglages et instructions* ;
3. la **fiche issue du site** (profil, compétences, formation, projets,
   certifications, contact) — reconstruite à chaque message : modifier le site
   met l'IA à jour ;
4. tes **connaissances et consignes** : admin → *Assistant IA · connaissances
   et consignes* (une entrée = un fait ou une règle, activable/désactivable).

Dans la page des réglages, la section « Ce que l'IA lit exactement » affiche le
texte complet envoyé au modèle.

### Configurer les clés des fournisseurs

1. Crée une clé sur https://openrouter.ai/keys.
2. Fournis-la **uniquement** par la variable d'environnement `OPENROUTER_API_KEY` :
   - **en local** : dans le fichier `.env` (ignoré par git) ;
   - **PythonAnywhere** : dans le fichier WSGI, avec les autres variables
     (`os.environ["OPENROUTER_API_KEY"] = "..."`), puis **Reload** ;
   - **Render** : variable secrète dans le tableau de bord.
3. Dans l'admin → *Assistant IA · réglages et instructions*, clique sur
   **« Tester les fournisseurs IA »** pour vérifier les clés configurées et envoyer
   une vraie question.

Pour activer le secours Groq, crée aussi une clé sur https://console.groq.com/keys
et configure `GROQ_API_KEY` dans `.env`, dans les variables WSGI de PythonAnywhere
ou comme secret Render. Cette clé est optionnelle : OpenRouter continue de
fonctionner seul si elle est absente. Le code n'utilise chez Groq qu'une liste
autorisée de modèles gratuits présents dans le catalogue Groq ; les modèles payants
ne sont donc pas sélectionnés automatiquement. Groq documente son API compatible
OpenAI et son catalogue à https://console.groq.com/docs/models.

> ⚠️ Les clés ne doivent jamais être écrites dans le code, dans la base, dans un
> message ni dans un dépôt Git. Si une clé a été exposée, révoque-la chez son
> fournisseur et crée-en une nouvelle.

### Modèle

Laisse le champ « Modèle OpenRouter gratuit » **vide** (recommandé) : le site
interroge le catalogue OpenRouter, ne retient que les modèles dont l'identifiant
porte le suffixe `:free`, et consulte aussi le catalogue Groq si `GROQ_API_KEY`
est configurée. L'assistant alterne entre les deux fournisseurs et peut essayer
jusqu'à **dix modèles au total** (au plus dix par fournisseur si l'autre clé
manque). Si un modèle est indisponible, surchargé ou limité (quota), il passe au
suivant. Les catalogues sont mis en cache cinq minutes ; des listes de secours
connues sont prévues si un catalogue est temporairement inaccessible. Dans l'admin,
le modèle forcé doit rester un identifiant OpenRouter gratuit avec suffixe `:free`.

Les modèles et leurs quotas gratuits dépendent des fournisseurs et peuvent évoluer ;
Groq ne propose que des modèles gratuits de sa liste autorisée. La gratuité ne garantit
pas une disponibilité permanente.

### Si le chat répond « momentanément indisponible »

Les visiteurs ne voient jamais la cause technique ; toi, si :

1. Connecte-toi à `/admin/` **dans le même navigateur**, puis écris un message dans le chat :
   la bulle d'erreur affiche alors « Détail (visible par les admins) : … » avec la vraie raison.
2. Ou clique sur **« Tester les fournisseurs IA »** (admin → Assistant IA · réglages).
3. Ou ouvre *Assistant IA · conversations* et filtre « Réponse obtenue = Non » : la colonne
   d'erreur est enregistrée pour chaque échec.

Causes courantes : clé révoquée ou mal recopiée (`config` / « API key not valid ») — après
tout changement de `.env`, **redémarre `runserver`**, il ne le relit pas tout seul ;
quota gratuit épuisé (`quota`) ; modèle indisponible (`model`). Dans ces deux derniers cas,
le site essaie automatiquement jusqu'à dix modèles gratuits répartis entre OpenRouter
et Groq si leurs clés sont configurées.

### Protections intégrées

- clé uniquement côté serveur (jamais envoyée au navigateur) ;
- protection CSRF, limite par visiteur et par heure, plafond quotidien global
  (réglables) pour ne pas épuiser le quota gratuit ;
- les visiteurs ne sont identifiés que par une empreinte anonyme (l'adresse IP
  n'est pas stockée) ; l'enregistrement des conversations se désactive d'une case ;
- les réponses sont affichées sans HTML actif (pas d'injection possible).

### Aide dans l'univers 3D

L'univers est l'endroit où l'on se perd le plus facilement : l'assistant y est donc
**toujours disponible** et mis en avant.

- Tant que le visiteur ne l'a pas ouvert, le bouton passe en **mode alerte** (doré, ondes
  qui pulsent, bulle « Perdu ? Demandez-moi ! » — texte modifiable) au milieu du bord droit,
  là où il ne gêne ni le joystick ni le radar. L'alerte s'arrête au premier clic.
- Sur mobile, dans l'univers, le bouton peut être déplacé en le maintenant puis en le faisant
  glisser ; il reste dans l'écran et le glissement ne déclenche pas l'ouverture du chat.
- Les questions suggérées y restent affichées en permanence, à commencer par
  **« Dis-moi tout sur cet univers »** (listes modifiables dans les réglages du chat).
- L'IA connaît un **guide de l'univers 3D** reconstruit automatiquement : objectif (trouver le
  trou noir, porte vers l'Atelier), commandes PC et mobile, quête, radar, chaque astre et ce
  qu'il révèle sur Nick, lieux à découvrir. Il suit tes modifications de l'admin.
- Elle sait aussi dans quel écran se trouve le visiteur (accueil, univers, atelier) et
  adapte ses conseils.
- Taper dans le chat ne pilote **jamais** le vaisseau (clavier et molette isolés).

### Tirer pour actualiser (mobile)

Sur l'accueil, le défilement est désactivé (`.no-scroll`), ce qui supprime le geste natif
de rafraîchissement des navigateurs mobiles. `js/refresh.js` le recrée : tirer vers le bas,
relâcher au-delà du seuil → la page se recharge. Il est volontairement limité à l'accueil :
dans l'univers 3D, glisser le doigt sert à regarder autour de soi.

## Déploiement sur PythonAnywhere

1. Compte gratuit sur https://www.pythonanywhere.com/ → **Bash console**.
2. `git clone https://github.com/nicko001-dev/mon-portfolio.git portfolio && cd portfolio`
3. ```bash
   mkvirtualenv --python=/usr/bin/python3.13 portfolio
   pip install -r requirements.txt
   export DJANGO_SUPERUSER_PASSWORD='<choisis-un-mot-de-passe-solide>'
   python manage.py migrate
   python manage.py seed_portfolio
   python manage.py collectstatic --noinput
   ```
4. Onglet **Web** → *Add a new web app* → *Manual configuration* (Python 3.13),
   virtualenv `/home/<compte>/.virtualenvs/portfolio`.
5. Fichier WSGI :
   ```python
   import os, sys
   path = "/home/<compte>/portfolio"
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
   os.environ["DEBUG"] = "False"
   os.environ["SECRET_KEY"] = "<une-longue-chaine-aleatoire>"
   os.environ["ALLOWED_HOSTS"] = "<compte>.pythonanywhere.com"
   os.environ["CSRF_TRUSTED_ORIGINS"] = "https://<compte>.pythonanywhere.com"
   os.environ["OPENROUTER_API_KEY"] = "<ta-cle-openrouter>"
   os.environ["GROQ_API_KEY"] = "<ta-cle-groq>"  # optionnel, active le secours Groq

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
6. **Static files** : `/static/` → `/home/<compte>/portfolio/staticfiles`.
   Optionnel (plus rapide) : `/media/` → `/home/<compte>/portfolio/media`
   (sans cela, Django sert quand même les images téléversées).
7. **Reload**.

**Mettre à jour le site** après avoir poussé les changements sur `main` : dans la
Bash console de PythonAnywhere, exécute :

```bash
cd ~/portfolio
git pull --ff-only origin main
workon portfolio
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
```

Puis clique sur **Reload** dans l'onglet **Web**. `migrate` ne change rien s'il n'y
a pas de nouvelle migration. Réexécute `seed_portfolio` seulement si une mise à jour
ajoute de nouvelles données initiales ; ce n'est pas nécessaire pour chaque déploiement.

**Sauvegardes** : télécharge régulièrement `db.sqlite3` **et** le dossier
`media/` (photo, certificats téléversés) depuis l'onglet *Files*.

Vérifie que ton hébergeur autorise les appels sortants vers `openrouter.ai` et
`api.groq.com`, puis teste les fournisseurs depuis l'administration.

## Structure

```
config/                     réglages (settings.py, urls.py, wsgi.py)
portfolio/
  models.py                 contenus éditables, astres 3D, modèles de l'assistant IA
  admin.py                  admin découpé en blocs calés sur le site
  views.py                  page d'accueil + API du chat (/api/chat/)
  chatbot.py                prompt, clients OpenRouter/Groq, bascule des modèles, limites d'usage
  templatetags/             filtre « [MOTS] en gras » (échappe le HTML)
  management/commands/
    seed_portfolio.py       remplit la base sans rien écraser (--reset pour forcer)
    seed_chatbot.py         réglages et connaissances initiales de l'IA
  templates/portfolio/      base.html, index.html, _chatbot.html (widget)
  templates/admin/portfolio/chat_diagnostic.html   diagnostic des fournisseurs IA
  static/portfolio/
    css/style.css, css/chatbot.css, css/refresh.css
    js/hyperspace.js (univers 3D), core3d.js, main.js, chatbot.js, refresh.js
  tests.py                  tests du chat, des fournisseurs, de l'univers, de l'admin et du seed
```

## Notes

- **Base** : SQLite. Pour PostgreSQL, adapte `DATABASES` dans `config/settings.py`.
- **Sécurité** : `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `OPENROUTER_API_KEY` et
  `GROQ_API_KEY` viennent
  de l'environnement ; ne committe jamais de secret ni de mot de passe.
- **Pièges connus** :
  - `style.css` applique des règles globales aux balises `header`, `section` et `button`.
    Le widget de chat n'utilise donc que des `div` — ne les remplace pas par des balises
    sémantiques.
  - Un commentaire `{# … #}` ne fonctionne **que sur une seule ligne**. Sur plusieurs lignes,
    Django l'affiche tel quel et le navigateur interprète les balises qu'il contient : le chat
    s'était ainsi retrouvé enfermé dans un faux en-tête, invisible sous l'univers 3D. Utilise
    `{% comment %} … {% endcomment %}` (des tests vérifient le rendu réel de la page).
