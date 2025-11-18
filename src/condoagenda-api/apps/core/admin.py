from django.contrib import admin

from .models import Apartamento, Configuracao, Reserva

admin.site.register(Apartamento)
admin.site.register(Reserva)
admin.site.register(Configuracao)
