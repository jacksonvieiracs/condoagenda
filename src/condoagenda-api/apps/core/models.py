from django.db import models
from datetime import time


class Configuracao(models.Model):
    hora_inicio = models.TimeField(default=time(7, 0))
    hora_fim = models.TimeField(default=time(19, 0))
    duracao_reserva_minutos = models.IntegerField(default=120)

    quantidade_agendamento_por_apartamento = models.IntegerField(default=2)
    tempo_lembrete_entrada_minutos = models.IntegerField(default=5)
    tempo_lembrete_saida_minutos = models.IntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuração {self.hora_inicio:%H:%M} - {self.hora_fim:%H:%M}"

    class Meta:
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"


class Apartamento(models.Model):
    numero = models.IntegerField()
    responsavel = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ap {self.numero}"


class Andar(models.IntegerChoices):
    TERRAS = (0, "Térreo")
    PRIMEIRO = (1, "1º Andar")


class Reserva(models.Model):
    PHONE_NUMBER_MAX_LENGTH = 13

    data = models.DateField()
    hora = models.TimeField()
    hora_saida = models.TimeField()

    apartamento = models.ForeignKey(Apartamento, on_delete=models.CASCADE)
    andar = models.IntegerField(default=Andar.TERRAS, choices=Andar.choices)
    phone_number = models.CharField(max_length=PHONE_NUMBER_MAX_LENGTH, blank=True)

    lembrete_entrada_enviado = models.BooleanField(default=False)
    lembrete_saida_enviado = models.BooleanField(default=False)

    enviar_lembrete = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} {self.data:%d/%m/%Y} {self.hora:%H:%M} - {self.apartamento} - {self.get_andar_display()}"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["data", "hora"]

        constraints = [
            models.UniqueConstraint(
                fields=["data", "hora", "andar"], name="unique_reserva"
            )
        ]
