# Generated by Django 2.2.8 on 2020-09-17 19:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(blank=True, choices=[('C', 'Clothing'), ('P', 'Posters'), ('M', 'Mugs')], max_length=2, null=True),
        ),
    ]
