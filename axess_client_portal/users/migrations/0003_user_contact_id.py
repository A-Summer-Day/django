# Generated by Django 3.2.5 on 2021-08-10 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20210809_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='contact_id',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
