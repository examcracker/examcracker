# Generated by Django 2.0.4 on 2018-04-29 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0008_coursepattern'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='About Me'),
        ),
    ]
