from django.contrib import admin
from django.contrib.admin import ModelAdmin

from app.models import Post, Comment, Like


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ['id', 'user', 'caption_preview', 'created_at', 'likes_count', 'comments_count']
    list_filter = ['created_at']
    search_fields = ['user__username', 'caption']
    readonly_fields = ['created_at', 'updated_at', 'likes_count', 'comments_count']
    ordering = ['-created_at']

    def caption_preview(self, obj):
        return obj.caption[:50] + '...' if len(obj.caption) > 50 else obj.caption

    caption_preview.short_description = 'Caption'


@admin.register(Like)
class LikeAdmin(ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__id']
    ordering = ['-created_at']


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ['id', 'user', 'post', 'text_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__id', 'text']
    readonly_fields = ['created_at', ]
    ordering = ['-created_at']

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Comment'
