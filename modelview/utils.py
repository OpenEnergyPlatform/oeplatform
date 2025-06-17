# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

from django.urls import reverse

from modelview.models import Energyframework, Energymodel


def get_url(sheettype, obj_id):
    kwargs = {"sheettype": sheettype, "model_name": obj_id}
    detail_url = reverse(
        "modelview:show-factsheet",
        kwargs=kwargs,
    )
    return detail_url


def get_model_class(model_type: str):
    if model_type == "energymodel":
        return Energymodel
    elif model_type == "energyframework":
        return Energyframework
    else:
        raise ValueError(f"Model type '{model_type}' is not recognized.")


def get_model_metadata_by_id(id_model: int, model_type: str):
    model_class = get_model_class(model_type)
    model_instance = (
        model_class.objects.filter(id=id_model).values("model_name", "acronym").first()
    )

    if model_instance is None:
        return None  # Handle the case when the model is not found

    model_metadata = {
        "id": id_model,
        "name": model_instance["model_name"],
        "acronym": model_instance["acronym"],
        "urn": get_url("framework", id_model),
    }

    return model_metadata


def get_framework_metadata_by_id(id_framework: int, model_type: str):
    model_class = get_model_class(model_type)
    model_instance = (
        model_class.objects.filter(id=id_framework)
        .values("model_name", "acronym")
        .first()
    )

    if model_instance is None:
        return None  # Handle the case when the model is not found

    model_metadata = {
        "id": id_framework,
        "name": model_instance["model_name"],
        "acronym": model_instance["acronym"],
        "urn": get_url("model", id_framework),
    }

    return model_metadata


def get_framework_metadata_by_name(framework_name: str, model_type: str):
    """Functionality mainly used in data migration / transformation script.
    It helps to restore data that in in the OEKG but its structure does
    not match the current retrieval functionality any more.

    """

    model_class = get_model_class(model_type)
    model_instance = (
        model_class.objects.filter(model_name=framework_name)
        .values("id", "acronym")
        .first()
    )

    if model_instance is None:
        return None  # Handle the case when the model is not found

    model_metadata = {
        "id": model_instance["id"],
        "name": framework_name,
        "acronym": model_instance["acronym"],
        "urn": get_url("framework", model_instance["id"]),
    }

    return model_metadata


def get_model_metadata_by_name(model_name: str, model_type: str):
    """Functionality mainly used in data migration / transformation script.
    It helps to restore data that in in the OEKG but its structure does
    not match the current retrieval functionality any more.

    """

    model_class = get_model_class(model_type)

    model_instance = (
        model_class.objects.filter(model_name=model_name)
        .values("id", "acronym")
        .first()
    )
    if model_instance is None:
        return None  # Handle the case when the model is not found

    model_metadata = {
        "id": model_instance["id"],
        "name": model_name,
        "acronym": model_instance["acronym"],
        "urn": get_url("model", model_instance["id"]),
    }

    return model_metadata
