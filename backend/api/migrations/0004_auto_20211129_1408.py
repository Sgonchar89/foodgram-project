# Generated by Django 2.2.6 on 2021-11-29 22:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20211128_1634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_cart', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
    ]
