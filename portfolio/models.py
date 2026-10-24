from django.db import models
from django.templatetags.static import static


class Profile(models.Model):
    """Fiche unique décrivant Nick — récupérée avec Profile.get()."""
    name = models.CharField("Nom affiché", max_length=120, default="Nick Kakaye")
    role = models.CharField("Métier / statut", max_length=160, default="Étudiant en génie logiciel")
    school = models.CharField("École", max_length=160, default="ESATIC — École Supérieure Africaine des TIC")
    program = models.CharField("Filière", max_length=80, default="Licence 3 SIGL")
    program_year = models.CharField("Année", max_length=40, default="Année 2026-2027")
    location = models.CharField("Ville", max_length=120, default="Abidjan, Côte d'Ivoire")
    email = models.EmailField("Adresse e-mail", default="nickkakaye4@gmail.com")
    bio_p1 = models.TextField("Biographie — 1er paragraphe")
    bio_p2 = models.TextField("Biographie — 2e paragraphe")
    looking_for = models.CharField(
        "Recherche (bas de l'accueil)", max_length=200,
        default="à la recherche d'un stage de fin d'année académique",
    )
    stat_projects = models.PositiveIntegerField("Chiffre — projets (secours)", default=6)
    stat_certifications = models.PositiveIntegerField("Chiffre — certifications (secours)", default=5)
    stat_technologies = models.PositiveIntegerField("Chiffre — technologies (secours)", default=10)
    stat_years = models.PositiveIntegerField("Chiffre — années (secours)", default=3)
    photo_full = models.CharField(
        "Photo — grande (chemin)", max_length=200,
        default="portfolio/img/avatar_full.webp",
    )
    photo_thumb = models.CharField(
        "Photo — vignette (chemin)", max_length=200,
        default="portfolio/img/avatar_thumb.webp",
    )
    quote = models.CharField("Citation", max_length=200, default="Je fabrique pour comprendre.")
    photo = models.ImageField(
        "Photo (téléversement)", upload_to="profile/", blank=True,
        help_text="Optionnel. Si une photo est téléversée ici, elle remplace la photo "
                  "du site (grande et vignette). Format carré ou portrait, moins de 1 Mo.",
    )

    class Meta:
        verbose_name = "Profil (identité, bio, photo)"
        verbose_name_plural = "Profil (identité, bio, photo)"

    @property
    def photo_full_url(self):
        return self.photo.url if self.photo else static(self.photo_full)

    @property
    def photo_thumb_url(self):
        return self.photo.url if self.photo else static(self.photo_thumb)

    def __str__(self):
        return self.name

    @classmethod
    def get(cls):
        return cls.objects.first()


