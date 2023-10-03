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
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin


from .forms import PostForm, CommentForm
from .models import Post, User, Comment, Category

now = timezone.now()

PAGINATE_NUM = 10
# Константа для настройки пагинации


class PublicateLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/auth/login/"
    model = None
    action = None

    def dispatch(self, request, *args, **kwargs):
        if self.action != "create":
            self.object = get_object_or_404(self.model, pk=kwargs["pk"])
            if request.user != self.object.author:
                if self.action == "edit":
                    return redirect(self.object.get_absolute_url())
                else:
                    raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
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
    model = Post
    template_name = "blog/create.html"
    form_class = PostForm
    action = "create"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDetailView(DetailView):
    model = Post
    fields = "__all__"
    template_name = "blog/detail.html"
    queryset = Post.objects.select_related("location", "category")

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, pk=kwargs["pk"])
        if self.request.user != self.object.author:
            get_object_or_404(
                Post,
                pk=kwargs["pk"],
                is_published=True,
                category__is_published=True,
                pub_date__lt=now,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.filter(
            is_published=True,
        ).select_related("author")
        return context


class PostListView(ListView):
    model = Post
    fields = "__all__"
    template_name = "blog/index.html"
    ordering = "-pub_date"
    paginate_by = PAGINATE_NUM
    queryset = Post.objects.filter(
        pub_date__lte=now,
        is_published=True,
        category__is_published=True,
    ).select_related("location", "category")


class PostUpdateView(PublicateLoginRequiredMixin, UpdateView):
    model = Post
    template_name = "blog/create.html"
    form_class = PostForm
    action = "edit"


class PostDeleteView(PublicateLoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/create.html"
    form_class = PostForm
    action = "delete"


class Comment_publicateLoginRequiredMixin(LoginRequiredMixin):
    login_url = "/auth/login/"
    model = None
    action = None

    def dispatch(self, request, *args, **kwargs):
        if self.action != "create":
            if request.user.is_anonymous:
                raise Http404
            get_object_or_404(self.model, pk=kwargs["pk"], author=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()


class CommentCreateView(Comment_publicateLoginRequiredMixin, CreateView):
    post_id = None
    model = Comment
    form_class = CommentForm
    template_name = "blog/comment.html"
    action = "create"

    def dispatch(self, request, *args, **kwargs):
        self.post_id = get_object_or_404(Post, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_id
        return super().form_valid(form)


class CommentUpdateView(Comment_publicateLoginRequiredMixin, UpdateView):
    model = Comment
    fields = ("text",)
    template_name = "blog/comment.html"


class CommentDeleteView(Comment_publicateLoginRequiredMixin, DeleteView):
    model = Comment
    fields = ("text",)
    template_name = "blog/comment.html"


class EditProfileView(LoginRequiredMixin, UpdateView):
    login_url = "/auth/login/"
    model = None
    model = User
    fields = (
        "first_name",
        "last_name",
        "email",
    )
    template_name = "blog/user.html"

    def get_object(self, *args, **kwargs):
        return self.request.user

    def get_success_url(self) -> str:
        return reverse("blog:profile", kwargs={"slug": self.object.username})


class UserDetailView(DetailView):
    """Класс представления отображения профиля пользователя."""

    model = User
    fields = "__all__"
    slug_field = "username"
    context_object_name = "profile"
    template_name = "blog/profile.html"
    paginate_by = PAGINATE_NUM

    def paginate_list(self, objects_list: list[User], paginate_by=paginate_by):
        # Получение объекта страницы пагинатора для списка объектов
        paginator = Paginator(objects_list, paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return page_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.select_related("location",
                                                 "category").order_by(
            "-pub_date"
        )
        if self.request.user != self.object:
            posts = posts.filter(
                is_published=True,
                category__is_published=True,
            )
        page_obj = self.paginate_list(posts)
        # PAGINATE_NUM)
        context["page_obj"] = page_obj
        return context


class CategoryDetailView(DetailView):
    model = Category
    fields = "__all__"
    slug_field = "slug"
    template_name = "blog/category.html"
    queryset = Category.objects.filter(is_published=True)
    paginate_by = PAGINATE_NUM

    def paginate_list(self, objects_list: list[Category],
                      paginate_by=paginate_by):
        # Получение объекта страницы пагинатора для списка объектов
        paginator = Paginator(objects_list, paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return page_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = (
            self.object.posts.filter(
                pub_date__lte=now,
                is_published=True,
                category__is_published=True,
            )
            .select_related("location", "category")
            .order_by("-pub_date")
        )
        context["page_obj"] = self.paginate_list(posts, PAGINATE_NUM)
        return context
