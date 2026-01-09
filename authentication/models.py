from ckeditor.fields import RichTextField
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models import ImageField, Model, ForeignKey, CASCADE
from django.db.models.fields import EmailField, DateTimeField, CharField, BooleanField
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ru', 'Русский'),
        ('uz', 'O‘zbekcha'),
    ]

    language = CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    email = EmailField(unique=True)
    avatar = ImageField(upload_to='avatars/%Y/%m/%d/', null=True, blank=True)
    bio = RichTextField(null=True, blank=True)
    updated_at = DateTimeField(auto_now=True)
    is_deleted = BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.following.count()

    @property
    def posts_count(self):
        return self.posts.count()


class Follow(Model):
    class Meta:
        ordering = ('-created_at',)
        unique_together = ('follower', 'following')
        verbose_name = _('Follow')
        verbose_name_plural = _('Follows')

    follower = ForeignKey(
        'authentication.User',
        on_delete=CASCADE,
        related_name='following',
        verbose_name=_('Follower'))
    following = ForeignKey(
        'authentication.User',
        on_delete=CASCADE,
        related_name='followers',
        verbose_name=_('Following'))
    created_at = DateTimeField(auto_now_add=True, verbose_name=_('Created at'))

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