class HeroStage(models.Model):
    """Un état du hero : le nuage de particules prend une forme, le texte change."""
    SHAPE_CHOICES = [
        ("brain", "Cerveau"),
        ("dissolve", "Dispersion (texte de problématique)"),
        ("lightbulb", "Ampoule"),
        ("globe", "Globe"),
    ]
    order = models.PositiveSmallIntegerField("Ordre d'apparition", default=0)
    shape = models.CharField("Forme des particules", max_length=20, choices=SHAPE_CHOICES)
    eyebrow = models.CharField("Sur-titre", max_length=140, blank=True)
    title = models.CharField("Titre", max_length=140, blank=True)
    body = models.TextField("Texte", blank=True)
    cta_label = models.CharField("Bouton (libellé)", max_length=60, blank=True)
    cta_href = models.CharField("Bouton (lien)", max_length=120, blank=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "(ancien) étape du hero — non affiché"
        verbose_name_plural = "(ancien) étapes du hero — non affichées"

    def __str__(self):
        return f"{self.order}. {self.shape} — {self.title or self.eyebrow}"


class ProblemStatement(models.Model):
    """Les phrases qui défilent pendant l'état 'dissolve' du hero."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    text = models.CharField("Phrase affichée", max_length=220)

    class Meta:
        ordering = ["order"]
        verbose_name = "(ancien) phrase qui défile — non affichée"
        verbose_name_plural = "(ancien) phrases qui défilent — non affichées"

    def __str__(self):
        return self.text


class SkillGroup(models.Model):
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    name = models.CharField("Nom du groupe", max_length=80)
    description = models.CharField("Liste des outils", max_length=240)

    class Meta:
        ordering = ["order"]
        verbose_name = "Atelier 03 · Boîte à outils — compétence"
        verbose_name_plural = "Atelier 03 · Boîte à outils (compétences)"

    def __str__(self):
        return self.name


class Project(models.Model):
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    monogram = models.CharField("Monogramme", max_length=3, help_text="1 à 3 lettres, ex. « SB »")
    title = models.CharField("Titre du projet", max_length=100)
    tag = models.CharField("Étiquette", max_length=60, help_text="Étiquette courte, ex. « IA locale »")
    kind = models.CharField("Sous-titre", max_length=120, help_text="Ex. « Application mobile d'IA 100 % locale »")
    description = models.TextField("Description")
    stack = models.CharField("Pile technique", max_length=200, help_text="Séparée par « · »")

    class Meta:
        ordering = ["order"]
        verbose_name = "Atelier 05 · Travaux récents — projet"
        verbose_name_plural = "Atelier 05 · Travaux récents (projets, aussi dans l'Univers 3D)"

    def __str__(self):
        return self.title


class Certification(models.Model):
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    title = models.CharField("Intitulé", max_length=160)
    org = models.CharField("Organisme", max_length=120)
    date = models.CharField("Date d'obtention", max_length=60)
    slug = models.SlugField(
        "Fichier image", max_length=30, blank=True,
        help_text="Doit correspondre au nom de fichier statique, ex. « ds » "
                  "(portfolio/img/certs/ds_full.webp).",
    )

    image = models.ImageField(
        "Image du certificat (téléversement)", upload_to="certs/", blank=True,
        help_text="Optionnel. Remplace l'image du dossier statique (fichier image ci-dessus).",
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Atelier 06 · Reconnaissances — certification"
        verbose_name_plural = "Atelier 06 · Reconnaissances (certifications)"

    def __str__(self):
        return self.title

    @property
    def image_full(self):
        return f"portfolio/img/certs/{self.slug}_full.webp"

    @property
    def image_thumb(self):
        return f"portfolio/img/certs/{self.slug}_thumb.webp"

    @property
    def image_full_url(self):
        return self.image.url if self.image else static(self.image_full)

    @property
    def image_thumb_url(self):
        return self.image.url if self.image else static(self.image_thumb)


class TrainingItem(models.Model):
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    title = models.CharField("Matière", max_length=80)
    description = models.TextField("Ce qui est étudié")

    class Meta:
        ordering = ["order"]
        verbose_name = "Atelier 04 · Diplôme en cours — matière"
        verbose_name_plural = "Atelier 04 · Diplôme en cours (matières)"

    def __str__(self):
        return self.title


class SiteText(models.Model):
    """Un texte fixe du site, modifiable depuis l'admin (titre, libellé, phrase)."""
    GROUP_CHOICES = [
        ("general", "Général"),
        ("accueil", "Accueil"),
        ("univers", "Univers 3D"),
        ("atelier", "Atelier"),
        ("navigation", "Navigation & boutons"),
        ("pied", "Pied de page"),
    ]
    key = models.SlugField(
        "Identifiant", max_length=60, unique=True,
        help_text="Identifiant interne — ne pas modifier.",
    )
    label = models.CharField(
        "Emplacement", max_length=120,
        help_text="Où ce texte apparaît sur le site.",
    )
    value = models.TextField("Texte affiché", help_text="Le texte affiché sur le site.")
    group = models.CharField(
        max_length=20, choices=GROUP_CHOICES, default="accueil",
        verbose_name="Section du site",
        help_text="Où ce texte apparaît — sert à regrouper l'admin.",
    )
    class Meta:
        ordering = ["key"]
        verbose_name = "Libellé & texte du site"
        verbose_name_plural = "Libellés & textes du site"
    def __str__(self):
        return f"{self.label} — {self.value[:40]}"
    @classmethod
    def as_dict(cls):
        return {t.key: t.value for t in cls.objects.all()}
class NavItem(models.Model):
    """Un lien de navigation (en-tête et/ou menu latéral)."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    label = models.CharField("Nom du lien", max_length=60)
    anchor = models.CharField("Cible", max_length=60, help_text="Ancre, ex. « #projects »")
    show_in_nav = models.BooleanField(default=True, verbose_name="Visible dans l'en-tête")
    show_in_drawer = models.BooleanField(default=True, verbose_name="Visible dans le menu")
    class Meta:
        ordering = ["order"]
        verbose_name = "Navigation · lien"
        verbose_name_plural = "Navigation · liens (en-tête et menu)"
    def __str__(self):
        return f"{self.label} ({self.anchor})"
class MarqueeItem(models.Model):
    """Un mot du bandeau défilant."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    text = models.CharField("Mot affiché", max_length=40)
    class Meta:
        ordering = ["order"]
        verbose_name = "Atelier · Bandeau défilant — mot"
        verbose_name_plural = "Atelier · Bandeau défilant (mots)"
    def __str__(self):
        return self.text
class ManifestoStat(models.Model):
    """Un chiffre du manifeste (nombre animé + libellé)."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    value = models.PositiveIntegerField("Chiffre", default=0)
    label = models.CharField("Libellé", max_length=40, help_text="Ex. « Projets menés »")
    class Meta:
        ordering = ["order"]
        verbose_name = "Atelier 01 · L'atelier — chiffre animé"
        verbose_name_plural = "Atelier 01 · L'atelier (chiffres animés)"
    def __str__(self):
        return f"{self.value} — {self.label}"
class FocusItem(models.Model):
    """Une ligne de la section « Ce qui m'anime »."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    title = models.CharField("Titre de la ligne", max_length=120)
    body = models.TextField("Texte de la ligne")
    class Meta:
        ordering = ["order"]
        verbose_name = "Atelier 02 · Ce qui m'anime — ligne"
        verbose_name_plural = "Atelier 02 · Ce qui m'anime (lignes)"
    def __str__(self):
        return self.title
class ContactItem(models.Model):
    """Un bloc de la grille de contact (libellé + valeur)."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    label = models.CharField("Titre du bloc", max_length=40, help_text="Ex. « École », « Où »")
    value = models.TextField(
        "Contenu", 
        help_text="Texte affiché ; une adresse « mailto:… » devient un lien, "
                  "un « #ancre » devient un lien interne.",
    )
    copyable = models.BooleanField(
        default=False, verbose_name="Bouton « copier »",
        help_text="Ajoute un bouton pour copier la valeur (utile pour l'e-mail).",
    )
    class Meta:
        ordering = ["order"]
        verbose_name = "Atelier 07 · Contact — bloc"
        verbose_name_plural = "Atelier 07 · Contact (blocs)"
    def __str__(self):
        return f"{self.label} — {self.value[:30]}"
    @property
    def is_mail(self):
        return self.value.strip().lower().startswith("mailto:")

    @property
    def is_anchor(self):
        return self.value.strip().startswith("#")
    @property
    def href(self):
        v = self.value.strip()
        return v if (v.startswith("mailto:") or v.startswith("#") or v.startswith("http")) else f"mailto:{v}"


class UniverseBody(models.Model):
    """Textes d'un astre de l'univers 3D (le soleil, une planète, le trou noir…).

    Les formes, couleurs et positions restent dans le code 3D : seuls les textes
    sont éditables. ``key`` désigne l'emplacement dans la scène (non modifiable).
    """
    key = models.SlugField("Emplacement dans la scène", max_length=20, unique=True)
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    name = models.CharField(
        "Nom de l'astre", max_length=60,
        help_text="Affiché en 3D au-dessus de l'astre, dans la carte de transmission, "
                  "dans le message « DÉCOUVERTE » et dans la ligne « CIBLE ».",
    )
    subtitle = models.CharField(
        "Sous-titre", max_length=80, blank=True,
        help_text="Affiché sous le nom (en 3D et dans la carte de transmission).",
    )
    info = models.TextField(
        "Transmission (texte affiché en s'approchant)", blank=True,
        help_text="Texte de la carte « TRANSMISSION STELLAIRE » qui s'ouvre quand on s'approche "
                  "de l'astre. Laisse vide pour les astres sans transmission (trou noir, galaxie…).",
    )

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Univers 3D · astre"
        verbose_name_plural = "Univers 3D · astres (soleil, planètes, trou noir…)"

    def __str__(self):
        return f"{self.name} ({self.key})"


# ════════════════════════════════════════════════════════════════════════
#  Textes du site, rangés par partie (un « proxy » par section de l'admin)
# ════════════════════════════════════════════════════════════════════════
class SiteTextGeneral(SiteText):
    class Meta:
        proxy = True
        verbose_name = "Général · réglage"
        verbose_name_plural = "Général · onglet, description, vidéo d'accueil"


class SiteTextAccueil(SiteText):
    class Meta:
        proxy = True
        verbose_name = "Accueil · texte"
        verbose_name_plural = "Accueil (vidéo) · textes et boutons"


class SiteTextUnivers(SiteText):
    class Meta:
        proxy = True
        verbose_name = "Univers 3D · texte"
        verbose_name_plural = "Univers 3D · textes, commandes et messages"


class SiteTextAtelier(SiteText):
    class Meta:
        proxy = True
        verbose_name = "Atelier · texte"
        verbose_name_plural = "Atelier · titres des sections et boutons"


class SiteTextNavigation(SiteText):
    class Meta:
        proxy = True
        verbose_name = "Navigation · texte"
        verbose_name_plural = "Navigation · textes du menu"


class SiteTextPied(SiteText):
    class Meta:
        proxy = True
        verbose_name = "Pied de page · texte"
        verbose_name_plural = "Pied de page · textes"


# ════════════════════════════════════════════════════════════════════════
#  Assistant IA (chatbot OpenRouter)
# ════════════════════════════════════════════════════════════════════════
DEFAULT_INSTRUCTIONS = (
    "Ton : chaleureux, professionnel et enthousiaste, jamais arrogant.\n"
    "Quand on te parle de Nick, mets en avant ses points forts avec des faits précis : "
    "projets menés de bout en bout, apprentissage par la pratique, IA locale, "
    "certifications Cisco, rigueur, autonomie.\n"
    "Quand un recruteur ou un enseignant s'intéresse à lui, invite-le à le contacter "
    "par e-mail et rappelle sa recherche de stage."
)


class ChatbotSettings(models.Model):
    """Réglages uniques de l'assistant IA — récupérés avec ChatbotSettings.get()."""
    enabled = models.BooleanField(
        "Assistant activé", default=True,
        help_text="Décoche pour retirer la bulle de chat du site sans rien supprimer.",
    )
    assistant_name = models.CharField("Nom de l'assistant", max_length=60, default="Assistant de Nick")
    header_subtitle = models.CharField(
        "Sous-titre de l'en-tête du chat", max_length=80,
        default="Assistant IA · réponses générées automatiquement", blank=True,
    )
    welcome_message = models.TextField(
        "Message d'accueil",
        default="Bonjour ! Je suis l'assistant IA de Nick Kakaye. Posez-moi vos questions "
                "sur son parcours, ses projets ou ses compétences — ou sur n'importe quel autre sujet.",
    )
    placeholder = models.CharField("Texte du champ de saisie", max_length=80, default="Écrivez votre message…")
    suggestions = models.TextField(
        "Questions suggérées", blank=True,
        default="Dis-moi tout sur cet univers\nQui est Nick ?\nQuels sont ses projets les plus marquants ?\n"
                "Est-il disponible pour un stage ?",
        help_text="Une question par ligne. Elles s'affichent comme boutons au début de la conversation.",
    )
    universe_suggestions = models.TextField(
        "Questions suggérées dans l'univers 3D", blank=True,
        default="Dis-moi tout sur cet univers\nComment me déplacer ?\nOù est le trou noir ?\n"
                "Je suis perdu, aide-moi !",
        help_text="Une question par ligne. Dans l'univers 3D, elles restent affichées en permanence "
                  "au-dessus du champ de saisie, car c'est là qu'on se perd le plus facilement.",
    )
    universe_alert_text = models.CharField(
        "Bulle d'alerte dans l'univers 3D", max_length=60, default="Perdu ? Demandez-moi !",
        blank=True,
        help_text="Texte qui clignote à côté du bouton de l'assistant dans l'univers 3D, "
                  "tant que le visiteur ne l'a pas ouvert. Laisse vide pour ne garder que l'animation.",
    )
    instructions = models.TextField(
        "Instructions pour l'IA", default=DEFAULT_INSTRUCTIONS, blank=True,
        help_text="Ton, priorités, façon de présenter Nick, règles particulières… "
                  "Écris ici tout ce que tu veux dire à l'IA (comme un brief). "
                  "Pour ajouter des informations sur toi, utilise plutôt « Connaissances de l'IA ».",
    )
    model_name = models.CharField(
        "Modèle OpenRouter gratuit", max_length=80, blank=True, default="",
        help_text="Laisse vide pour un choix automatique (recommandé). Sinon indique "
                  "l'identifiant exact d'un modèle OpenRouter gratuit (suffixe :free).",
    )
    temperature = models.FloatField(
        "Créativité (0 à 1)", default=0.7,
        help_text="0 = très factuel, 1 = très créatif. 0,7 est un bon équilibre.",
    )
    max_output_tokens = models.PositiveIntegerField(
        "Longueur maximale des réponses", default=1500,
        help_text="En « tokens » (≈ ¾ de mot). 1500 laisse de la place au raisonnement du modèle.",
    )
    max_message_chars = models.PositiveIntegerField("Longueur maximale d'un message visiteur", default=600)
    history_messages = models.PositiveSmallIntegerField(
        "Messages d'historique envoyés à l'IA", default=10,
        help_text="Combien de messages précédents l'IA relit pour garder le fil.",
    )
    hourly_limit_per_visitor = models.PositiveIntegerField(
        "Messages par visiteur et par heure", default=15,
    )
    daily_limit_global = models.PositiveIntegerField(
        "Messages par jour (tous visiteurs)", default=400,
        help_text="Plafond de sécurité pour préserver les quotas gratuits OpenRouter.",
    )
    log_conversations = models.BooleanField(
        "Enregistrer les conversations", default=True,
        help_text="Permet de relire ce que les visiteurs demandent (menu « Conversations »). "
                  "Si décoché, seul le compteur anti-abus est conservé.",
    )
    unavailable_message = models.CharField(
        "Message si l'IA est indisponible", max_length=240,
        default="L'assistant est momentanément indisponible. Vous pouvez écrire directement à Nick par e-mail.",
    )

    class Meta:
        verbose_name = "Assistant IA · réglages et instructions"
        verbose_name_plural = "Assistant IA · réglages et instructions"

    def __str__(self):
        return "Réglages de l'assistant IA"

    @classmethod
    def get(cls):
        obj = cls.objects.first()
        return obj or cls.objects.create()

    @staticmethod
    def _lines(text, limit=6):
        return [l.strip() for l in text.splitlines() if l.strip()][:limit]

    def suggestion_list(self):
        return self._lines(self.suggestions)

    def universe_suggestion_list(self):
        return self._lines(self.universe_suggestions)


class ChatKnowledge(models.Model):
    """Une information (ou une consigne) donnée à l'IA depuis l'admin."""
    KIND_CHOICES = [
        ("info", "Information sur Nick"),
        ("instruction", "Consigne de comportement"),
    ]
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    title = models.CharField("Titre (pour t'y retrouver)", max_length=120)
    kind = models.CharField("Type", max_length=12, choices=KIND_CHOICES, default="info")
    content = models.TextField(
        "Contenu",
        help_text="Écris-le comme tu le dirais à quelqu'un : l'IA le lit tel quel.",
    )
    active = models.BooleanField("Actif", default=True, help_text="Décoche pour désactiver sans supprimer.")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Assistant IA · connaissance"
        verbose_name_plural = "Assistant IA · connaissances et consignes"

    def __str__(self):
        return self.title


class ChatLog(models.Model):
    """Trace d'un échange (et compteur anti-abus)."""
    created_at = models.DateTimeField("Date", auto_now_add=True, db_index=True)
    visitor = models.CharField("Visiteur (empreinte)", max_length=16, db_index=True)
    question = models.TextField("Question", blank=True)
    answer = models.TextField("Réponse", blank=True)
    ok = models.BooleanField("Réponse obtenue", default=True)
    error = models.CharField("Erreur", max_length=200, blank=True)
    model_used = models.CharField("Modèle", max_length=80, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assistant IA · conversation"
        verbose_name_plural = "Assistant IA · conversations (lecture seule)"

    def __str__(self):
        return f"{self.created_at:%d/%m %H:%M} — {self.question[:50]}"
