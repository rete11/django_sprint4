from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView

from django.urls import include, path, reverse_lazy

handler404 = "pages.views.page_not_found"

handler500 = "pages.views.server_error"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("django.contrib.auth.urls")),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "auth/registration/",
        CreateView.as_view(
            template_name="registration/registration_form.html",
            form_class=UserCreationForm,
            success_url=reverse_lazy("blog:index"),
        ),
        name="registration",
    ),
    path("", include("pages.urls")),
    path("", include("blog.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
