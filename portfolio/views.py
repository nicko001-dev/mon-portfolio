import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import chatbot
from .models import (
    Profile, SkillGroup, Project, Certification, TrainingItem,
    SiteText, NavItem, MarqueeItem, ManifestoStat, FocusItem, ContactItem,
    ChatbotSettings, ChatLog, UniverseBody,
)

log = logging.getLogger(__name__)


def build_hyperspace(txt):
    """Données injectées dans l'univers 3D (lues par hyperspace.js).

    - ``projects`` : une planète par projet (titre, sous-titre, description, pile).
    - ``ui`` : tous les textes affichés par le JavaScript (messages, libellés du HUD),
      modifiables dans l'admin → « Univers 3D · textes, commandes et messages ».
    """
    def t(key, default):
        return txt.get(key, default)

    return {
        "projects": [
            {
                "mono": pj.monogram,
                "title": pj.title,
                "tag": pj.tag,
                "kind": pj.kind,
                "desc": pj.description,
                "stack": pj.stack,
            }
            for pj in Project.objects.all()
        ],
        # Textes des astres (nom, sous-titre, transmission) — lus par hyperspace.js
        "bodies": [
            {"key": b.key, "name": b.name, "sub": b.subtitle, "info": b.info}
            for b in UniverseBody.objects.all()
        ],
        "ui": {
            "discovery": t("hs_toast_discovery", "DÉCOUVERTE"),
            "warpTitle": t("hs_toast_warp_title", "HORIZON FRANCHI"),
            "warpText": t("hs_toast_warp_text", "Entrée dans l\'Atelier..."),
            "welcomeTitle": t("hs_toast_welcome_title", "BIENVENUE DANS L\'UNIVERS"),
            "welcomeText": t("hs_toast_welcome_text", "Quête : Trouve le trou noir pour accéder à l\'Atelier !"),
            "returnTitle": t("hs_toast_return_title", "RETOUR DANS L\'UNIVERS"),
            "returnText": t("hs_toast_return_text", "Cap maintenu vers les étoiles."),
            "target": t("hs_target_label", "CIBLE"),
            "speed": t("hs_speed_label", "VITESSE"),
        },
    }


def index(request):
    profile = Profile.get() or Profile()
    txt = SiteText.as_dict()
    bot = ChatbotSettings.get()
    context = {
        "profile": profile,
        "skill_groups": SkillGroup.objects.all(),
        "projects": Project.objects.all(),
        "certifications": Certification.objects.all(),
        "training_items": TrainingItem.objects.all(),
        # Contenu éditable depuis l'admin
        "txt": txt,
        "nav_items": NavItem.objects.all(),
        "nav_header": NavItem.objects.filter(show_in_nav=True),
        "nav_drawer": NavItem.objects.filter(show_in_drawer=True),
        "marquee_items": MarqueeItem.objects.all(),
        "manifesto_stats": ManifestoStat.objects.all(),
        "focus_items": FocusItem.objects.all(),
        "contact_items": ContactItem.objects.all(),
        # Univers 3D
        "hyperspace": build_hyperspace(txt),
        # Assistant IA (configuration publique du widget — jamais la clé API)
        "chatbot": {
            "enabled": bot.enabled,
            "name": bot.assistant_name,
            "subtitle": bot.header_subtitle,
            "welcome": bot.welcome_message,
            "placeholder": bot.placeholder,
            "suggestions": bot.suggestion_list(),
            "universeSuggestions": bot.universe_suggestion_list(),
            "alertText": bot.universe_alert_text,
            "maxChars": bot.max_message_chars,
            "url": "/api/chat/",
        },
    }
    return render(request, "portfolio/index.html", context)


# ── Assistant IA ────────────────────────────────────────────────────────
ERROR_TEXT = {
    "visitor": "Vous avez posé beaucoup de questions en peu de temps. Réessayez dans un moment.",
    "global": "L'assistant a atteint sa limite d\'utilisation pour aujourd\'hui. Réessayez demain.",
    "quota": "Les modèles gratuits sont temporairement limités ou saturés. Réessayez dans une minute.",
}


def _fail(request, visitor, cfg, status, user_msg, question="", error="", model=""):
    ChatLog.objects.create(
        visitor=visitor,
        question=question if cfg.log_conversations else "",
        ok=False, error=error[:200], model_used=model,
    )
    payload = {"error": user_msg}
    # Le détail technique n'est montré qu'à un administrateur connecté (jamais aux visiteurs) :
    # pratique pour comprendre un échec sans aller chercher dans les journaux du serveur.
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.is_staff:
        payload["debug"] = error[:300]
    return JsonResponse(payload, status=status)


@require_POST
def chat_api(request):
    cfg = ChatbotSettings.get()
    if not cfg.enabled:
        return JsonResponse({"error": cfg.unavailable_message}, status=503)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Requête invalide."}, status=400)

    message = str(data.get("message", "")).strip()
    if not message:
        return JsonResponse({"error": "Le message est vide."}, status=400)
    if len(message) > cfg.max_message_chars:
        return JsonResponse(
            {"error": f"Message trop long ({cfg.max_message_chars} caractères maximum)."}, status=400)

    visitor = chatbot.visitor_id(request)
    limit = chatbot.check_limits(cfg, visitor)
    if limit:
        return JsonResponse({"error": ERROR_TEXT[limit]}, status=429)

    history = chatbot.clean_history(data.get("history"), cfg)
    screen = data.get("screen") if data.get("screen") in chatbot.SCREEN_LABELS else None
    try:
        reply, model = chatbot.ask_assistant(
            cfg, chatbot.build_system_prompt(cfg, screen=screen), history, message)
    except chatbot.AIProviderError as e:
        log.error("Les fournisseurs IA ont échoué (%s) : %s", e.kind, e.detail)
        user_msg = ERROR_TEXT["quota"] if e.kind == "quota" else cfg.unavailable_message
        status = 429 if e.kind == "quota" else 503
        return _fail(request, visitor, cfg, status, user_msg, message, f"{e.kind}: {e.detail}")

    ChatLog.objects.create(
        visitor=visitor,
        question=message if cfg.log_conversations else "",
        answer=reply if cfg.log_conversations else "",
        ok=True, model_used=model,
    )
    return JsonResponse({"reply": reply})
