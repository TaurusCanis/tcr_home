from django.core.management.base import BaseCommand, CommandError
from core.models import Item, ItemVariant, ItemVariantFiles
from django.conf import settings
import base64
import requests
import json

class Command(BaseCommand):
    help = 'Cancel printful orders whose status is DRAFT'

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
        url = printful_api_base + "orders?limit=100"

        response = requests.get(url, headers=headers)
        data = response.json()['result']

        print("data: ", data)
        print("data length: ", len(data))
        count = 1
        for item in data:
            url = printful_api_base + "orders/" + str(item["id"])
            response = requests.delete(url, headers=headers)

            print("response: ", response)

        # self.stdout.write(self.style.SUCCESS('Printful DATA: "%s"' % data))