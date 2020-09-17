# Generated by Django 2.2.8 on 2020-09-17 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20200917_1953'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='braintree_transaction_id',
        ),
        migrations.AlterField(
            model_name='address',
            name='address_type',
            field=models.CharField(choices=[('B', 'billing'), ('S', 'shipping')], max_length=1),
        ),
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(blank=True, choices=[('C', 'Clothing'), ('M', 'Mugs'), ('P', 'Posters')], max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='label',
            field=models.CharField(blank=True, choices=[('P', 'primary'), ('D', 'danger'), ('S', 'seconary')], max_length=1, null=True),
        ),
    ]
