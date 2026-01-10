from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from authentication.models import User, Follow

admin.site.site_header = "Django Project"
admin.site.site_title = "Project's Admin Portal"
admin.site.index_title = "Welcome"
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Info', {'fields': ('bio', 'avatar',)}),
    )


@admin.register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ['id', 'follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    ordering = ['-created_at']
