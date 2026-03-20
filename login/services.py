__license__ = """
SPDX-FileCopyrightText: 2026 Hendrik Huyskens <https://github.com/henhuy> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from login.forms import OrganizationForm, ProjectForm
from login.models import Membership, Organization, Project, myuser
from login.permissions import ADMIN_PERM


def get_group_form(group_type: str, data: dict, group_id=None):
    if group_type == "organization":
        form_class = OrganizationForm
        model = Organization
    else:
        form_class = ProjectForm
        model = Project
    group = model.objects.get(id=group_id) if group_id else None
    form = form_class(data, instance=group)
    return form


def create_group(user: myuser, form) -> Group:
    group = form.save()
    membership = Membership.objects.create(user=user, group=group, level=ADMIN_PERM)
    membership.save()
    return group


def edit_group(user: myuser, form) -> Group:
    membership = get_object_or_404(Membership, group=form.instance, user=user)
    if membership.level < ADMIN_PERM:
        raise PermissionDenied
    return form.save()


def delete_group(user: myuser, group_id: int) -> None:
    group = get_object_or_404(Group, id=group_id)
    membership = get_object_or_404(Membership, group=group, user=user)
    if membership.level < ADMIN_PERM:
        raise PermissionDenied
    group.delete()
