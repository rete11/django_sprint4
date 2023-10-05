from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма публикации."""
    class Meta:
        model = Post

        exclude = (
            "author",
            "is_published",
        )
        widgets = {"pub_date": forms.DateInput(attrs={"type": "date"})}


class CommentForm(forms.ModelForm):
    """Форма комментария."""
    class Meta:
        model = Comment
        fields = ("text",)
