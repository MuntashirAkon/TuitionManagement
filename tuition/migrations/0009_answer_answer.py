# Generated by Django 2.2.2 on 2019-07-06 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tuition', '0008_auto_20190705_1657'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='answer',
            field=models.TextField(default='', verbose_name='Answer'),
            preserve_default=False,
        ),
    ]
