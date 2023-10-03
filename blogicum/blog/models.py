from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class PublishedModel(models.Model):
    """Абстрактная модель. Добвляет флаги is_published, created_at"""

    is_published = models.BooleanField(
        "Опубликовано",
        help_text="Снимите галочку, чтобы скрыть публикацию.",
        default=True,
        blank=False,
    )
    created_at = models.DateTimeField(
        "Добавлено",
        auto_now_add=True,
        blank=False,
    )

    class Meta:
        abstract = True


class Post(PublishedModel):
    title = models.CharField("Заголовок", max_length=256)
    text = models.TextField("Текст")
    pub_date = models.DateTimeField(
        "Дата и время публикации",
        help_text="Если установить дату и время "
        + "в будущем — можно делать отложенные публикации.",
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор публикации",
        on_delete=models.CASCADE,
        related_name="posts",
    )
    location = models.ForeignKey(
        "Location",
        verbose_name="Местоположение",
        related_name="posts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        "Category",
        related_name="posts",
        verbose_name="Категория",
        on_delete=models.SET_NULL,
        null=True,
    )
    image = models.ImageField(
        "Изображения",
        upload_to="posts_images",
        blank=True,
    )

    class Meta:
        verbose_name = "публикация"
        verbose_name_plural = "Публикации"

    def __str__(self) -> str:
        return f'"{self.title}" от {self.pub_date}'

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"pk": self.pk})

    @property
    def comment_count(self):
        return Comment.objects.filter(post_id=self.pk).count()


class Category(PublishedModel):
    title = models.CharField("Заголовок", max_length=256, blank=False)
    description = models.TextField("Описание", blank=False)
    slug = models.SlugField(
        "Идентификатор",
        blank=False,
        help_text="Идентификатор страницы "
        + "для URL; разрешены символы латиницы, "
        + "цифры, дефис и подчёркивание.",
        unique=True,
    )

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.title


class Location(PublishedModel):
    name = models.CharField(
        "Название места",
        max_length=256,
        blank=False,
    )

    class Meta:
        verbose_name = "местоположение"
        verbose_name_plural = "Местоположения"

    def __str__(self):
        return self.name


class Comment(PublishedModel):
    text = models.TextField(
        blank=False,
        verbose_name="Текст",
    )
    author = models.ForeignKey(
        User,
        related_name="comments",
        verbose_name="Автор комментария",
        on_delete=models.CASCADE,
    )
    post = models.ForeignKey(
        Post,
        verbose_name="Публикация",
        on_delete=models.CASCADE,
        related_name="comments",
    )

    class Meta:
        ordering = ("created_at",)

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"pk": self.post.pk})
