from django.contrib import admin

from .models import (
    Profile, HeroStage, ProblemStatement, SkillGroup,
    Project, Certification, TrainingItem,
    SiteText, NavItem, MarqueeItem, ManifestoStat, FocusItem, ContactItem,
)

admin.site.site_header = "Administration — Portfolio de Nick"
admin.site.site_title = "Portfolio de Nick"
admin.site.index_title = "Contenu du site"


def site_order(model):
    """Ordre d'affichage des contenus dans l'admin, calqué sur l'ordre réel
    du site : accueil (vidéo) → univers 3D → atelier → navigation."""
    order = [
        "Profile", "HeroStage", "ProblemStatement",
        "SiteText",
        "SkillGroup", "Project", "Certification", "TrainingItem",
        "MarqueeItem", "ManifestoStat", "FocusItem", "ContactItem",
        "NavItem",
    ]
    name = model.__name__
    return (order.index(name), name) if name in order else (len(order), name)


_default_get_app_list = admin.AdminSite.get_app_list


def ordered_get_app_list(self, request, app_label=None):
    app_list = _default_get_app_list(self, request, app_label)
    for app in app_list:
        if app.get("app_label") == "portfolio":
            app["models"].sort(key=lambda m: site_order(m["model"]))
    return app_list


admin.AdminSite.get_app_list = ordered_get_app_list


class SingletonAdmin(admin.ModelAdmin):
    """Contenu unique : on modifie la ligne, on ne la supprime pas."""

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(SingletonAdmin):
    list_display = ("name", "role", "email", "school")
    fieldsets = (
        ("Identité (accueil et en-tête)", {
            "fields": ("name", "role", "email", "location"),
        }),
        ("Études (atelier — Formation)", {
            "fields": ("school", "program", "program_year"),
        }),
        ("Textes", {
            "fields": ("bio_p1", "bio_p2", "looking_for", "quote"),
        }),
        ("Photo et vignette", {
            "fields": ("photo_full", "photo_thumb"),
            "description": "Chemins relatifs aux fichiers statiques "
                           "(portfolio/img/…). Remplacer les fichiers dans "
                           "portfolio/static/portfolio/img/ pour changer la photo.",
        }),
        ("Chiffres de secours", {
            "fields": ("stat_projects", "stat_certifications",
                       "stat_technologies", "stat_years"),
            "description": "Utilisés seulement si « 9 · Atelier — chiffres animés » "
                           "est vide.",
        }),
    )

    def has_add_permission(self, request):
        # Fiche unique : on évite d'en créer une deuxième par erreur.
        return not Profile.objects.exists()


@admin.register(HeroStage)
class HeroStageAdmin(admin.ModelAdmin):
    list_display = ("order", "shape", "title", "eyebrow")
    list_editable = ("order",)
    list_display_links = ("shape",)
    ordering = ("order",)
    fieldsets = (
        ("Placement", {
            "fields": ("order", "shape"),
            "description": "L'ordre d'apparition et la forme que prennent "
                           "les particules à cette étape.",
        }),
        ("Texte affiché", {"fields": ("eyebrow", "title", "body")}),
        ("Bouton (optionnel)", {"fields": ("cta_label", "cta_href")}),
    )


@admin.register(ProblemStatement)
class ProblemStatementAdmin(admin.ModelAdmin):
    list_display = ("order", "text")
    list_editable = ("order",)
    list_display_links = ("text",)
    ordering = ("order",)
    fieldsets = (
        ("Phrase", {
            "fields": ("order", "text"),
            "description": "Ces phrases défilent pendant l'étape « dispersion ».",
        }),
    )


@admin.register(SkillGroup)
class SkillGroupAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "description")
    list_editable = ("order",)
    list_display_links = ("name",)
    ordering = ("order",)
    search_fields = ("name", "description")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "tag", "kind")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order",)
    search_fields = ("title", "tag", "kind", "stack", "description")


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "org", "date", "slug")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order",)
    search_fields = ("title", "org", "date", "slug")
    fieldsets = (
        ("Certificat", {"fields": ("order", "title", "org", "date")}),
        ("Image", {
            "fields": ("slug",),
            "description": "Le « fichier image » doit correspondre à deux "
                           "fichiers dans portfolio/static/portfolio/img/certs/ : "
                           "<identifiant>_full.webp et <identifiant>_thumb.webp.",
        }),
    )


@admin.register(TrainingItem)
class TrainingItemAdmin(admin.ModelAdmin):
    list_display = ("order", "title")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order",)
    search_fields = ("title", "description")


@admin.register(SiteText)
class SiteTextAdmin(SingletonAdmin):
    list_display = ("label", "group", "key", "value")
    list_editable = ("value",)
    list_filter = ("group",)
    search_fields = ("label", "key", "value")
    ordering = ("key",)
    readonly_fields = ("key",)
    fieldsets = (
        ("Emplacement", {
            "fields": ("group", "label", "key"),
            "description": "Le groupe indique la partie du site : Accueil "
                           "(vidéo), Univers 3D, Atelier, Navigation ou Pied de page.",
        }),
        ("Texte affiché", {"fields": ("value",)}),
    )


@admin.register(NavItem)
class NavItemAdmin(admin.ModelAdmin):
    list_display = ("order", "label", "anchor", "show_in_nav", "show_in_drawer")
    list_editable = ("order", "show_in_nav", "show_in_drawer")
    list_display_links = ("label",)
    ordering = ("order",)
    fieldsets = (
        ("Lien", {
            "fields": ("order", "label", "anchor"),
            "description": "« Cible » doit être une ancre existante du site, "
                           "ex. #projects, #skills, #certs, #cta, #home.",
        }),
        ("Où il apparaît", {"fields": ("show_in_nav", "show_in_drawer")}),
    )


@admin.register(MarqueeItem)
class MarqueeItemAdmin(admin.ModelAdmin):
    list_display = ("order", "text")
    list_editable = ("order", "text")
    list_display_links = None
    ordering = ("order",)
    fieldsets = (
        ("Bandeau", {
            "fields": ("order", "text"),
            "description": "Les mots défilent en tête de l'atelier, juste "
                           "après le franchissement du trou noir.",
        }),
    )


@admin.register(ManifestoStat)
class ManifestoStatAdmin(admin.ModelAdmin):
    list_display = ("order", "value", "label")
    list_editable = ("order", "value", "label")
    list_display_links = None
    ordering = ("order",)
    fieldsets = (
        ("Chiffre animé", {
            "fields": ("order", "value", "label"),
            "description": "Le nombre s'anime à l'entrée dans l'atelier. "
                           "Sert aussi aux nombres du manifeste.",
        }),
    )


@admin.register(FocusItem)
class FocusItemAdmin(admin.ModelAdmin):
    list_display = ("order", "title")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order",)
    search_fields = ("title", "body")
    fieldsets = (
        ("Ligne", {
            "fields": ("order", "title", "body"),
            "description": "Section « Ce qui m'anime », juste après le manifeste.",
        }),
    )


@admin.register(ContactItem)
class ContactItemAdmin(admin.ModelAdmin):
    list_display = ("order", "label", "value", "copyable")
    list_editable = ("order", "label", "value", "copyable")
    list_display_links = None
    ordering = ("order",)
    fieldsets = (
        ("Bloc de contact", {
            "fields": ("order", "label", "value", "copyable"),
            "description": "Dernière section de l'atelier. Une adresse e-mail "
                           "devient un lien « mailto: » ; un « #ancre » devient "
                           "un lien interne.",
        }),
    )
