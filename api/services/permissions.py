from dataedit.models import Table as DBTable
from login.models import ADMIN_PERM, UserPermission


def assign_table_holder(user, schema_name, table_name):
    """
    Grant ADMIN permission level to user for the specified table.
    """
    table_obj = DBTable.load(schema_name, table_name)

    perm, created = UserPermission.objects.get_or_create(
        table=table_obj,
        holder=user,
        defaults={"level": ADMIN_PERM},
    )
    if not created:
        perm.level = ADMIN_PERM
        perm.save()
