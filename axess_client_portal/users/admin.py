from django.contrib import admin
from .models import User

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_filter = ('username', 'email', 'first_name', 'last_name')
    list_display = ('username', 'email', 'full_name', 'contact_id')

admin.site.register(User, UserAdmin)
