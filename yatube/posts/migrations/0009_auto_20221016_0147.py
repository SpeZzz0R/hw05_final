# Generated by Django 2.2.16 on 2022-10-15 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20221015_2152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(verbose_name='Комментарий'),
        ),
    ]
