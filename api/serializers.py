"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from re import match
from uuid import UUID

from django.urls import reverse
from rest_framework import serializers

from dataedit.models import Table
from modelview.models import Energyframework, Energymodel
from oeplatform.settings import URL


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


# TODO jh-RLI: Its called deserializer!!
class DatasetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    external_url = serializers.URLField(
        max_length=1000, required=False, allow_null=True
    )
    type = serializers.ChoiceField(choices=["input", "output"], required=True)
    # title = serializers.SerializerMethodField()

    # ✅ Basic validation for 'name' (regex check only)
    def validate_name(self, value):
        if not match(r"^[\w]+$", value):
            raise serializers.ValidationError(
                "Dataset name should contain only alphanumeric characters "
                "and underscores."
            )
        return value  # Don't check DB here, do it in validate()

    # ✅ Main validation logic (includes db check for object existence)
    def validate(self, data):
        name = data.get("name")
        external_url = data.get("external_url")

        if external_url:
            # ✅ External URL provided → Skip DB check for 'name'
            if not external_url.startswith("https://databus.openenergyplatform.org"):
                raise serializers.ValidationError(
                    {
                        "external_url": (
                            "If you want to link distributions stored outside the OEP, "
                            "please use the Databus: "
                            "https://databus.openenergyplatform.org/app/publish-wizard "
                            "to register your data and use the file or version URI as "
                            "a persistent identifier."
                        )
                    }
                )
            data["name"] = f"{name} (external dataset)"
        else:
            # ✅ No external URL → Validate 'name' in the database
            if not Table.objects.filter(name=name).exists():
                raise serializers.ValidationError(
                    {
                        "name": f"Dataset '{name}' does not exist in the database."
                        "If you want to add links to external distributions please "
                        "add 'external_url' to the request body."
                    }
                )
            full_label = self.get_title(data)
            if full_label:
                data["name"] = full_label

            # ✅ Generate internal distribution URL
            reversed_url = reverse(
                "dataedit:view",
                kwargs={"schema": "scenario", "table": name},
            )
            data["external_url"] = f"{URL}{reversed_url}"

        return data  # Return updated data with 'distribution_url' if applicable

    def get_title(self, data):
        name = data.get("name")
        # ✅ Generate internal distribution label
        full_label = Table.objects.get(name=name).get_readable_table_name()
        if full_label:
            return full_label
        else:
            return None


# TODO jh-RLI: Its called deserializer!!
class ScenarioBundleScenarioDatasetSerializer(serializers.Serializer):
    scenario_bundle = serializers.UUIDField(
        required=True
    )  # Validate the scenario bundle UUID
    scenario = serializers.UUIDField(required=True)  # Validate the scenario UUID
    datasets = serializers.ListField(
        child=DatasetSerializer(), required=True
    )  # List of datasets with 'name' and 'type'

    # Custom validation for 'scenario'
    def validate_scenario(self, value):
        try:
            UUID(str(value))
        except ValueError:
            raise serializers.ValidationError("Invalid UUID format for scenario.")

        return value

    # Custom validation for the entire dataset list
    def validate_dataset(self, value):
        if not value:
            raise serializers.ValidationError("The dataset list cannot be empty.")

        # Check for duplicates in dataset names
        dataset_names = [dataset["name"] for dataset in value]
        if len(dataset_names) != len(set(dataset_names)):
            raise serializers.ValidationError("Dataset names must be unique.")

        return value
