# login/management/commands/create_dev_user.py

import getpass

from django.core.management.base import BaseCommand, CommandError

from login.models import myuser


class Command(BaseCommand):
    help = "Create a development user if it doesn't already exist."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Username for the new user")
        parser.add_argument("email", help="Email address for the new user")
        parser.add_argument(
            "--password",
            "-p",
            help="Password for the new user; if omitted, will be prompted securely",
            required=False,
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]

        # Check if the user already exists
        if myuser.objects.filter(name=username).exists():
            self.stdout.write(
                self.style.WARNING(f"User '{username}' already exists. Skipping.")
            )
            return

        # Prompt for password if not provided
        if not password:
            password = getpass.getpass(f"Password for {username}: ")
            if not password:
                raise CommandError("No password entered. Aborting.")

        # Create and save the dev user
        user = myuser.objects.create_devuser(username, email)
        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created dev user '{username}' with email '{email}'")
        )
