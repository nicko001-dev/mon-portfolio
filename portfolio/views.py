from django.shortcuts import render

from .models import (
    Profile, HeroStage, ProblemStatement, SkillGroup,
    Project, Certification, TrainingItem,
)


def index(request):
    context = {
        "profile": Profile.get(),
        "hero_stages": HeroStage.objects.all(),
        "problem_statements": ProblemStatement.objects.all(),
        "skill_groups": SkillGroup.objects.all(),
        "projects": Project.objects.all(),
        "certifications": Certification.objects.all(),
        "training_items": TrainingItem.objects.all(),
    }
    return render(request, "portfolio/index.html", context)
