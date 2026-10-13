from django.contrib import admin
from .models import (
    Profile, HeroStage, ProblemStatement, SkillGroup,
    Project, Certification, TrainingItem,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "email")

    def has_add_permission(self, request):
        # Fiche unique : on évite d'en créer une deuxième par erreur.
        return not Profile.objects.exists()


@admin.register(HeroStage)
class HeroStageAdmin(admin.ModelAdmin):
    list_display = ("order", "shape", "title", "eyebrow")
    list_editable = ("order",)
    list_display_links = ("shape",)
    ordering = ("order",)


@admin.register(ProblemStatement)
class ProblemStatementAdmin(admin.ModelAdmin):
    list_display = ("order", "text")
    list_editable = ("order",)
    list_display_links = ("text",)
    ordering = ("order",)


@admin.register(SkillGroup)
class SkillGroupAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "description")
    list_editable = ("order",)
    list_display_links = ("name",)
    ordering = ("order",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "tag", "kind")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order",)


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "org", "date", "slug")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order",)


@admin.register(TrainingItem)
class TrainingItemAdmin(admin.ModelAdmin):
    list_display = ("order", "title")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order",)
