# Generated by Django 4.2.16 on 2024-11-01 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='avatar',
            field=models.ImageField(null=True, upload_to='users/'),
        ),
    ]
