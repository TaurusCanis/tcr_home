# Generated by Django 2.2.8 on 2020-09-17 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20200917_2002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address_type',
            field=models.CharField(choices=[('B', 'billing'), ('S', 'shipping')], max_length=1),
        ),
        migrations.AlterField(
            model_name='item',
            name='label',
            field=models.CharField(blank=True, choices=[('D', 'danger'), ('P', 'primary'), ('S', 'seconary')], max_length=1, null=True),
        ),
    ]
