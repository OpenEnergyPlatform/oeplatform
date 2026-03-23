__license__ = """
SPDX-FileCopyrightText: 2026 Hendrik Huyskens <https://github.com/henhuy> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from dataedit.models import Table
from login.forms import OrganizationForm, ProjectForm
from login.models import GroupPermission, Membership, Organization, Project, myuser
from login.permissions import ADMIN_PERM, WRITE_PERM


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


def add_table_to_group(user: myuser, group: Group, table: Table) -> GroupPermission:
    user_permissions = table.userpermission_set.filter(
        holder=user, level__gt=WRITE_PERM
    ).first()
    if user_permissions is None:
        raise PermissionDenied("No permission to add this table.")

    permission, _ = GroupPermission.objects.get_or_create(holder=group, table=table)
    permission.save()
    return permission


def remove_table_from_group(user: myuser, group: Group, table: Table) -> None:
    user_permissions = table.userpermission_set.filter(
        holder=user, level__gt=WRITE_PERM
    ).first()
    if user_permissions is None:
        raise PermissionDenied("No permission to remove this table.")

    GroupPermission.objects.get(holder=group, table=table).delete()


def alter_table_in_group(
    user: myuser, group: Group, table: Table, level: int
) -> GroupPermission:
    user_permissions = table.userpermission_set.filter(
        holder=user, level__gt=WRITE_PERM
    ).first()
    if user_permissions is None:
        raise PermissionDenied("No permission to alter this table.")

    permission = GroupPermission.objects.get(holder=group, table=table)
    permission.level = level
    permission.save()
    return permission
