from typing import Any, Dict, Type, Optional, List

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse
from django.http import Http404, HttpRequest, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import PostForm, CommentForm
from .models import Post, User, Comment, Category

# Константа, которая хранит текущее время
NOW = timezone.now()

# Константа для настройки пагинации
PAGINATE_NUM = 10


class PublicateLoginRequiredMixin(LoginRequiredMixin):
    """Класс миксина, расширяющий функциональность LoginRequiredMixin.

    Класс применяется для ограничения доступа к методам создания,
    редактирования и удаления публикаций для пользователей, которые
    не являются авторами этих публикаций.

    Атрибуты:
        login_url (str): URL-адрес для перенаправления неавторизованного
        пользователя.
        model (Type[Model]): Модель Django, с которой работает миксин.
        action (Optional[str]): Действие, которое предполагается выполнить
        ('create', 'edit' и т.д.)
    """
    login_url: str = "/auth/login/"
    model: Any = None
    action: str = None

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """Метод для обработки запросов перед вызовом представления.

        Аргументы:
            request (HttpRequest): Объект запроса Django.
            *args: Переменные позиции.
            **kwargs: Переменная ключевых слов.

        Возвращает:
            HttpResponse: Объект ответа Django.
        """
        if self.action != "create":
            self.object = get_object_or_404(self.model, pk=kwargs["pk"])
            if request.user != self.object.author:
                if self.action == "edit":
                    return redirect(self.object.get_absolute_url())
                else:
                    raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        """Метод для определения URL-адреса перенаправления после успешного
        выполнения действия.

        В зависимости от типа действия ("delete", "create" или др.),
        возвращается соответствующий URL.
        Если действие - "delete", возвращается URL-адрес главной страницы
        блога.
        Если действие - "create", возвращается URL-адрес профиля автора
        новой публикации.
        В остальных случаях возвращается URL-адрес самой публикации
        (абсолютный URL).

        Возвращаемое значение:
            str: URL-адрес для перенаправления.
        """
        if self.action == "delete":
            return reverse("blog:index")
        elif self.action == "create":
            return reverse(
                "blog:profile",
                kwargs={
                    "slug": self.object.author.username,
                },
            )
        else:
            return self.object.get_absolute_url()


