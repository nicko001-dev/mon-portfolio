from django.db import models


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

    class Meta:
        verbose_name = "1 · Profil & accueil"
        verbose_name_plural = "1 · Profil & accueil"

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
        verbose_name = "2 · Accueil — étape du hero"
        verbose_name_plural = "2 · Accueil — étapes du hero"

    def __str__(self):
        return f"{self.order}. {self.shape} — {self.title or self.eyebrow}"


class ProblemStatement(models.Model):
    """Les phrases qui défilent pendant l'état 'dissolve' du hero."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    text = models.CharField("Phrase affichée", max_length=220)

    class Meta:
        ordering = ["order"]
        verbose_name = "3 · Accueil — phrase qui défile"
        verbose_name_plural = "3 · Accueil — phrases qui défilent"

    def __str__(self):
        return self.text


class SkillGroup(models.Model):
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    name = models.CharField("Nom du groupe", max_length=80)
    description = models.CharField("Liste des outils", max_length=240)

    class Meta:
        ordering = ["order"]
        verbose_name = "4 · Atelier — compétence"
        verbose_name_plural = "4 · Atelier — Compétences"

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
        verbose_name = "5 · Atelier — projet"
        verbose_name_plural = "5 · Atelier — Travaux récents"

    def __str__(self):
        return self.title


class Certification(models.Model):
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    title = models.CharField("Intitulé", max_length=160)
    org = models.CharField("Organisme", max_length=120)
    date = models.CharField("Date d'obtention", max_length=60)
    slug = models.SlugField(
        "Fichier image", max_length=30,
        help_text="Doit correspondre au nom de fichier statique, ex. « ds » "
                  "(portfolio/img/certs/ds_full.webp).",
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "6 · Atelier — certification"
        verbose_name_plural = "6 · Atelier — Reconnaissances"

    def __str__(self):
        return self.title

    @property
    def image_full(self):
        return f"portfolio/img/certs/{self.slug}_full.webp"

    @property
    def image_thumb(self):
        return f"portfolio/img/certs/{self.slug}_thumb.webp"


class TrainingItem(models.Model):
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    title = models.CharField("Matière", max_length=80)
    description = models.TextField("Ce qui est étudié")

    class Meta:
        ordering = ["order"]
        verbose_name = "7 · Atelier — formation"
        verbose_name_plural = "7 · Atelier — Formation (matière)"

    def __str__(self):
        return self.title


class SiteText(models.Model):
    """Un texte fixe du site, modifiable depuis l'admin (titre, libellé, phrase)."""
    GROUP_CHOICES = [
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
        verbose_name = "Navigation — lien"
        verbose_name_plural = "Navigation — liens"
    def __str__(self):
        return f"{self.label} ({self.anchor})"
class MarqueeItem(models.Model):
    """Un mot du bandeau défilant."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    text = models.CharField("Mot affiché", max_length=40)
    class Meta:
        ordering = ["order"]
        verbose_name = "8 · Atelier — mot du bandeau"
        verbose_name_plural = "8 · Atelier — bandeau défilant"
    def __str__(self):
        return self.text
class ManifestoStat(models.Model):
    """Un chiffre du manifeste (nombre animé + libellé)."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    value = models.PositiveIntegerField("Chiffre", default=0)
    label = models.CharField("Libellé", max_length=40, help_text="Ex. « Projets menés »")
    class Meta:
        ordering = ["order"]
        verbose_name = "9 · Atelier — chiffre animé"
        verbose_name_plural = "9 · Atelier — chiffres animés"
    def __str__(self):
        return f"{self.value} — {self.label}"
class FocusItem(models.Model):
    """Une ligne de la section « Ce qui m'anime »."""
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    title = models.CharField("Titre de la ligne", max_length=120)
    body = models.TextField("Texte de la ligne")
    class Meta:
        ordering = ["order"]
        verbose_name = "10 · Atelier — « Ce qui m'anime »"
        verbose_name_plural = "10 · Atelier — « Ce qui m'anime »"
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
        verbose_name = "11 · Atelier — bloc de contact"
        verbose_name_plural = "11 · Atelier — Contact"
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
