from django.contrib import admin

from .models import File
from .models import Preview

admin.site.register(File)
admin.site.register(Preview)
