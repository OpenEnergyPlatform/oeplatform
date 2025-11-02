from dataedit.models import Table
from login.models import ADMIN_PERM, UserPermission


def assign_table_holder(user, schema: str, table: str):
    """
    Grant ADMIN permission level to user for the specified table.
    """
    table_obj = Table.load(name=table)

    perm, created = UserPermission.objects.get_or_create(
        table=table_obj,
        holder=user,
        defaults={"level": ADMIN_PERM},
    )
    if not created:
        perm.level = ADMIN_PERM
        perm.save()
