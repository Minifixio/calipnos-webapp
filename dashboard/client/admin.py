from django.contrib import admin

# Register your models here.
from .models import DeviceMeasure, DeviceMeasurePoint

admin.site.register(DeviceMeasure)
admin.site.register(DeviceMeasurePoint)