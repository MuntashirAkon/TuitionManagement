# Generated by Django 2.2.2 on 2019-07-05 10:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='expertise',
            field=models.CharField(max_length=1000, verbose_name='expertise'),
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('institute', models.CharField(max_length=200, verbose_name='Institute')),
                ('department', models.CharField(max_length=200, verbose_name='Department')),
                ('degree', models.CharField(max_length=200, verbose_name='Degree')),
                ('result', models.CharField(max_length=200, verbose_name='Result')),
                ('from_year', models.DateField(verbose_name='From year')),
                ('to_year', models.DateField(verbose_name='To year')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
