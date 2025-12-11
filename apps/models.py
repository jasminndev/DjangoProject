from django.db.models import Model, ForeignKey, CASCADE, TextField, DateTimeField
from django.forms import ImageField


class Post(Model):
    author = ForeignKey('auth_.User', on_delete=CASCADE, related_name='posts')
    content = TextField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return self.content


class PostImage(Model):
    post = ForeignKey('apps.Post', on_delete=CASCADE, related_name='images')
    image = ImageField()


class PostView(Model):
    class Meta:
        unique_together = ('post', 'user')

    post = ForeignKey('apps.Post', on_delete=CASCADE, related_name='views')
    user = ForeignKey('auth_.User', on_delete=CASCADE, related_name='views')


class Comment(Model):
    post = ForeignKey('apps.Post', on_delete=CASCADE, related_name='comments')
    author = ForeignKey('auth_.User', on_delete=CASCADE, related_name='comments')
    content = TextField()
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} commented on {self.post}"


class Like(Model):
    post = ForeignKey('apps.Post', on_delete=CASCADE, related_name='likes')
    user = ForeignKey('auth_.User', on_delete=CASCADE, related_name='likes')
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} liked {self.post}"
