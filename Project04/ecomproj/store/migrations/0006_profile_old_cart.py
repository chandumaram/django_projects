# Generated by Django 5.1.2 on 2024-11-06 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='old_cart',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
