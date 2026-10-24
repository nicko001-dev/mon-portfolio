from django.core.management.base import BaseCommand

from portfolio.models import ChatbotSettings, ChatKnowledge

KNOWLEDGE = [
    ("info", "Recherche de stage",
     "Nick cherche un stage de fin de licence : un stage qui donne lieu à une soutenance "
     "en fin d'année universitaire pour valider sa Licence 3. Il est disponible à partir "
     "de mars et reste flexible sur la durée et les missions. Ce n'est plus un stage "
     "d'immersion : il veut réaliser un projet concret au sein d'une équipe."),
    ("info", "Projet NAYO",
     "NAYO est un jeu mobile Android 2D d'aventure, développé en C# sous Unity, qui fait "
     "découvrir la langue ivoirienne bété à travers des dialogues immersifs (système de "
     "dialogue dynamique avec variables de genre grammatical). Nick ne parle pas le bété : "
     "la langue est le thème du jeu. Il l'a réalisé sans expérience préalable d'Unity."),
    ("info", "Projet Jarvis",
     "Jarvis est un assistant vocal IA qui fonctionne hors-ligne, en Python : reconnaissance "
     "vocale avec Vosk, mémoire persistante, intégration d'Ollama, gestion des entrées voix "
     "et clavier, réponses contextuelles et modules extensibles."),
    ("info", "Application de gestion académique",
     "Application de bureau complète en Java Swing pour les professeurs : gestion des notes, "
     "export PDF et Excel (iText, Apache POI), authentification sécurisée (BCrypt), formules "
     "dynamiques (exp4j) et installateur Windows (jpackage)."),
    ("info", "Projet EcoValor CI",
     "Application mobile Flutter / Firebase de valorisation des déchets industriels en Côte "
     "d'Ivoire : authentification Firebase, routage conditionnel et collections Firestore."),
    ("info", "Contrôle de l'ordinateur par gestes",
     "Projet Python (MediaPipe, PyAutoGUI) : contrôle du curseur par détection des gestes de "
     "la main via la caméra, avec suivi adaptatif du centre de la paume et lissage."),
    ("info", "Ce portfolio",
     "Ce site a été conçu et développé par Nick lui-même : Django pour le contenu et "
     "l'administration, Three.js pour l'univers 3D explorable, et cet assistant IA branché "
     "sur l'API OpenRouter. Tout le contenu est modifiable depuis l'espace admin."),
    ("instruction", "Contact et disponibilité",
     "Quand un visiteur veut recruter Nick, collaborer ou le contacter, donne son e-mail "
     "(nickkakaye4@gmail.com) et rappelle qu'il est disponible à partir de mars pour un "
     "stage de fin de licence."),
]


OLD_DEFAULT_SUGGESTIONS = (
    "Qui est Nick ?\nQuels sont ses projets les plus marquants ?\n"
    "Quelles certifications a-t-il obtenues ?\nEst-il disponible pour un stage ?"
)

class Command(BaseCommand):
    help = "Crée les réglages de l'assistant IA et ses connaissances initiales (sans rien écraser)."

    def handle(self, *args, **options):
        cfg = ChatbotSettings.get()  # crée la fiche si elle n'existe pas
        portfolio_knowledge = ChatKnowledge.objects.filter(title="Ce portfolio").first()
        old_provider_text = "l'API Gemini de Google"
        if portfolio_knowledge and old_provider_text in portfolio_knowledge.content:
            portfolio_knowledge.content = portfolio_knowledge.content.replace(
                old_provider_text, "l'API OpenRouter", 1)
            portfolio_knowledge.save(update_fields=["content"])
            self.stdout.write("Connaissance du portfolio mise à jour : OpenRouter.")

        # Ajoute « Dis-moi tout sur cet univers » aux suggestions, mais uniquement si
        # l'admin n'a jamais modifié la liste (on ne touche pas à ses réglages).
        if cfg.suggestions.strip() == OLD_DEFAULT_SUGGESTIONS:
            cfg.suggestions = ChatbotSettings._meta.get_field("suggestions").default
            cfg.save(update_fields=["suggestions"])
            self.stdout.write("Suggestions mises à jour (ajout de « Dis-moi tout sur cet univers »).")
        if not ChatKnowledge.objects.exists():
            for i, (kind, title, content) in enumerate(KNOWLEDGE, start=1):
                ChatKnowledge.objects.create(order=i, kind=kind, title=title, content=content)
            self.stdout.write(self.style.SUCCESS(f"{len(KNOWLEDGE)} connaissances initiales créées."))
        else:
            self.stdout.write("Connaissances de l'assistant déjà présentes : conservées.")
