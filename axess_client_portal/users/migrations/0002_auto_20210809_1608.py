# Generated by Django 3.2.5 on 2021-08-09 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Admin',
        ),
        migrations.RemoveField(
            model_name='businesspartner',
            name='user',
        ),
        migrations.RemoveField(
            model_name='client',
            name='user',
        ),
        migrations.DeleteModel(
            name='Employee',
        ),
        migrations.AddField(
            model_name='user',
            name='is_employee',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='BusinessPartner',
        ),
        migrations.DeleteModel(
            name='Client',
        ),
    ]
