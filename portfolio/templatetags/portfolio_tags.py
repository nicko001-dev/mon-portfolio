import re

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def bracket_bold(value):
    """Met en gras les [MOTS ENTRE CROCHETS] et convertit les retours à la ligne.

    Le texte est d'abord échappé : aucun HTML saisi dans l'admin n'est interprété.
    """
    escaped = conditional_escape(str(value).replace("\\n", "\n"))
    bolded = re.sub(r"(\[[^\]\n]{1,40}\])", r"<b>\1</b>", str(escaped))
    return mark_safe(bolded.replace("\n", "<br>"))
