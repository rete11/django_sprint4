from typing import Any
#from django.db.models import Count
from django.db import models
from django.db.models import Model
from django.db.models.query import QuerySet
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
from django.http import Http404, HttpResponse
#from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
#from .settings import DETAIL_VIEW_PAGINATE_BY

from .forms import PostForm, CommentForm
from .models import Post, User, Comment, Category

from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.utils import timezone

#from blog.models import Post, Category

User = get_user_model()

now = timezone.now()
num_posts = 10
PAGINATE_NUM = 10

class PublicateLoginRequiredMixin(LoginRequiredMixin):
    """Миксин авторизации для действий с публикациями."""
    login_url = '/auth/login/'
    model = None
    action = None

    def dispatch(self, request, *args, **kwargs):
        if self.action != 'create':
            self.object = get_object_or_404(self.model, pk=kwargs['pk'])
            if request.user != self.object.author:
                if self.action == 'edit':
                    return redirect(self.object.get_absolute_url())
                else:
                    raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if self.action == 'delete':
            return reverse('blog:index')
        elif self.action == 'create':
            return reverse('blog:profile', kwargs={
                'slug': self.object.author.username,
            }
            )
        else:
            return self.object.get_absolute_url()
        
class PostCreateView(PublicateLoginRequiredMixin, CreateView):
    """Класс представления создания новой публикации."""
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    action = 'create'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    

