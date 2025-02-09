# Generated by Django 2.2.8 on 2021-05-18 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20200919_1624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address_type',
            field=models.CharField(choices=[('S', 'shipping'), ('B', 'billing')], max_length=1),
        ),
        migrations.AlterField(
            model_name='item',
            name='label',
            field=models.CharField(blank=True, choices=[('D', 'danger'), ('P', 'primary'), ('S', 'seconary')], max_length=1, null=True),
        ),
    ]
