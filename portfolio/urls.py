from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/chat/", views.chat_api, name="chat"),
]