class PostDetailView(DetailView):
    """Класс представления отображения одного поста."""
    model = Post
    fields = '__all__'
    template_name = 'blog/detail.html'
    queryset = Post.objects.select_related('location', 'category')

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, pk=kwargs['pk'])
        if self.request.user != self.object.author:
            get_object_or_404(
                Post,
                pk=kwargs['pk'],
                is_published=True,
                category__is_published=True,
                pub_date__lt=now,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.filter(
            is_published=True,
        ).select_related(
            'author'
        )
        return context


class PostListView(ListView):
    """Класс представления списка публикаций."""
    model = Post
    fields = '__all__'
    template_name = 'blog/index.html'
    ordering = '-pub_date'
    paginate_by = num_posts
    queryset = Post.objects.filter(
        pub_date__lte=now,
        is_published=True,
        category__is_published=True,
    ).select_related(
        'location', 'category'
    )


class PostUpdateView(PublicateLoginRequiredMixin, UpdateView):
    """Класс представления изменения публикации."""
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    action = 'edit'


class PostDeleteView(PublicateLoginRequiredMixin, DeleteView):
    """Класс представления удаления публикации."""
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    action = 'delete'
    
class Comment_publicateLoginRequiredMixin(LoginRequiredMixin):
    """Миксин авторизации для действий с комментариями."""
    login_url = '/auth/login/'
    model = None
    action = None

    def dispatch(self, request, *args, **kwargs):
        if self.action != 'create':
            if request.user.is_anonymous:
                raise Http404
            get_object_or_404(self.model, pk=kwargs['pk'], 
                              author=request.user
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()

    
class CommentCreateView(Comment_publicateLoginRequiredMixin, CreateView):
    """Класс представления создания нового комментария."""
    post_id = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    action = 'create'

    def dispatch(self, request, *args, **kwargs):
        self.post_id = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_id
        return super().form_valid(form)


class CommentUpdateView(Comment_publicateLoginRequiredMixin, UpdateView):
    """Класс представления изменения комментария."""
    model = Comment
    fields = ('text',)
    template_name = 'blog/comment.html'


class CommentDeleteView(Comment_publicateLoginRequiredMixin, DeleteView):
    """Класс представления удаления комментария."""
    model = Comment
    fields = ('text',)
    template_name = 'blog/comment.html'

class PaginatorMixin():
    """Миксин пагинации списка связанных объектов для контекста DetailView."""
    paginate_by = 1

    def paginate_list(self,
                      objects_list: list[Model],
                      paginate_by=paginate_by):
        """Функция, выдающая объект страницы пагинатора для списка объектов."""
        paginator = Paginator(objects_list, paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return page_obj


class UserDetailView(DetailView, PaginatorMixin):
    """Класс представления отображения профиля пользователя."""
    model = User
    fields = '__all__'
    slug_field = 'username'
    context_object_name = 'profile'
    template_name = 'blog/profile.html'
    #paginate_by = 1

    '''def paginate_list(self, objects_list, paginate_by=None):
        if paginate_by is None:
           paginate_by = self.paginate_by
           paginator = Paginator(objects_list, paginate_by)
           page_number = self.request.GET.get('page')
           page_obj = paginator.get_page(page_number)
        return page_obj'''
    
    
    
    '''def paginate_list(self,
                      objects_list: list[User],
                      paginate_by=paginate_by):
        """Функция, выдающая объект страницы пагинатора для списка объектов."""
        paginator = Paginator(objects_list, paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return page_obj'''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.select_related(
            'location', 'category').order_by('-pub_date')
        if self.request.user != self.object:
            posts = posts.filter(
                is_published=True,
                category__is_published=True,
            )
        page_obj = self.paginate_list(posts, PAGINATE_NUM)
        context['page_obj'] = page_obj
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    """Класс представления редактирования профиля пользователя."""
    login_url = '/auth/login/'
    model = None
    model = User
    fields = (
        'first_name',
        'last_name',
        'email',
    )
    template_name = 'blog/user.html'

    def get_object(self, *args, **kwargs):
        return self.request.user

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'slug': self.object.username})






class CategoryDetailView(DetailView, PaginatorMixin):
    """Класс представления одной категории со списком связанных публикаций."""
    model = Category
    fields = '__all__'
    slug_field = 'slug'
    template_name = 'blog/category.html'
    queryset = Category.objects.filter(is_published=True)
    #paginate_by = 1
    
    '''def paginate_list(self,
                      objects_list: list[Category],
                      paginate_by=paginate_by):
        """Функция, выдающая объект страницы пагинатора для списка объектов."""
        page_obj = self.paginate_list(posts)
        #page_obj = self.paginate_list(posts, paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return page_obj'''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.filter(
            pub_date__lte=now,
            is_published=True,
            category__is_published=True,
        ).select_related('location', 'category'
        ).order_by('-pub_date')
        context['page_obj'] = self.paginate_list(
            posts, PAGINATE_NUM)
        return context





        



'''def index(request):
    # константа 'num_first_posts' отвечает за количество последних публикаций
    # константа 'num_offset' отвечает за сдвиг публикаций
    # num_offset = 5
    template_name = 'blog/index.html'
    post_list = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lt=now,
    ).order_by('-pub_date')
    # [num_offset:num_first_posts]
    paginator = Paginator(post_list, num_posts)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template_name, context)'''


'''def post_detail(request, pk):
    template_name = 'blog/detail.html'
    post = get_object_or_404(
        Post,
        #is_published=True,
        category__is_published=True,
        #pub_date__lt=now,
        pk=pk
    )
    context = {'post': post}
    return render(request, template_name, context)'''


'''def category_posts(request, category_slug):
    template_name = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = get_list_or_404(
        Post,
        is_published=True,
        category__is_published=True,
        pub_date__lt=now,
        category=category,
    )
    paginator = Paginator(post_list, num_posts)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'category': category,
    }
    return render(request, template_name, context)

def user_profile(request, username):
    #num_first_posts = 50
    #num_offset = 0
    template_name = 'blog/profile.html'
    post_list = Post.objects.filter(
        author__username=username,
        is_published=True,
        #is_published=False,
        category__is_published=True,
        #pub_date__lt=now,
    ).order_by('-pub_date')
    #[num_offset:num_first_posts]
    paginator = Paginator(post_list, num_posts)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'profile': username,
        }
    return render(request, template_name, context)'''

