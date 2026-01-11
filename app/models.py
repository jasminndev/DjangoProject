from django.db.models import Model, ForeignKey, CASCADE, TextField, DateTimeField, ImageField, BooleanField
from django.utils.translation import gettext_lazy as _

from core.storage import SupabaseStorage

supabase_storage = SupabaseStorage()


class Post(Model):
    user = ForeignKey(
        'authentication.User',
        on_delete=CASCADE,
        related_name='posts',
        verbose_name=_('User')
    )
    image = ImageField(upload_to='posts//%Y/%m/%d/', storage=supabase_storage, verbose_name=_('Image'))
    caption = TextField(max_length=2200, blank=True, verbose_name=_('Caption'))
    created_at = DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = DateTimeField(auto_now=True, verbose_name=_('Updated at'))
    is_edited = BooleanField(default=False, verbose_name=_('Is edited'))

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Post by {self.user.username} ({self.created_at})"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()

    @property
    def views_count(self):
        return self.views.count()


class PostView(Model):
    class Meta:
        unique_together = ('post', 'user')
        verbose_name = _('Post View')
        verbose_name_plural = _('Post Views')

    post = ForeignKey(
        'app.Post',
        on_delete=CASCADE,
        related_name='views',
        verbose_name=_('Post')
    )
    user = ForeignKey(
        'authentication.User',
        on_delete=CASCADE,
        related_name='views',
        verbose_name=_('User')
    )


class Comment(Model):
    post = ForeignKey(
        'app.Post',
        on_delete=CASCADE,
        related_name='comments',
        verbose_name=_('Post')
    )
    user = ForeignKey(
        'authentication.User',
        on_delete=CASCADE,
        related_name='comments',
        verbose_name=_('User')
    )
    text = TextField(max_length=500, verbose_name=_('Comment text'))
    created_at = DateTimeField(auto_now_add=True, verbose_name=_('Created at'))

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        return f"{self.user.username} commented on {self.post.id}: {self.text[:30]}"


class Like(Model):
    class Meta:
        ordering = ('-created_at',)
        unique_together = ('post', 'user')
        verbose_name = _('Like')
        verbose_name_plural = _('Likes')

    post = ForeignKey(
        'app.Post',
        on_delete=CASCADE,
        related_name='likes',
        verbose_name=_('Post')
    )
    user = ForeignKey(
        'authentication.User',
        on_delete=CASCADE,
        related_name='likes',
        verbose_name=_('User')
    )
    created_at = DateTimeField(auto_now_add=True, verbose_name=_('Created at'))

    def __str__(self):
        return f"{self.user} liked {self.post}"
