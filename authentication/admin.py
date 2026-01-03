from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import Group

from authentication.models import User

admin.site.site_header = "Django Project"
admin.site.site_title = "Project's Admin Portal"
admin.site.index_title = "Welcome"
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(ModelAdmin):
    pass
