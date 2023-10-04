from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Конфигурация приложения Django для модуля блога.

    Этот класс наследуется от AppConfig и содержит основные
    настройкидля блога.

    Атрибуты:
        default_auto_field (str): Поле для автоматического
        создания ID моделей в Django.
        name (str): Название приложения.
        verbose_name (str): Полное название приложения,
        которое будет отображаться в пользовательском интерфейсе Django.
    """
    default_auto_field: str = 'django.db.models.BigAutoField'
    name: str = 'blog'
    verbose_name: str = 'Блог искателей мудрости'
