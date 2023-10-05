from django.urls import path

from . import views


app_name = "pages"

urlpatterns = [
    path("pages/about/", views.About.as_view(), name="about"),
    path("pages/rules/", views.Rules.as_view(), name="rules"),
]
