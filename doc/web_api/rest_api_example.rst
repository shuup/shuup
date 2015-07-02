REST API Usage Example
======================

This sketch of a script illustrates how to use the Shoop REST API.

.. code-block:: python

   # -*- coding: utf-8 -*-
   import json
   import uuid
   import requests

   base_url = "http://127.0.0.1:8000/api/"
   s = requests.session()
   s.auth = ("admin", "admin")

   def send(endpoint, data, method="post"):
       data = json.dumps(data)
       resp = s.request(method, base_url + endpoint, data=data, headers={
           "Content-Type": "application/json",
           "Accept": "application/json;indent=4",
           "X-Requested-With": "XMLHttpRequest"  # For `request.is_ajax()`
       })
       if resp.status_code > 300:
           raise Exception(resp.text)
       return resp.json()


   def create_product():
       product = send("shoop/product/", {
           "tax_class": 1,
           "sku": str(uuid.uuid4()),
           "type": 1,
           "translations": {
               "en": {
                   "name": "Hello"
               }
           }
       })
       return product


   def create_shop_product(product):
       product_id = product["id"]

       shop_product = send("shoop/shop_product/", {
           "product": product_id,
           "shop": 1,
       })
       assert not shop_product.get("primary_category")

       shop_product = send("shoop/shop_product/%d/" % shop_product["id"], {
           "primary_category": 1,
           "purchase_multiple": 38
       }, "patch")
       assert shop_product.get("primary_category") == 1
       return shop_product


   def create_product_price(product):
       price = send("shoop/simple_product_price/", {
           "product": product["id"],
           "shop": None,
           "group": None,
           "price": 180
       })
       return price


   def main():
       product = create_product()
       shop_product = create_shop_product(product)
       price = create_product_price(product)
       print(product["id"])


   if __name__ == "__main__":
       main()
