from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from . import chatbot
from .models import (
    Profile, SkillGroup, Project, Certification, TrainingItem,
    NavItem, MarqueeItem, ManifestoStat, FocusItem, ContactItem,
    SiteTextGeneral, SiteTextAccueil, SiteTextUnivers, SiteTextAtelier,
    SiteTextNavigation, SiteTextPied,
    ChatbotSettings, ChatKnowledge, ChatLog, UniverseBody,
)

admin.site.site_header = "Administration — Portfolio de Nick"
admin.site.site_title = "Portfolio de Nick"
admin.site.index_title = "Modifier le site — les blocs suivent l'ordre de la page"


# ════════════════════════════════════════════════════════════════════════
#  Page d'accueil de l'admin : mêmes parties, même ordre que le site
# ════════════════════════════════════════════════════════════════════════
SECTIONS = [
    ("① Général — valable pour tout le site",
     ["Profile", "SiteTextGeneral"]),
    ("② Écran 1 · Accueil (vidéo d'introduction)",
     ["SiteTextAccueil"]),
    ("③ Écran 2 · Univers 3D (vol spatial)",
     ["UniverseBody", "SiteTextUnivers"]),
    ("④ Écran 3 · Atelier — de haut en bas de la page",
     ["MarqueeItem", "SiteTextAtelier", "ManifestoStat", "FocusItem", "SkillGroup",
      "TrainingItem", "Project", "Certification", "ContactItem"]),
    ("⑤ Navigation (en-tête, menu) et pied de page",
     ["NavItem", "SiteTextNavigation", "SiteTextPied"]),
    ("⑥ Assistant IA (chatbot)",
     ["ChatbotSettings", "ChatKnowledge", "ChatLog"]),
]

_default_get_app_list = admin.AdminSite.get_app_list


def sectioned_get_app_list(self, request, app_label=None):
    app_list = _default_get_app_list(self, request, app_label)
    if app_label is not None:
        return app_list
    result, others = [], []
    for app in app_list:
        if app.get("app_label") != "portfolio":
            others.append(app)
            continue
        by_name = {m["object_name"]: m for m in app["models"]}
        for i, (title, names) in enumerate(SECTIONS, start=1):
            models_ = [by_name[n] for n in names if n in by_name]
            if models_:
                result.append({**app, "name": title, "app_label": f"portfolio_s{i}", "models": models_})
    return result + others


admin.AdminSite.get_app_list = sectioned_get_app_list


# ════════════════════════════════════════════════════════════════════════
#  Contenus à fiche unique
# ════════════════════════════════════════════════════════════════════════
class SingletonAdmin(admin.ModelAdmin):
    """Contenu unique : on modifie la ligne, on ne la supprime pas."""

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(SingletonAdmin):
    list_display = ("name", "role", "email", "school")
    fieldsets = (
        ("Identité — Accueil (grand titre), en-tête, contact", {
            "fields": ("name", "role", "email", "location"),
        }),
        ("Études — Atelier 04 « Diplôme en cours » et bloc Contact", {
            "fields": ("school", "program", "program_year"),
        }),
        ("Textes — bio (Atelier 01), recherche de stage (Accueil + Contact), citation", {
            "fields": ("bio_p1", "bio_p2", "looking_for", "quote"),
        }),
        ("Photo (en-tête et visionneuse)", {
            "fields": ("photo", "photo_full", "photo_thumb"),
            "description": "Le plus simple : téléverse une image dans « Photo ». "
                           "Sans téléversement, le site utilise les chemins ci-dessous "
                           "(fichiers de portfolio/static/portfolio/img/).",
        }),
        ("Chiffres de secours", {
            "classes": ("collapse",),
            "fields": ("stat_projects", "stat_certifications",
                       "stat_technologies", "stat_years"),
            "description": "Utilisés seulement si « Atelier 01 · L'atelier (chiffres animés) » "
                           "est vide.",
        }),
    )

    def has_add_permission(self, request):
        return not Profile.objects.exists()


