# Generated by Django 3.2.13 on 2022-08-23 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tutorials", "0010_alter_tutorial_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tutorial",
            name="category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Training", [("overview", "Overview")]),
                    (
                        "Tutorial",
                        [
                            ("general", "General"),
                            ("publication", "Publication/Licensing"),
                            ("io", "Upload/Download"),
                            ("data_structure", "Data Structure"),
                            ("ontology", "Ontology"),
                            ("other", "Other Topics"),
                        ],
                    ),
                ],
                max_length=15,
            ),
        ),
    ]