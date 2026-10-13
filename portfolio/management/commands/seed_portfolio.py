from django.core.management.base import BaseCommand

from portfolio.models import (
    Profile, HeroStage, ProblemStatement, SkillGroup,
    Project, Certification, TrainingItem,
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
            dict(order=4, shape="lightbulb",
                 title="Faire jaillir les idées.",
                 body="Second Brain, Jarvis, la reconnaissance de gestes : autant "
                      "d'expériences pour donner une intelligence locale et réactive à des "
                      "objets du quotidien."),
            dict(order=5, shape="globe",
                 title="Un métier sans frontières.",
                 body="Mobile, web, jeu vidéo, réseaux : je navigue entre les briques "
                      "techniques pour donner vie à une idée, quel que soit le terrain.",
                 cta_label="Me contacter", cta_href="mailto:nickkakaye4@gmail.com"),
        ]
        for s in stages:
            HeroStage.objects.update_or_create(order=s["order"], defaults=s)

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
