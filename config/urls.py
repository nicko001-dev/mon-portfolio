from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    # Fichiers téléversés depuis l'admin (photo, certificats). Servis par Django
    # lui-même pour fonctionner sur tout hébergeur ; sur PythonAnywhere, tu peux
    # aussi déclarer /media/ dans l'onglet « Static files » pour plus de vitesse.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    path("", include("portfolio.urls")),
]
