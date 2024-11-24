from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator



class User(AbstractUser):
    """Модель для пользователей, созданная для приложения foodgram"""
    USER_REGEX = r'^[\w.@+-]+$'

    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True
    )
    username = models.CharField(
        max_length=150,
        verbose_name='Имя пользователя',
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=USER_REGEX,
                message='Используйте только буквы и символы: \ w . @ + - ',
            ),
        ]
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
#    password = models.CharField(
#       'Пароль', max_length=,
#    )
    avatar = models.ImageField(
        upload_to='media/avatar',
        blank=True,
        null=True,
        verbose_name='Аватар')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        """Мета-параметры"""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        """Строковое представление"""

        return self.username
