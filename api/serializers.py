from re import match
from uuid import UUID

from django.urls import reverse
from rest_framework import serializers

from dataedit.models import Table
from modelview.models import Energyframework, Energymodel


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
        fields = ["id", "model_name", "acronym", "url", "license", "institutions"]


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
        fields = ["id", "model_name", "acronym", "url", "license", "institutions"]


class ScenarioDataTablesSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        kwargs = {"schema": "scenario", "table": obj.name}
        detail_url = reverse(
            "dataedit:view",
            kwargs=kwargs,
        )
        return detail_url

    class Meta:
        model = Table
        # fields = ["id", "model_name", "acronym", "url"]
        fields = ["id", "name", "human_readable_name", "url"]


class DatasetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)  # Dataset table name
    type = serializers.ChoiceField(
        choices=["input", "output"], required=True
    )  # Type: input or output

    # Custom validation for 'name'
    def validate_name(self, value):
        # Use regex to allow alphanumeric characters and underscores
        if not match(r"^[\w]+$", value):
            raise serializers.ValidationError(
                "Dataset name should contain only"
                "alphanumeric characters and underscores."
            )
        # Add any additional custom validation logic here
        return value


class ScenarioBundleScenarioDatasetSerializer(serializers.Serializer):
    scenario = serializers.UUIDField(required=True)  # Validate the scenario UUID
    dataset = serializers.ListField(
        child=DatasetSerializer(), required=True
    )  # List of datasets with 'name' and 'type'

    # Custom validation for 'scenario'
    def validate_scenario(self, value):
        try:
            UUID(str(value))
        except ValueError:
            raise serializers.ValidationError("Invalid UUID format for scenario.")
        # Add any additional custom validation logic here
        return value

    # Custom validation for the entire dataset list
    def validate_dataset(self, value):
        if not value:
            raise serializers.ValidationError("The dataset list cannot be empty.")

        # Check for duplicates in dataset names
        dataset_names = [dataset["name"] for dataset in value]
        if len(dataset_names) != len(set(dataset_names)):
            raise serializers.ValidationError("Dataset names must be unique.")

        # Add any additional custom validation logic here
        return value
