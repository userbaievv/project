# Generated by Django 4.2.20 on 2025-04-18 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registereduser',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