class PostCreateView(PublicateLoginRequiredMixin, CreateView):
    """Класс представления создания новой публикации."""
    model: Type[Post] = Post
    template_name: str = "blog/create.html"
    form_class: Type[PostForm] = PostForm
    action: str = "create"

    def form_valid(self, form: PostForm) -> HttpResponse:
        """Переопределённый метод для добавления автора к экземпляру формы.

        Аргументы:
            form (PostForm): форма с введёнными данными.

        Возвращает:
            HttpResponse: HTTP-ответ после успешной валидации формы.
        """
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDetailView(DetailView):
    """Класс представления отображения одного поста."""
    model: Type[Post] = Post
    fields: str = "all"
    template_name: str = "blog/detail.html"
    queryset = Post.objects.select_related("location", "category")

    def dispatch(self, request: HttpRequest,
                 *args: Any, **kwargs: Any) -> HttpResponse:
        """Переопределённый метод для проверки прав доступа и детализирования.

        Аргументы:
            request (HttpRequest): входящий HTTP-запрос.

        Возвращает:
            HttpResponse: HTTP-ответ после выполнения проверок
            и детализирования.
        """
        self.object = get_object_or_404(Post, pk=kwargs["pk"])
        if self.request.user != self.object.author:
            get_object_or_404(
                Post,
                pk=kwargs["pk"],
                is_published=True,
                category__is_published=True,
                pub_date__lt=NOW,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Переопределённый метод для добавления комментариев к контексту
        страницы.

        Возвращает:
            Dict[str, Any]: словарь с подготовленными данными для передачи
            в шаблон.
        """
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.filter(
            is_published=True,
        ).select_related("author")
        return context


class PostListView(ListView):
    """Класс представления списка публикаций."""
    model: Type[Post] = Post
    fields: str = "__all__"
    template_name: str = "blog/index.html"
    ordering = "-pub_date"
    paginate_by = PAGINATE_NUM
    queryset = Post.objects.filter(
        pub_date__lte=NOW,
        is_published=True,
        category__is_published=True,
    ).select_related("location", "category")


class PostUpdateView(PublicateLoginRequiredMixin, UpdateView):
    """Класс представления изменения публикации."""
    model: Type[Post] = Post
    template_name: str = "blog/create.html"
    form_class: Type[PostForm] = PostForm
    action: str = "edit"


class PostDeleteView(PublicateLoginRequiredMixin, DeleteView):
    """Класс представления удаления публикации."""
    model: Type[Post] = Post
    template_name: str = "blog/create.html"
    form_class: Type[PostForm] = PostForm
    action: str = "delete"


class Comment_publicateLoginRequiredMixin(LoginRequiredMixin):
    """Миксин, требующий аутентификации пользователя и определенных прав на
    действия над объектами."""
    login_url: str = "/auth/login/"
    model = None
    action: str = None

    def dispatch(self, request: HttpRequest,
                 *args: Any, **kwargs: Any) -> HttpResponse:
        """Переопределённый метод для проверки прав доступа
           и детализирования."""
        if self.action != "create":
            if request.user.is_anonymous:
                raise Http404
            get_object_or_404(self.model, pk=kwargs["pk"], author=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        """Возвращает URL-адрес для перенаправления после успешной обработки
           формы."""
        return self.object.get_absolute_url()


class CommentCreateView(Comment_publicateLoginRequiredMixin, CreateView):
    """Представление для создания комментариев. Пользователь должен быть
    аутентифицирован."""
    post_id = None
    model: Type[Comment] = Comment
    form_class: Type[CommentForm] = CommentForm
    template_name: str = "blog/comment.html"
    action: str = "create"

    def dispatch(self, request: HttpRequest,
                 *args: Any, **kwargs: Any) -> HttpResponse:
        """Переопределённый метод для получения поста, к которому добавляется
        комментарий.
        """
        self.post_id = get_object_or_404(Post, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: CommentForm) -> HttpResponse:
        """Если форма валидна, сохраняет модель комментария и связывает её
        спользователем и постом.
        """
        form.instance.author = self.request.user
        form.instance.post = self.post_id
        return super().form_valid(form)


class CommentUpdateView(Comment_publicateLoginRequiredMixin, UpdateView):
    """Класс представления изменения комментария."""
    model: Type[Comment] = Comment
    fields = ("text",)
    template_name: str = "blog/comment.html"


class CommentDeleteView(Comment_publicateLoginRequiredMixin, DeleteView):
    """Класс представления удаления комментария."""
    model: Type[Comment] = Comment
    fields = ("text",)
    template_name: str = "blog/comment.html"


class EditProfileView(LoginRequiredMixin, UpdateView):
    """Класс представления отображения профиля пользователя."""
    login_url: str = "/auth/login/"
    model = User
    fields = (
        "first_name",
        "last_name",
        "email",
    )
    template_name: str = "blog/user.html"

    def get_object(self, *args: Any, **kwargs: Any) -> User:
        """Возвращает текущего авторизованного пользователя как объект,
        подлежащий редактированию.
        """
        return self.request.user

    def get_success_url(self) -> str:
        """Возвращает URL для перенаправления после успешного обновления
        профиля пользователя.
        """
        return reverse("blog:profile", kwargs={"slug": self.object.username})


class PaginatorAddMixin:
    """Миксин для добавления пагинации к списку связанных объектов."""
    paginate_by: int = PAGINATE_NUM

    def paginate_list(self, objects_list: List,
                      paginate_by: Optional[int] = None) -> Paginator:
        """Пагинирует предоставленный список. Количество элементов на странице
        определяется параметром `paginate_by`. Если `paginate_by` не
        предоставлен, используется `self.paginate_by`.
        """
        paginate_by = paginate_by or self.paginate_by
        paginator = Paginator(objects_list, paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return page_obj


class UserDetailView(PaginatorAddMixin, DetailView):
    """Класс представления просмотра профиля пользователя."""

    model: str = User
    fields = "__all__"
    slug_field: str = "username"
    context_object_name: str = "profile"
    template_name: str = "blog/profile.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Добавляет к контексту посты, связанные с пользователем.
        """
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.select_related("location", "category"
                                                 ).order_by("-pub_date")

        if self.request.user != self.object:
            posts = posts.filter(
                is_published=True,
                category__is_published=True,
            )

        page_obj = self.paginate_list(posts)
        context["page_obj"] = page_obj
        return context


class CategoryDetailView(PaginatorAddMixin, DetailView):
    """Класс представления просмотра категории."""

    model: str = Category
    fields = "__all__"
    slug_field: str = "slug"
    template_name: str = "blog/category.html"
    queryset = Category.objects.filter(is_published=True)

    def get_context_data(self, **kwargs) -> dict:
        """Добавляет к контексту посты, связанные с категорией.
        """
        context = super().get_context_data(**kwargs)
        posts = (
            self.object.posts.filter(
                pub_date__lte=NOW,
                is_published=True,
                category__is_published=True,
            )
            .select_related("location", "category")
            .order_by("-pub_date")
        )

        page_obj = self.paginate_list(posts, PAGINATE_NUM)
        context["page_obj"] = page_obj
        return context
