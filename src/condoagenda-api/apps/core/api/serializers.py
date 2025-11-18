from rest_framework import serializers
from apps.core.models import Andar, Reserva
from apps.core.services import ReservaService, ReservaValidationError


class ReservaSerializer(serializers.ModelSerializer):
    apartamento = serializers.IntegerField()

    class Meta:
        model = Reserva
        read_only_fields = ["id", "hora_saida"]
        fields = ["id", "data", "hora", "hora_saida", "apartamento", "andar"]

    def validate(self, attrs):
        data = attrs.get("data")
        hora = attrs.get("hora")
        andar = attrs.get("andar")
        numero_apartamento = attrs.get("apartamento")

        if not data or not hora or not numero_apartamento:
            return attrs

        try:
            ReservaService.validate_reserva(data, hora, numero_apartamento, andar)
        except ReservaValidationError as e:
            if e.field:
                raise serializers.ValidationError({e.field: e.message})
            raise serializers.ValidationError(e.message)

        return attrs

    def create(self, validated_data):
        data = validated_data["data"]
        hora = validated_data["hora"]
        numero_apartamento = validated_data["apartamento"]
        andar = validated_data.get("andar", 0)

        return ReservaService.create_reserva(data, hora, numero_apartamento, andar)


class ListarSlotsDisponiveisRequestSerializer(serializers.Serializer):
    data = serializers.DateField()
    andar = serializers.ChoiceField(choices=Andar.choices)


class ListarSlotsDisponiveisResponseSerializer(serializers.Serializer):
    slots = serializers.ListField(child=serializers.DictField())
    data = serializers.DateField()
    andar = serializers.ChoiceField(choices=Andar.choices)
