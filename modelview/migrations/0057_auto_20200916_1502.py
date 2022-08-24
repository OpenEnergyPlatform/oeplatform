from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("modelview", "0056_auto_20200910_1231"),
    ]

    operations = [
        migrations.RunSQL(
            'ALTER TABLE "modelview_basicfactsheet" ALTER COLUMN "contact_email" TYPE varchar(254)[] USING ARRAY["contact_email"];'  # noqa
        )
    ]
