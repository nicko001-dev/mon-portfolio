from django.shortcuts import render

from .models import (
    Profile, HeroStage, ProblemStatement, SkillGroup,
    Project, Certification, TrainingItem,
    SiteText, NavItem, MarqueeItem, ManifestoStat, FocusItem, ContactItem,
)


def build_hyperspace(profile, txt):
    """Contenu injecté dans l'univers 3D (acte II — base « lilo »).

    Le JSON est émis tel quel par le template puis lu par hyperspace.js :
    chaque information devient un corps, une balise ou une transmission
    que l'on découvre en volant, plutôt qu'un bloc de texte en HTML.
    """
    p = profile or Profile()
    stats = [
        {"value": s.value, "label": s.label}
        for s in ManifestoStat.objects.all()
    ]
    if not stats:
        stats = [
            {"value": p.stat_projects, "label": "Projets menés"},
            {"value": p.stat_certifications, "label": "Certifications"},
            {"value": p.stat_technologies, "label": "Technologies"},
            {"value": p.stat_years, "label": "Années d'atelier"},
        ]
    return {
        "identity": {
            "name": p.name,
            "role": p.role,
            "school": p.school,
            "program": p.program,
            "year": p.program_year,
            "location": p.location,
        },
        "mission": {
            "title": txt.get("space_title", "Applications intelligentes"),
            "text": txt.get(
                "space_text",
                "IA embarquée, mobile et vision par ordinateur — des projets "
                "pensés de bout en bout, souvent sans connexion.",
            ),
            "cta": txt.get("space_cta", "Découvrir mes projets"),
        },
        "stages": [
            {"title": s.title, "body": s.body}
            for s in HeroStage.objects.exclude(title="")
        ],
        "statements": [s.text for s in ProblemStatement.objects.all()],
        "projects": [
            {
                "mono": pj.monogram,
                "title": pj.title,
                "tag": pj.tag,
                "kind": pj.kind,
                "stack": pj.stack,
            }
            for pj in Project.objects.all()
        ],
        "skills": [
            {"name": g.name, "description": g.description}
            for g in SkillGroup.objects.all()
        ],
        "certs": [
            {"title": c.title, "org": c.org, "date": c.date}
            for c in Certification.objects.all()
        ],
        "training": [
            {"title": t.title, "description": t.description}
            for t in TrainingItem.objects.all()
        ],
        "stats": stats,
        # Les planètes de l'univers portent les informations réelles :
        # une ligne courte par corps, dans l'ordre du fichier de base.
        "bodies": [
            f"{p.role} · {p.school}",
            f"{p.program} · {p.program_year}",
            f"{p.location}",
            "IA locale, mobile et vision par ordinateur",
            txt.get("space_title", "Applications intelligentes"),
        ],
        # Les sites de l'univers (astéroïdes, cristaux, arche, galaxie…)
        # portent les compétences, la formation, les certifications et les
        # chiffres du parcours. Le fichier de base ne garde que les
        # emplacements — le contenu vient de la base de données.
        "discoveries": _discoveries(txt, stats),
    }


def _discoveries(txt, stats):
    """Les découvertes de l'univers : mêmes sites que le fichier de base,
    contenu tiré du portfolio (compétences, formation, certifications)."""
    out = []

    # Ceinture d'astéroïdes → ce qui m'anime
    out.append({
        "name": "CEINTURE KUIPER-X",
        "pos": [0, -200, -3000],
        "r": 450,
        "color": "#eab54d",
        "lines": [f.title + " " + f.body for f in FocusItem.objects.all()][:2] or
                 ["Des milliers de roches à frôler — le terrain où j'apprends."],
    })

    # Arche orbitale → boîte à outils (compétences)
    out.append({
        "name": "ARCHE ORBITALE",
        "pos": [-1100, 400, -2800],
        "r": 420,
        "color": "#00f2ff",
        "lines": [f"{g.name} — {g.description}" for g in SkillGroup.objects.all()][:3],
    })

    # Cristaux d'éther → diplôme en cours (formation)
    out.append({
        "name": "CRISTAUX D'ÉTHER",
        "pos": [-1300, -250, -8200],
        "r": 460,
        "color": "#7de8ff",
        "lines": [f"{t.title} — {t.description}" for t in TrainingItem.objects.all()][:3],
    })

    # Galaxie spirale → certifications
    out.append({
        "name": "GALAXIE SPIRALE",
        "pos": [4500, 2200, -9000],
        "r": 1800,
        "color": "#f472b6",
        "lines": [f"{c.title} — {c.org} ({c.date})" for c in Certification.objects.all()][:4],
    })

    # Soleil → le manifeste, en une ligne
    out.append({
        "name": "SOLEIL ALPHA",
        "pos": [-4200, 1500, -1500],
        "r": 420,
        "color": "#eab54d",
        "lines": [
            txt.get("lilo_intro_h1", "Je fabrique") + " " + txt.get("lilo_intro_h2", "pour comprendre"),
            " · ".join(f"{s['value']} {s['label'].lower()}" for s in stats),
        ],
    })
    return out


def index(request):
    profile = Profile.get()
    txt = SiteText.as_dict()
    context = {
        "profile": profile,
        "hero_stages": HeroStage.objects.all(),
        "problem_statements": ProblemStatement.objects.all(),
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
        # Univers hyperspace (acte II)
        "hyperspace": build_hyperspace(profile, txt),
    }
    return render(request, "portfolio/index.html", context)