# ════════════════════════════════════════════════════════════════════════
#  Textes du site : une entrée d'admin par partie de la page
# ════════════════════════════════════════════════════════════════════════
class SiteTextSectionAdmin(admin.ModelAdmin):
    """Liste filtrée sur un groupe ; on modifie directement les textes dans la liste."""
    group = None
    list_display = ("label", "value")
    list_editable = ("value",)
    search_fields = ("label", "value")
    ordering = ("label",)
    readonly_fields = ("key",)
    list_per_page = 100
    fieldsets = (
        ("Emplacement", {"fields": ("label", "key")}),
        ("Texte affiché", {"fields": ("value",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(group=self.group)

    def has_add_permission(self, request):
        return False  # chaque texte correspond à un emplacement précis du site

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteTextGeneral)
class SiteTextGeneralAdmin(SiteTextSectionAdmin):
    group = "general"


@admin.register(SiteTextAccueil)
class SiteTextAccueilAdmin(SiteTextSectionAdmin):
    group = "accueil"


@admin.register(SiteTextUnivers)
class SiteTextUniversAdmin(SiteTextSectionAdmin):
    group = "univers"


@admin.register(UniverseBody)
class UniverseBodyAdmin(admin.ModelAdmin):
    """Textes des astres : la scène 3D a un nombre fixe d'emplacements."""
    list_display = ("order", "name", "subtitle", "has_transmission", "key")
    list_display_links = ("name",)
    ordering = ("order",)
    readonly_fields = ("key",)
    search_fields = ("name", "subtitle", "info")
    fieldsets = (
        ("Emplacement", {
            "fields": ("key",),
            "description": "Chaque ligne correspond à un astre de la scène 3D (soleil, planètes, "
                           "trou noir, lieux à découvrir). Leur forme et leur position sont fixées "
                           "par le code ; ici tu modifies leurs textes. Les projets, eux, sont les "
                           "planètes de « Atelier 05 · Travaux récents ».",
        }),
        ("Textes", {"fields": ("name", "subtitle", "info")}),
    )

    @admin.display(description="Transmission", boolean=True)
    def has_transmission(self, obj):
        return bool(obj.info.strip())

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteTextAtelier)
class SiteTextAtelierAdmin(SiteTextSectionAdmin):
    group = "atelier"


@admin.register(SiteTextNavigation)
class SiteTextNavigationAdmin(SiteTextSectionAdmin):
    group = "navigation"


@admin.register(SiteTextPied)
class SiteTextPiedAdmin(SiteTextSectionAdmin):
    group = "pied"


# ════════════════════════════════════════════════════════════════════════
#  Atelier (écran 3) — dans l'ordre de la page
# ════════════════════════════════════════════════════════════════════════
@admin.register(MarqueeItem)
class MarqueeItemAdmin(admin.ModelAdmin):
    list_display = ("order", "text")
    list_editable = ("order", "text")
    list_display_links = None
    ordering = ("order",)
    fieldsets = (
        ("Bandeau", {
            "fields": ("order", "text"),
            "description": "Les mots défilent tout en haut de l'atelier, juste "
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
            "description": "Section « 01 / L'atelier » : le nombre s'anime à l'arrivée.",
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
            "description": "Section « 02 / Ce qui m'anime », juste après le manifeste.",
        }),
    )


@admin.register(SkillGroup)
class SkillGroupAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "description")
    list_editable = ("order",)
    list_display_links = ("name",)
    ordering = ("order",)
    search_fields = ("name", "description")


@admin.register(TrainingItem)
class TrainingItemAdmin(admin.ModelAdmin):
    list_display = ("order", "title")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order",)
    search_fields = ("title", "description")


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
        ("Image du certificat", {
            "fields": ("image", "slug"),
            "description": "Téléverse l'image dans « Image du certificat ». Sans "
                           "téléversement, « Fichier image » doit correspondre à deux "
                           "fichiers de portfolio/static/portfolio/img/certs/ : "
                           "<identifiant>_full.webp et <identifiant>_thumb.webp.",
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
            "description": "Section « 07 / Contact ». Une adresse e-mail devient un "
                           "lien « mailto: » ; un « #ancre » devient un lien interne.",
        }),
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
            "description": "« Cible » doit être une ancre existante du site : "
                           "#home, #skills, #training, #projects, #certs ou #cta.",
        }),
        ("Où il apparaît", {"fields": ("show_in_nav", "show_in_drawer")}),
    )


