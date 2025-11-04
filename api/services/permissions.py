from dataedit.models import Table
from login.models import UserPermission
from login.models import myuser as User
from login.permissions import ADMIN_PERM


def assign_table_holder(user: User, table: Table) -> None:
    """
    Grant ADMIN permission level to user for the specified table.
    """

    perm, created = UserPermission.objects.get_or_create(
        table=table,
        holder=user,
        defaults={"level": ADMIN_PERM},
    )
    if not created:
        perm.level = ADMIN_PERM
        perm.save()
