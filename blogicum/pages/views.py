from http import HTTPStatus
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView


class About(TemplateView):
    """Представление страницы About.

    Атрибуты:
    template_name (str): Путь к шаблону страницы About.
    """
    template_name: str = "pages/about.html"


class Rules(TemplateView):
    """Представление страницы Rules.

    Атрибуты:
    template_name (str): Путь к шаблону страницы Rules.
    """
    template_name: str = "pages/rules.html"


def page_not_found(request: HttpRequest,
                   exception: Optional[BaseException]) -> HttpResponse:
    """Обработка ошибки "страница не найдена" (404).

    Аргументы:
        request: объект запроса Django.
        exception: исключение, вызвавшее ошибку.

    Возвращает:
        Отрендеренную страницу 404 со статусом HTTP 404.
    """
    return render(request, "pages/404.html", status=HTTPStatus.NOT_FOUND)


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    """Обработка ошибки несоответствия CSRF-токена (403).

    Аргументы:
        request: объект запроса Django.
        reason (str): причина несоответствия CSRF-токена.

    Возвращает:
        Отрендеренную страницу 403 со статусом HTTP 403.
    """
    return render(request, "pages/403csrf.html", status=HTTPStatus.FORBIDDEN)


def server_error(request: HttpRequest,
                 exception: Optional[BaseException] = None) -> HttpResponse:
    """Обработка серверной ошибки (500).

    Аргументы:
        request: объект запроса Django.
        exception: исключение, вызвавшее серверную ошибку.

    Возвращает:
        Отрендеренную страницу 500 со статусом HTTP 500.
    """
    return render(request, "pages/500.html",
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)
