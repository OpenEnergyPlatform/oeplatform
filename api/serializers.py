from rest_framework import serializers
from modelview.models import Energyframework, Energymodel
from dataedit.models import Table
from django.urls import reverse


class EnergyframeworkSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        kwargs = {"sheettype": "framework", "model_name": obj.id}
        detail_url = reverse(
            "modelview:show-factsheet",
            kwargs=kwargs,
        )
        return detail_url

    class Meta:
        model = Energyframework
        fields = ["id", "model_name", "acronym", "url"]


class EnergymodelSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        kwargs = {"sheettype": "model", "model_name": obj.id}
        detail_url = reverse(
            "modelview:show-factsheet",
            kwargs=kwargs,
        )
        return detail_url

    class Meta:
        model = Energymodel
        # fields = ["id", "model_name", "acronym", "url"]
        fields = ["id", "model_name", "acronym", "url"]


class ScenarioDataTablesSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        kwargs = {"sheettype": "model", "model_name": obj.id}
        detail_url = reverse(
            "modelview:show-factsheet",
            kwargs=kwargs,
        )
        return detail_url

    class Meta:
        model = Table
        # fields = ["id", "model_name", "acronym", "url"]
        fields = ["id", "model_name", "acronym", "url"]
