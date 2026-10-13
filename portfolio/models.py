from django.db import models


class Profile(models.Model):
    """Fiche unique décrivant Nick — récupérée avec Profile.get()."""
    name = models.CharField(max_length=120, default="Nick Kakaye")
    role = models.CharField(max_length=160, default="Étudiant en génie logiciel")
    school = models.CharField(max_length=160, default="ESATIC — École Supérieure Africaine des TIC")
    program = models.CharField(max_length=80, default="Licence 3 SIGL")
    program_year = models.CharField(max_length=40, default="Année 2026-2027")
    location = models.CharField(max_length=120, default="Abidjan, Côte d'Ivoire")
    email = models.EmailField(default="nickkakaye4@gmail.com")
    bio_p1 = models.TextField()
    bio_p2 = models.TextField()
    looking_for = models.CharField(
        max_length=200, default="à la recherche d'un stage de fin d'année académique"
    )
    stat_projects = models.PositiveIntegerField(default=6)
    stat_certifications = models.PositiveIntegerField(default=5)
    stat_technologies = models.PositiveIntegerField(default=10)
    stat_years = models.PositiveIntegerField(default=3)
    photo_full = models.CharField(max_length=200, default="portfolio/img/avatar_full.webp")
    photo_thumb = models.CharField(max_length=200, default="portfolio/img/avatar_thumb.webp")
    quote = models.CharField(max_length=200, default="Je fabrique pour comprendre.")

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profil"

    def __str__(self):
        return self.name

    @classmethod
    def get(cls):
        return cls.objects.first()


class HeroStage(models.Model):
    """Un état du morph du hero (le nuage de particules prend une forme, le texte change)."""
    SHAPE_CHOICES = [
        ("brain", "Cerveau"),
        ("dissolve", "Dispersion (texte de problématique)"),
        ("lightbulb", "Ampoule"),
        ("globe", "Globe"),
    ]
    order = models.PositiveSmallIntegerField(default=0)
    shape = models.CharField(max_length=20, choices=SHAPE_CHOICES)
    eyebrow = models.CharField(max_length=140, blank=True)
    title = models.CharField(max_length=140, blank=True)
    body = models.TextField(blank=True)
    cta_label = models.CharField(max_length=60, blank=True)
    cta_href = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Étape du hero"
        verbose_name_plural = "Étapes du hero"

    def __str__(self):
        return f"{self.order}. {self.shape} — {self.title or self.eyebrow}"


class ProblemStatement(models.Model):
    """Les phrases qui défilent pendant l'état 'dissolve' du hero."""
    order = models.PositiveSmallIntegerField(default=0)
    text = models.CharField(max_length=220)

    class Meta:
        ordering = ["order"]
        verbose_name = "Phrase (dispersion)"
        verbose_name_plural = "Phrases (dispersion)"

    def __str__(self):
        return self.text


class SkillGroup(models.Model):
    order = models.PositiveSmallIntegerField(default=0)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=240)

    class Meta:
        ordering = ["order"]
        verbose_name = "Groupe de compétences"
        verbose_name_plural = "Groupes de compétences"

    def __str__(self):
        return self.name


class Project(models.Model):
    order = models.PositiveSmallIntegerField(default=0)
    monogram = models.CharField(max_length=3, help_text="1 à 3 lettres, ex. « SB »")
    title = models.CharField(max_length=100)
    tag = models.CharField(max_length=60, help_text="Étiquette courte, ex. « IA locale »")
    kind = models.CharField(max_length=120, help_text="Sous-titre, ex. « Application mobile d'IA 100 % locale »")
    description = models.TextField()
    stack = models.CharField(max_length=200, help_text="Séparée par « · »")

    class Meta:
        ordering = ["order"]
        verbose_name = "Projet"
        verbose_name_plural = "Projets"

    def __str__(self):
        return self.title


class Certification(models.Model):
    order = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=160)
    org = models.CharField(max_length=120)
    date = models.CharField(max_length=60)
    slug = models.SlugField(max_length=30, help_text="Doit correspondre au nom de fichier statique, ex. « ds »")

    class Meta:
        ordering = ["order"]
        verbose_name = "Certification"
        verbose_name_plural = "Certifications"

    def __str__(self):
        return self.title

    @property
    def image_full(self):
        return f"portfolio/img/certs/{self.slug}_full.webp"

    @property
    def image_thumb(self):
        return f"portfolio/img/certs/{self.slug}_thumb.webp"


class TrainingItem(models.Model):
    order = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=80)
    description = models.TextField()

    class Meta:
        ordering = ["order"]
        verbose_name = "Point de formation"
        verbose_name_plural = "Points de formation"

    def __str__(self):
        return self.title
