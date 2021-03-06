# Generated by Django 2.2.2 on 2019-07-13 11:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Verification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=50, verbose_name='File Type')),
                ('file', models.TextField(verbose_name='File location')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
