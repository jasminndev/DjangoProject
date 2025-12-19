from django.db.models import Model, ForeignKey, CASCADE, TextField, DateTimeField, ImageField, BooleanField


class Post(Model):
    user = ForeignKey('auth_.User', on_delete=CASCADE, related_name='posts')
    image = ImageField(upload_to='posts/')
    caption = TextField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    is_edited = BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)

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

    post = ForeignKey('app.Post', on_delete=CASCADE, related_name='views')
    user = ForeignKey('auth_.User', on_delete=CASCADE, related_name='views')


class Comment(Model):
    post = ForeignKey('app.Post', on_delete=CASCADE, related_name='comments')
    user = ForeignKey('auth_.User', on_delete=CASCADE, related_name='comments')
    text = TextField()
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.user.username} commented on {self.post.id}: {self.text[:30]}"


class Like(Model):
    class Meta:
        ordering = ('-created_at',)
        unique_together = ('post', 'user')

    post = ForeignKey('app.Post', on_delete=CASCADE, related_name='likes')
    user = ForeignKey('auth_.User', on_delete=CASCADE, related_name='likes')
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} liked {self.post}"
