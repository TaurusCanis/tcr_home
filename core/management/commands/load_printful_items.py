from django.core.management.base import BaseCommand, CommandError
from core.models import Item, ItemVariant, ItemVariantFiles
from django.conf import settings
import base64
import requests
import json

class Command(BaseCommand):
    help = 'Get Printful Items, Item Variants, and ItemVariantFiles'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        printful_api_base = 'https://api.printful.com/'
        key_bytes = settings.PRINTFUL_KEY.encode('utf-8')
        b64Val = base64.b64encode(key_bytes)
        key_decoded = b64Val.decode('utf-8')
        headers = {
            'content-type': 'application/json',
            'Authorization': "Basic %s" %key_decoded
        }
        url = printful_api_base + "store/products"

        response = requests.get(url, headers=headers)
        data = response.json()['result']

        print("data: ", data)
        print("data length: ", len(data))
        count = 1
        for item in data:
            url = printful_api_base + "store/products"
            print("COUNT: ", count)
            print("item: ", item)
            item_id = item["id"]
            print("item_id: ", item_id)
            url = url + "/" + str(item_id)
            print("URL: ", url)
            response = requests.get(url, headers=headers)
            variant_data = response.json()["result"]

            sync_product = variant_data['sync_product']

            print("sync_product: ", sync_product)

            new_item = Item(
                title = sync_product["name"],
            #     price = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
            #     discount_price = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
            #     category = models.CharField(choices=CATEGORY_CHOICES, max_length=2, blank=True, null=True)
            #     label = models.CharField(choices=LABEL_CHOICES, max_length=1, blank=True, null=True)
            #     slug = models.SlugField(blank=True, null=True)
            #     description = models.TextField(blank=True, null=True)
            #     image = models.ImageField(blank=True, null=True)
                printful_product_id = sync_product["id"],
                thumbnail_url = sync_product["thumbnail_url"],
                printful_name = sync_product["name"],
            )

            new_item.save()

            for variant in variant_data["sync_variants"]:
                print("variant: ", variant)
                new_item_variant = ItemVariant(
                    title = variant["name"],
                    item = new_item,
                    printful_variant_id = variant["variant_id"],
                    printful_item_variant_id = variant["id"],
                    retail_price = variant["retail_price"],
                    sku = variant["sku"],
                    product_id = variant["id"],
                )

                new_item_variant.save()
            count += 1



        self.stdout.write(self.style.SUCCESS('Printful DATA: "%s"' % data))

    

    