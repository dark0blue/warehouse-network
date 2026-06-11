class Warehouse:
    def __init__(self, name: str, capacity_m3: float):
        self.name = name
        self.capacity_m3 = capacity_m3
        self.inventory = {}

    def current_volume(self):
        volume = 0

        for item in self.inventory.values():
            volume += item["product"].volume_m3 * item["quantity"]

        return volume

    def remaining_volume(self):
        return self.capacity_m3 - self.current_volume()

    def add_product(self, product, quantity):
        if quantity <= 0:
            print("Invalid quantity")
            return

        added_volume = product.volume_m3 * quantity

        if added_volume > self.remaining_volume():
            print("Not enough warehouse space")
            return

        if product.code not in self.inventory:
            self.inventory[product.code] = {
                "product": product,
                "quantity": 0
            }

        self.inventory[product.code]["quantity"] += quantity

    def remove_product(self, product_code, quantity):
        if quantity <= 0:
            print("Invalid quantity")
            return

        if product_code not in self.inventory:
            print("Product not found")
            return

        current_quantity = self.inventory[product_code]["quantity"]

        if quantity > current_quantity:
            print("Not enough products in stock")
            return

        self.inventory[product_code]["quantity"] -= quantity

        if self.inventory[product_code]["quantity"] == 0:
            del self.inventory[product_code]

    def get_quantity(self, product_code):
        if product_code not in self.inventory:
            return 0

        return self.inventory[product_code]["quantity"]

    def has_product(self, product_code):
        return self.get_quantity(product_code) > 0

    def get_product(self, product_code):
        if product_code not in self.inventory:
            print("Product not found")
            return

        return self.inventory[product_code]["product"]

    def print_inventory(self):
        print(f"Inventory for {self.name}:")

        if len(self.inventory) == 0:
            print("Empty warehouse")
            return

        for product_code, item in self.inventory.items():
            product = item["product"]
            quantity = item["quantity"]

            print(f"{product_code} - {product.name}: {quantity}")

    def __repr__(self):
        return f"Warehouse({self.name})"