import random


class FakeShopifyService:
    def create_customer(self, first_name, last_name, email):
        return {"id": random.randint(1000, 100000), "first_name": first_name, "last_name": last_name, "email": email}
