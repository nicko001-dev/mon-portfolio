import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from portfolio.models import (
    Profile, HeroStage, ProblemStatement, SkillGroup,
    Project, Certification, TrainingItem,
    SiteText, NavItem, MarqueeItem, ManifestoStat, FocusItem, ContactItem,
    UniverseBody,
)


OBSOLETE_TEXT_KEYS = [
    "home_cta1", "scroll_cue", "space_title", "space_text", "space_cta", "space_loader",
]


class _Upsert:
    """Comme ``Model.objects`` mais sans écraser l'existant (sauf avec --reset)."""

    def __init__(self, model, reset):
        self.model, self.reset = model, reset

    def update_or_create(self, defaults=None, **lookup):
        mgr = self.model.objects
        fn = mgr.update_or_create if self.reset else mgr.get_or_create
        return fn(defaults=defaults, **lookup)


class Command(BaseCommand):
    help = (
        "Remplit la base avec le contenu du portfolio de Nick. Par défaut, ne crée que "
        "ce qui manque (tes modifications faites dans l'admin sont conservées). "
        "Avec --reset, réécrit tout avec les valeurs du code."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="ÉCRASE le contenu existant avec les valeurs du code (efface les modifications d'admin).",
        )

    def upsert(self, model):
        return _Upsert(model, self.reset)

    def handle(self, *args, **options):
        self.reset = options["reset"]
        self.seed_profile()
        self.seed_universe_bodies()
        self.seed_skill_groups()
        self.seed_projects()
        self.seed_certifications()
        self.seed_training()
        self.seed_site_text()
        self.seed_nav()
        self.seed_marquee()
        self.seed_manifesto_stats()
        self.seed_focus_items()
        self.seed_contact_items()
        self.ensure_admin()
        call_command("seed_chatbot", stdout=self.stdout)
        mode = "réinitialisé (--reset)" if self.reset else "complété (rien d'existant n'a été écrasé)"
        self.stdout.write(self.style.SUCCESS(f"Contenu du portfolio {mode}."))

    def seed_profile(self):
        self.upsert(Profile).update_or_create(
            pk=1,
            defaults=dict(
                name="Nick Kakaye",
                role="Étudiant en génie logiciel",
                school="ESATIC — École Supérieure Africaine des TIC",
                program="Licence 3 SIGL",
                program_year="Année 2026-2027",
                location="Abidjan, Côte d'Ivoire",
                email="nickkakaye4@gmail.com",
                bio_p1=(
                    "Je suis en troisième année de licence Système Informatique et Génie "
                    "Logiciel à l'ESATIC, à Abidjan. Mes projets se situent à la croisée de "
                    "l'IA, du développement logiciel et de la confidentialité."
                ),
                bio_p2=(
                    "J'apprends en construisant : je pars souvent de zéro dans un domaine et "
                    "je mène chaque projet jusqu'au bout. Je préfère les outils libres et "
                    "locaux — une IA sur le téléphone plutôt que dans le cloud — mais je sais "
                    "aussi construire des solutions qui fonctionnent en ligne quand c'est ce "
                    "qu'il faut."
                ),
                looking_for="à la recherche d'un stage de fin d'année académique",
                stat_projects=6,
                stat_certifications=5,
                stat_technologies=10,
                stat_years=3,
                quote="Je fabrique pour comprendre.",
            ),
        )

    def seed_hero_stages(self):
        # Troisième partie : on ne garde que la PREMIÈRE MOITIÉ du mouvement des
        # particules (identité puis dispersion). L'ampoule et le globe — la
        # seconde moitié — sont volontairement retirés.
        stages = [
            dict(order=1, shape="brain",
                 eyebrow="Étudiant en génie logiciel",
                 title="Construire pour comprendre.",
                 body="Je conçois des applications intelligentes, du concept au dernier "
                      "détail — pensées pour fonctionner en local comme en ligne.",
                 cta_label="Voir mes projets", cta_href="#projects"),
            dict(order=2, shape="brain",
                 title="Apprendre en construisant.",
                 body="Je pars souvent de zéro dans un domaine et je mène chaque projet "
                      "jusqu'au bout, avec curiosité et rigueur."),
            dict(order=3, shape="dissolve"),
        ]
        for s in stages:
            self.upsert(HeroStage).update_or_create(order=s["order"], defaults=s)
        # Supprime les anciennes étapes (ampoule, globe…) si elles existent encore.
        HeroStage.objects.exclude(order__in=[s["order"] for s in stages]).delete()

    def seed_problem_statements(self):
        lines = [
            "Beaucoup d'outils intelligents dépendent d'un serveur distant.",
            "Ils exposent vos données pour fonctionner correctement.",
            "Ils deviennent inutilisables sans connexion internet.",
            "Il existe une autre voie : l'intelligence embarquée, en local.",
            "Des modèles qui tournent sur l'appareil, sans compromis sur la confidentialité.",
            "C'est cette voie que j'explore, projet après projet.",
        ]
        for i, text in enumerate(lines, start=1):
            self.upsert(ProblemStatement).update_or_create(order=i, defaults={"text": text})

    def seed_universe_bodies(self):
        """Textes des astres de l'univers 3D (soleil, planètes, trou noir, lieux)."""
        bodies = [
            ("sun", "SOLEIL ALPHA", "NICK KAKAYE · INGÉNIERIE & IA",
             "Étudiant en Système Informatique & Génie Logiciel à l'ESATIC (Abidjan). "
             "Concepteur de solutions IA et logicielles."),
            ("saturnia", "SATURNIA", "FORMATION ESATIC",
             "3e année Licence Système Informatique & Génie Logiciel — ESATIC, Abidjan (2026)."),
            ("verdania", "VERDANIA", "CE QUI M'ANIME",
             "Second Brain, Jarvis, IA locale et vision par ordinateur : donner de "
             "l'intelligence aux objets du quotidien."),
            ("jovis9", "JOVIS-9", "COMPÉTENCES CLÉS",
             "Python (Django, PyTorch), Mobile (Flutter), Systèmes C/C++, Docker, PostgreSQL, WebSockets."),
            ("ignis", "IGNIS", "CERTIFICATIONS",
             "5 Certifications Cisco obtenues en 2026 (CCNA, CyberOps, Python, Data Science, IoT)."),
            ("cryos", "CRYOS", "CONTACT & STAGE",
             "Disponible pour un stage de fin de cycle. Basé à Abidjan — ouvert au télétravail international."),
            ("blackhole", "SINGULARITÉ", "PORTE VERS L'ATELIER", ""),
            ("station", "ARCHE ORBITALE", "ATELIER & EXPERTISE", ""),
            ("galaxy", "GALAXIE SPIRALE", "", ""),
            ("kuiper", "CEINTURE KUIPER-X", "", ""),
            ("crystals", "CRISTAUX D'ÉTHER", "", ""),
        ]
        for i, (key, name, subtitle, info) in enumerate(bodies, start=1):
            self.upsert(UniverseBody).update_or_create(
                key=key,
                defaults={"order": i, "name": name, "subtitle": subtitle, "info": info},
            )

    def seed_skill_groups(self):
        groups = [
            ("Mobile & jeux", "Flutter, Dart, Firebase (Firestore, Auth), Unity, Unreal Engine"),
            ("IA en local", "llama.cpp, LM Studio, RAG, embeddings, MediaPipe, Vosk. Notions de CNN, RNN, Transformers et GAN"),
            ("Web & données", "Django, React, PostgreSQL, SQL, AWS, Git et GitHub"),
            ("Langages", "Java (POO, Swing, Maven, POI, iText), C++, C, C# (Unity), Python, Kotlin, Dart, XML"),
            ("Réseaux & sécurité", "Packet Tracer, CIDR et VLSM, SSH, routage, commutation, Kali Linux en environnement d'apprentissage"),
            ("Objets connectés", "Arduino"),
        ]
        for i, (name, desc) in enumerate(groups, start=1):
            self.upsert(SkillGroup).update_or_create(order=i, defaults={"name": name, "description": desc})

    def seed_projects(self):
        projects = [
            dict(order=1, monogram="SB", title="Second Brain", tag="IA locale",
                 kind="Application mobile d'IA 100 % locale",
                 description="Une application Flutter qui fait tourner un modèle de langage "
                              "directement sur le téléphone. Elle interroge les notes de "
                              "l'utilisateur par RAG, sans qu'aucune donnée ne quitte "
                              "l'appareil. J'en ai aussi tiré un cours de 16 chapitres pour "
                              "expliquer sa construction.",
                 stack="Flutter · llama.cpp (FFI) · Qwen3-1.7B · RAG · SQLite FTS5"),
            dict(order=2, monogram="JV", title="Jarvis", tag="IA locale",
                 kind="Assistant vocal hors-ligne",
                 description="Un assistant qui écoute et répond sans connexion internet, "
                              "avec une mémoire persistante. Je l'ai fait évoluer sur "
                              "plusieurs versions, en changeant de briques au fil de mes "
                              "tests.",
                 stack="Python · LM Studio · Vosk · Mémoire JSON"),
            dict(order=3, monogram="NY", title="NAYO", tag="Jeu éducatif",
                 kind="Jeu éducatif pour apprendre le bété",
                 description="Un jeu Android pour apprendre une langue de Côte d'Ivoire. "
                              "Construit selon une feuille de route en plusieurs étapes "
                              "réalisées : dialogues, fenêtre de vocabulaire, choix du "
                              "joueur et transitions entre scènes.",
                 stack="Unity · Android"),
            dict(order=4, monogram="EV", title="EcoValor CI", tag="Mobile",
                 kind="Application mobile",
                 description="Une application Flutter reliée à un backend Firebase : base "
                              "de données Firestore, authentification des utilisateurs et "
                              "navigation entre les écrans.",
                 stack="Flutter · Firebase · Firestore · Auth"),
            dict(order=5, monogram="CG", title="Contrôle par gestes", tag="Vision par ordinateur",
                 kind="Vision par ordinateur",
                 description="Un système qui pilote l'ordinateur sans souris, avec les "
                              "gestes de la main captés par caméra.",
                 stack="Python · MediaPipe Tasks · EAR"),
            dict(order=6, monogram="+", title="Et aussi", tag="Et aussi",
                 kind="Autres réalisations",
                 description="Bot WhatsApp de rangement de fichiers (whatsapp-web.js, LM "
                              "Studio) et application de gestion académique (Java Swing).",
                 stack="whatsapp-web.js · LM Studio · Java Swing"),
        ]
        for p in projects:
            self.upsert(Project).update_or_create(order=p["order"], defaults=p)

    def seed_certifications(self):
        certs = [
            dict(order=1, slug="cyber", title="Introduction à la cybersécurité",
                 org="Cisco Networking Academy", date="13 septembre 2026"),
            dict(order=2, slug="ds", title="Introduction à la science des données",
                 org="Cybastion IT Academy", date="14 avril 2026"),
            dict(order=3, slug="ia", title="Introduction à l'IA moderne",
                 org="Cybastion IT Academy", date="14 avril 2026"),
            dict(order=4, slug="itn", title="CCNA : Présentation des réseaux",
                 org="ESATIC", date="11 mai 2026"),
            dict(order=5, slug="srwe", title="CCNA : Switching, Routing, and Wireless Essentials",
                 org="ESATIC", date="18 août 2026"),
        ]
        for c in certs:
            self.upsert(Certification).update_or_create(order=c["order"], defaults=c)

    def seed_training(self):
        items = [
            ("Réseaux", "Adressage IP, CIDR, VLSM. Packet Tracer : routeurs et switchs en "
                        "ligne de commande, SSH, sécurisation de base."),
            ("Génie logiciel", "Cascade, V, spirale, agile. Scrum, Kanban, XP, SAFe, LeSS, MVC."),
            ("Bases de données", "SQL, jointures, algèbre relationnelle."),
            ("Théorie des graphes", "Dijkstra, Bellman, Kruskal, PERT et MPM."),
            ("Développement web", "Django, React, PostgreSQL, Git et GitHub en travaux pratiques."),
        ]
        for i, (title, desc) in enumerate(items, start=1):
            self.upsert(TrainingItem).update_or_create(order=i, defaults={"title": title, "description": desc})

    def seed_site_text(self):
        # (clé, libellé, valeur, groupe) — le groupe sert à ranger l'admin.
        texts = [
            # Général (tout le site)
            ("seo_title", "Titre de l'onglet du navigateur", "Nick Kakaye — Portfolio", "general"),
            ("seo_description", "Description pour Google et les aperçus de liens",
             "Nick Kakaye — étudiant Système Informatique et Génie Logiciel à l'ESATIC (Abidjan). "
             "IA locale, développement mobile et logiciels construits de bout en bout.", "general"),
            ("home_video_url", "Adresse (URL) de la vidéo de l'accueil",
             "https://strvid.nyc3.cdn.digitaloceanspaces.com/cloudinary/portfolio_hero_bg_zuhahj.webm", "general"),
            # Accueil (UI A)
            ("brand", "Nom affiché en haut à gauche", "Nick Kakaye", "accueil"),
            ("header_cta", "Bouton de l'en-tête", "Me contacter", "accueil"),
            ("home_greet", "Formule d'accueil (haut de page)", "Bonjour, je suis", "accueil"),
            ("home_title_enter", "Bouton « entrer dans l'univers »", "Entrer dans mon univers", "accueil"),
            ("home_cta2", "Bouton 2 de l'accueil", "Me contacter", "accueil"),
            ("home_avail", "Titre de la carte « disponible »", "Disponible pour un stage", "accueil"),
            # Univers 3D (UI B)
            ("hs_back_home", "Bouton « retour accueil » de l'univers", "Accueil", "univers"),
            ("hs_quest_title", "Titre de la quête (balise)", "TROU NOIR", "univers"),
            ("hs_transmission", "Badge de la transmission planétaire", "TRANSMISSION STELLAIRE", "univers"),
            ("hs_planet_default", "Nom de planète (avant découverte)", "PLANÈTE", "univers"),
            ("hs_target_label", "Étiquette de la cible (HUD)", "CIBLE", "univers"),
            ("hs_speed_label", "Étiquette de la vitesse (HUD)", "VITESSE", "univers"),
            ("hs_radar_legend", "Légende du radar", "RADAR STELLAIRE", "univers"),
            ("hs_cmds_pc_tag", "Titre du bloc commandes PC", "[COMMANDES PC]", "univers"),
            ("hs_cmds_touch_tag", "Titre du bloc commandes tactiles", "[COMMANDES TACTILES]", "univers"),
            ("hs_cmds_pc_body", "Commandes PC — texte (les [MOTS] sont mis en gras)",
             "[MOLETTE] Propulsion · [ZQSD / WASD] Translation\n[CLIC + GLISSER] Vue 360° · "
             "[ESPACE / C] Monter / Descendre\n[MAJ] Turbo · [M] Son", "univers"),
            ("hs_cmds_touch_body", "Commandes tactiles — texte (les [MOTS] sont mis en gras)",
             "[JOYSTICK] Déplacement · [GLISSER] Regarder autour à 360°\n[▲ / ▼] Hauteur", "univers"),
            ("hs_planet_desc_default", "Description de planète (avant découverte)", "Détails", "univers"),
            ("hs_toast_welcome_title", "Message d'arrivée — titre", "BIENVENUE DANS L'UNIVERS", "univers"),
            ("hs_toast_welcome_text", "Message d'arrivée — texte",
             "Quête : Trouve le trou noir pour accéder à l'Atelier !", "univers"),
            ("hs_toast_discovery", "Message « découverte » d'un corps céleste", "DÉCOUVERTE", "univers"),
            ("hs_toast_warp_title", "Message du trou noir — titre", "HORIZON FRANCHI", "univers"),
            ("hs_toast_warp_text", "Message du trou noir — texte", "Entrée dans l'Atelier...", "univers"),
            ("hs_toast_return_title", "Message de retour dans l'univers — titre", "RETOUR DANS L'UNIVERS", "univers"),
            ("hs_toast_return_text", "Message de retour dans l'univers — texte", "Cap maintenu vers les étoiles.", "univers"),
            # Atelier (UI C)
            ("lilo_intro_tag", "Sur-titre du manifeste", "01 / L'atelier", "atelier"),
            ("lilo_intro_h1", "Titre du manifeste (1re ligne)", "Je fabrique", "atelier"),
            ("lilo_intro_h2", "Titre du manifeste (2e ligne, contour)", "pour comprendre", "atelier"),
            ("metier_tag", "Sur-titre de « Ce qui m'anime »", "02 / Ce qui m'anime", "atelier"),
            ("skills_tag", "Sur-titre Compétences", "03 / Boîte à outils", "atelier"),
            ("skills_title", "Titre Compétences", "Compétences", "atelier"),
            ("training_tag", "Sur-titre Formation", "04 / Diplôme en cours", "atelier"),
            ("projects_tag", "Sur-titre Projets", "05 / Travaux récents", "atelier"),
            ("projects_title", "Titre Projets", "Projets réalisés", "atelier"),
            ("projects_lead", "Introduction Projets",
             "Construits de bout en bout, souvent en partant de zéro dans le domaine.", "atelier"),
            ("certs_tag", "Sur-titre Certifications", "06 / Reconnaissances", "atelier"),
            ("certs_title", "Titre Certifications", "Certifications", "atelier"),
            ("certs_lead", "Introduction Certifications",
             "Cinq certificats obtenus en 2026. Cliquez pour voir le document.", "atelier"),
            ("contact_tag", "Sur-titre Contact", "07 / Contact", "atelier"),
            ("contact_copy", "Bouton « copier l'adresse »", "Copier l'adresse", "atelier"),
            ("contact_up", "Lien « retour en haut »", "Retour en haut", "atelier"),
            ("atelier_home", "Bouton « revenir à l'accueil » de l'atelier", "Revenir à l'accueil", "atelier"),
            ("atelier_universe", "Bouton « retourner dans l'univers »", "Retourner dans mon univers", "atelier"),
            ("atelier_home_short", "Bouton « accueil » (version courte, mobile)", "Accueil", "atelier"),
            ("atelier_universe_short", "Bouton « univers » (version courte, mobile)", "Univers", "atelier"),
            ("contact_copied", "Message après « copier l'adresse »", "Adresse copiée", "atelier"),
            ("colophon", "Mention finale", "Conçu et développé par Nick Kakaye · Abidjan", "pied"),
            # Navigation & pied de page
            ("nav_projects", "Menu : Projets", "Projets", "navigation"),
            ("nav_skills", "Menu : Compétences", "Compétences", "navigation"),
            ("nav_training", "Menu : Formation", "Formation", "navigation"),
            ("nav_certs", "Menu : Certifications", "Certifications", "navigation"),
            ("nav_contact", "Menu : Contact", "Contact", "navigation"),
            ("footer_line", "Ligne du pied de page", "© 2026 Nick Kakaye. Conçu et développé.", "pied"),
        ]
        for key, label, value, group in texts:
            obj, created = SiteText.objects.get_or_create(
                key=key, defaults={"label": label, "value": value, "group": group},
            )
            if created:
                continue
            # L'emplacement (libellé, groupe) suit toujours le code ; la VALEUR n'est
            # écrasée qu'avec --reset, pour ne jamais perdre tes modifications d'admin.
            changed = []
            if obj.label != label:
                obj.label = label; changed.append("label")
            if obj.group != group:
                obj.group = group; changed.append("group")
            if self.reset and obj.value != value:
                obj.value = value; changed.append("value")
            if changed:
                obj.save(update_fields=changed)
        # Textes qui ne s'affichaient plus nulle part : on les retire de l'admin.
        SiteText.objects.filter(key__in=OBSOLETE_TEXT_KEYS).delete()

    def seed_nav(self):
        links = [
            (1, "Accueil", "#home", False, True),
            (2, "Projets", "#projects", True, True),
            (3, "Compétences", "#skills", True, True),
            (4, "Formation", "#training", False, True),
            (5, "Certifications", "#certs", True, True),
            (6, "Contact", "#cta", False, True),
        ]
        for order, label, anchor, in_nav, in_drawer in links:
            self.upsert(NavItem).update_or_create(
                order=order,
                defaults=dict(label=label, anchor=anchor, show_in_nav=in_nav, show_in_drawer=in_drawer),
            )

    def seed_marquee(self):
        words = ["IA locale & cloud", "Mobile", "Vision par ordinateur", "Réseaux", "Web", "Jeux"]
        for i, text in enumerate(words, start=1):
            self.upsert(MarqueeItem).update_or_create(order=i, defaults={"text": text})

    def seed_manifesto_stats(self):
        stats = [(6, "Projets menés"), (5, "Certifications"), (10, "Technologies"), (3, "Années d'atelier")]
        for i, (value, label) in enumerate(stats, start=1):
            self.upsert(ManifestoStat).update_or_create(order=i, defaults={"value": value, "label": label})

    def seed_focus_items(self):
        items = [
            ("Faire jaillir les idées.",
             "Second Brain, Jarvis, la reconnaissance de gestes : autant d'expériences pour "
             "donner une intelligence locale et réactive à des objets du quotidien."),
            ("Un métier sans frontières.",
             "Mobile, web, jeu vidéo, réseaux : je navigue entre les briques techniques pour "
             "donner vie à une idée, quel que soit le terrain."),
        ]
        for i, (title, body) in enumerate(items, start=1):
            self.upsert(FocusItem).update_or_create(order=i, defaults={"title": title, "body": body})

    def seed_contact_items(self):
        items = [
            ("École", "ESATIC — École Supérieure Africaine des TIC\nLicence 3 SIGL · Année 2026-2027", False),
            ("Où", "Abidjan, Côte d'Ivoire", False),
            ("Écrire", "nickkakaye4@gmail.com", True),
            ("Remonter", "#home", False),
        ]
        for i, (label, value, copyable) in enumerate(items, start=1):
            self.upsert(ContactItem).update_or_create(
                order=i, defaults={"label": label, "value": value, "copyable": copyable},
            )

    def ensure_admin(self):
        """Crée (ou réinitialise) le compte administrateur à partir de variables
        d'environnement. Utile sur un hébergeur sans accès terminal (Render).
        Sans DJANGO_SUPERUSER_PASSWORD, la commande ne touche à rien."""
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not password:
            return
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "nicko")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if email:
            user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        action = "créé" if created else "réinitialisé"
        self.stdout.write(self.style.SUCCESS(f"Compte administrateur « {username} » {action}."))
