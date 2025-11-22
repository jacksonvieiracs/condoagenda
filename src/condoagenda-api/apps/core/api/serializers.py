from rest_framework import serializers
from apps.core.models import Andar, Reserva
from apps.core.services import ReservaService, ReservaValidationError


class CriarReservaRequestSerializer(serializers.Serializer):
    data = serializers.DateField()
    hora = serializers.TimeField()
    numero_apartamento = serializers.IntegerField()
    andar = serializers.ChoiceField(choices=Andar.choices)

    def validate(self, attrs):
        try:
            ReservaService.validate_reserva(
                attrs["data"],
                attrs["hora"],
                attrs["numero_apartamento"],
                attrs["andar"],
            )
        except ReservaValidationError as e:
            if e.field:
                raise serializers.ValidationError({e.field: e.message})
            raise serializers.ValidationError(e.message)

        return attrs

    def create(self, validated_data):
        return ReservaService.create_reserva(
            validated_data["data"],
            validated_data["hora"],
            validated_data["numero_apartamento"],
            validated_data["andar"],
        )


class ReservaSerializer(serializers.ModelSerializer):
    numero_apartamento = serializers.IntegerField(source="apartamento.numero")

    class Meta:
        model = Reserva
        read_only_fields = [
            "id",
            "hora_saida",
            "hora",
            "hora_saida",
            "numero_apartamento",
            "andar",
        ]
        fields = ["id", "data", "hora", "hora_saida", "numero_apartamento", "andar"]


class ListarDatasDisponiveisRequestSerializer(serializers.Serializer):
    andar = serializers.ChoiceField(choices=Andar.choices)


class DataDisponivelSerializer(serializers.Serializer):
    data = serializers.DateField(read_only=True)
    quantidade_slots_disponiveis = serializers.IntegerField(read_only=True)
    disponivel = serializers.BooleanField(read_only=True)


class ListarDatasDisponiveisResponseSerializer(serializers.Serializer):
    datas = DataDisponivelSerializer(many=True)


class ListarSlotsDisponiveisRequestSerializer(serializers.Serializer):
    data = serializers.DateField()
    andar = serializers.ChoiceField(choices=Andar.choices)


class ListarSlotsDisponiveisResponseSerializer(serializers.Serializer):
    slots = serializers.ListField(child=serializers.DictField())
    data = serializers.DateField()
    andar = serializers.ChoiceField(choices=Andar.choices)


class ListarMinhasReservasResponseSerializer(serializers.Serializer):
    reservas = ReservaSerializer(many=True)
