from alembic.config import main
from django.core.management.base import BaseCommand, CommandError
from login.models import myuser, UserGroup, GroupMembership, ADMIN_PERM
from oeplatform.settings import METADATA_PERM_GROUP

class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("user_id")
        parser.add_argument(
            '--admin',
            action='store_true',
        )


    def handle(self, *args, **options):
        uid = options["user_id"]
        admin = options.get("admin", False)
        u = myuser.objects.get(id=int(uid))
        g = UserGroup.objects.get(name=METADATA_PERM_GROUP)
        gm, created = GroupMembership.objects.get_or_create(user=u, group=g)
        if admin:
            gm.level = ADMIN_PERM
        gm.save()
        print("Added user {user} as reviewer".format(user=u.name))
