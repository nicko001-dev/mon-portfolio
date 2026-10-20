import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from portfolio.models import (
    Profile, HeroStage, ProblemStatement, SkillGroup,
    Project, Certification, TrainingItem,
    SiteText, NavItem, MarqueeItem, ManifestoStat, FocusItem, ContactItem,
)


class Command(BaseCommand):
    help = "Remplit (ou met à jour) la base avec le contenu réel du portfolio de Nick."

    def handle(self, *args, **options):
        self.seed_profile()
        self.seed_hero_stages()
        self.seed_problem_statements()
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
        self.stdout.write(self.style.SUCCESS("Contenu du portfolio chargé."))

    def seed_profile(self):
        Profile.objects.update_or_create(
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
            HeroStage.objects.update_or_create(order=s["order"], defaults=s)
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
            ProblemStatement.objects.update_or_create(order=i, defaults={"text": text})

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
            SkillGroup.objects.update_or_create(order=i, defaults={"name": name, "description": desc})

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
            Project.objects.update_or_create(order=p["order"], defaults=p)

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
            Certification.objects.update_or_create(order=c["order"], defaults=c)

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
            TrainingItem.objects.update_or_create(order=i, defaults={"title": title, "description": desc})

    def seed_site_text(self):
        # (clé, libellé, valeur, groupe) — le groupe sert à ranger l'admin.
        texts = [
            # Accueil (UI A)
            ("brand", "Nom affiché en haut à gauche", "Nick Kakaye", "accueil"),
            ("header_cta", "Bouton de l'en-tête", "Me contacter", "accueil"),
            ("home_greet", "Formule d'accueil (haut de page)", "Bonjour, je suis", "accueil"),
            ("home_title_enter", "Bouton « entrer dans l'univers »", "Entrer dans mon univers", "accueil"),
            ("home_cta1", "Bouton 1 de l'accueil", "Voir mes projets", "accueil"),
            ("home_cta2", "Bouton 2 de l'accueil", "Me contacter", "accueil"),
            ("home_avail", "Titre de la carte « disponible »", "Disponible pour un stage", "accueil"),
            ("scroll_cue", "Indication « défiler »", "Défiler", "accueil"),
            # Univers 3D (UI B)
            ("space_title", "Titre de la section 3D", "Applications intelligentes", "univers"),
            ("space_text", "Texte de la section 3D",
             "IA embarquée, mobile et vision par ordinateur — des projets pensés de bout en bout, souvent sans connexion.",
             "univers"),
            ("space_cta", "Bouton de la section 3D", "Découvrir mes projets", "univers"),
            ("space_loader", "Libellé de chargement de la 3D", "Chargement de l'expérience…", "univers"),
            ("hs_back_home", "Bouton « retour accueil » de l'univers", "Accueil", "univers"),
            ("hs_quest_title", "Titre de la quête (balise)", "TROU NOIR", "univers"),
            ("hs_transmission", "Badge de la transmission planétaire", "TRANSMISSION STELLAIRE", "univers"),
            ("hs_planet_default", "Nom de planète (avant découverte)", "PLANÈTE", "univers"),
            ("hs_target_label", "Étiquette de la cible (HUD)", "CIBLE", "univers"),
            ("hs_speed_label", "Étiquette de la vitesse (HUD)", "VITESSE", "univers"),
            ("hs_radar_legend", "Légende du radar", "RADAR STELLAIRE", "univers"),
            ("hs_cmds_pc_tag", "Titre du bloc commandes PC", "[COMMANDES PC]", "univers"),
            ("hs_cmds_touch_tag", "Titre du bloc commandes tactiles", "[COMMANDES TACTILES]", "univers"),
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
            SiteText.objects.update_or_create(
                key=key, defaults={"label": label, "value": value, "group": group},
            )

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
            NavItem.objects.update_or_create(
                order=order,
                defaults=dict(label=label, anchor=anchor, show_in_nav=in_nav, show_in_drawer=in_drawer),
            )

    def seed_marquee(self):
        words = ["IA locale & cloud", "Mobile", "Vision par ordinateur", "Réseaux", "Web", "Jeux"]
        for i, text in enumerate(words, start=1):
            MarqueeItem.objects.update_or_create(order=i, defaults={"text": text})

    def seed_manifesto_stats(self):
        stats = [(6, "Projets menés"), (5, "Certifications"), (10, "Technologies"), (3, "Années d'atelier")]
        for i, (value, label) in enumerate(stats, start=1):
            ManifestoStat.objects.update_or_create(order=i, defaults={"value": value, "label": label})

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
            FocusItem.objects.update_or_create(order=i, defaults={"title": title, "body": body})

    def seed_contact_items(self):
        items = [
            ("École", "ESATIC — École Supérieure Africaine des TIC\nLicence 3 SIGL · Année 2026-2027", False),
            ("Où", "Abidjan, Côte d'Ivoire", False),
            ("Écrire", "nickkakaye4@gmail.com", True),
            ("Remonter", "#home", False),
        ]
        for i, (label, value, copyable) in enumerate(items, start=1):
            ContactItem.objects.update_or_create(
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