# ════════════════════════════════════════════════════════════════════════
#  Assistant IA
# ════════════════════════════════════════════════════════════════════════
@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(SingletonAdmin):
    list_display = ("__str__", "enabled", "assistant_name")
    readonly_fields = ("key_status", "diagnostic_link", "prompt_preview")
    fieldsets = (
        ("État", {
            "fields": ("enabled", "key_status", "diagnostic_link"),
            "description": "Les clés API ne se saisissent pas ici : elles sont lues dans les "
                           "variables OPENROUTER_API_KEY et GROQ_API_KEY (voir le README).",
        }),
        ("Instructions pour l'IA — c'est ici que tu la diriges", {
            "fields": ("instructions",),
            "description": "Pour lui donner de NOUVELLES INFORMATIONS sur toi, ajoute des "
                           "entrées dans « Assistant IA · connaissances et consignes ». "
                           "Le contenu du site (projets, compétences, certifications…) "
                           "est déjà transmis automatiquement à l'IA.",
        }),
        ("Apparence du chat", {
            "fields": ("assistant_name", "header_subtitle", "welcome_message", "placeholder", "suggestions",
                       "universe_suggestions", "universe_alert_text"),
        }),
        ("Modèle, limites et confidentialité", {
            "classes": ("collapse",),
            "fields": ("model_name", "temperature", "max_output_tokens",
                       "max_message_chars", "history_messages",
                       "hourly_limit_per_visitor", "daily_limit_global",
                       "log_conversations", "unavailable_message"),
        }),
        ("Ce que l'IA lit exactement (aperçu en lecture seule)", {
            "classes": ("collapse",),
            "fields": ("prompt_preview",),
            "description": "Voici le texte complet envoyé au modèle avant chaque conversation : "
                           "règles, tes instructions, la fiche issue du site et tes connaissances.",
        }),
    )

    def has_add_permission(self, request):
        return not ChatbotSettings.objects.exists()

    def changelist_view(self, request, extra_context=None):
        # Fiche unique : on va directement au formulaire.
        obj = ChatbotSettings.get()
        return HttpResponseRedirect(
            reverse("admin:portfolio_chatbotsettings_change", args=[obj.pk]))

    @admin.display(description="Clés API des fournisseurs")
    def key_status(self, obj):
        configured = [
            name for name, key in (
                ("OpenRouter", settings.OPENROUTER_API_KEY),
                ("Groq", settings.GROQ_API_KEY),
            ) if key
        ]
        if configured:
            return mark_safe(
                '<b style="color:#2e7d32">✔ Clé(s) détectée(s) : '
                + ", ".join(configured) + "</b>"
            )
        return mark_safe(
            '<b style="color:#c62828">✘ Aucune clé : définis OPENROUTER_API_KEY ou '
            'GROQ_API_KEY sur ton hébergeur (voir README).</b>')

    @admin.display(description="Test de connexion")
    def diagnostic_link(self, obj):
        return format_html(
            '<a class="button" href="{}">Tester les fournisseurs IA</a>',
            reverse("admin:portfolio_chat_diagnostic"))

    @admin.display(description="Prompt complet")
    def prompt_preview(self, obj):
        text = chatbot.build_system_prompt(obj)
        return format_html(
            '<pre style="white-space:pre-wrap;max-width:900px;max-height:480px;'
            'overflow:auto;margin:0;font-size:12px">{}</pre>', text)

    def get_urls(self):
        extra = [path("diagnostic/", self.admin_site.admin_view(self.diagnostic_view),
                      name="portfolio_chat_diagnostic")]
        return extra + super().get_urls()

    def diagnostic_view(self, request):
        """Vérifie les fournisseurs configurés et envoie une vraie question de test."""
        cfg = ChatbotSettings.get()
        steps = []

        def step(label, ok, detail=""):
            steps.append({"label": label, "ok": ok, "detail": detail})

        available_providers = []
        for provider, key in (
            ("OpenRouter", settings.OPENROUTER_API_KEY),
            ("Groq", settings.GROQ_API_KEY),
        ):
            step(f"Clé {provider} présente dans l'environnement", bool(key),
                 "" if key else "Fournisseur optionnel : ajoute sa clé pour l'activer.")
            if not key:
                continue
            try:
                models_ = chatbot.available_free_models(key, provider.lower())
                available_providers.append(provider)
                step(f"Modèles gratuits {provider}", True, f"{len(models_)} modèles.")
            except chatbot.AIProviderError as e:
                step(f"Catalogue {provider}", False, f"{e.kind} — {e.detail}")
        if available_providers:
            try:
                reply, model = chatbot.ask_assistant(
                    cfg, "Réponds en une courte phrase en français.", [], "Dis bonjour.")
                step("Réponse de test reçue", True, f"{reply} (modèle : {model})")
            except chatbot.AIProviderError as e:
                step("Appel aux fournisseurs IA", False, f"{e.kind} — {e.detail}")
        ctx = {**self.admin_site.each_context(request), "title": "Test des fournisseurs IA",
               "steps": steps, "opts": self.model._meta}
        return TemplateResponse(request, "admin/portfolio/chat_diagnostic.html", ctx)


@admin.register(ChatKnowledge)
class ChatKnowledgeAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "kind", "active")
    list_editable = ("order", "active")
    list_display_links = ("title",)
    list_filter = ("kind", "active")
    search_fields = ("title", "content")
    ordering = ("order", "id")
    fieldsets = (
        (None, {
            "fields": ("title", "kind", "content", "active", "order"),
            "description": "« Information sur Nick » : un fait que l'IA doit connaître "
                           "(ex. disponibilité, détail d'un projet, langues parlées…). "
                           "« Consigne de comportement » : une règle pour l'IA "
                           "(ex. « propose toujours le lien du portfolio »).",
        }),
    )


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "short_question", "ok", "model_used", "visitor")
    list_filter = ("ok", "created_at")
    search_fields = ("question", "answer", "error")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "visitor", "question", "answer", "ok", "error", "model_used")

    @admin.display(description="Question")
    def short_question(self, obj):
        return (obj.question[:80] + "…") if len(obj.question) > 80 else (obj.question or "—")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
