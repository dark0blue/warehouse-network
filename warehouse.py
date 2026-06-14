from datetime import date


class InventoryBatch:
    def __init__(self, product, quantity, exp_date=None):
        self.product = product
        self.quantity = quantity
        self.exp_date = exp_date

    def days_left(self):
        if self.exp_date is None:
            return 999999

        return (self.exp_date - date.today()).days

    def __repr__(self):
        return f"Batch({self.product.code}, quantity={self.quantity}, exp_date={self.exp_date})"


class Warehouse:
    def __init__(self, name: str, capacity_m3: float, lat: float = 0.0, lon: float = 0.0):
        self.name = name
        self.capacity_m3 = capacity_m3
        self.lat = lat
        self.lon = lon
        self.inventory = {}

    def current_volume(self):
        volume = 0

        for batches in self.inventory.values():
            for batch in batches:
                volume += batch.product.volume_m3 * batch.quantity

        return volume

    def remaining_volume(self):
        return self.capacity_m3 - self.current_volume()

    def add_product(self, product, quantity, exp_date=None):
        if quantity <= 0:
            print("Invalid quantity")
            return

        added_volume = product.volume_m3 * quantity

        if added_volume > self.remaining_volume():
            print("Not enough warehouse space")
            return

        if product.code not in self.inventory:
            self.inventory[product.code] = []

        for batch in self.inventory[product.code]:
            if batch.exp_date == exp_date:
                batch.quantity += quantity
                return

        self.inventory[product.code].append(InventoryBatch(product, quantity, exp_date))

    def remove_product(self, product_code, quantity):
        if quantity <= 0:
            print("Invalid quantity")
            return

        if product_code not in self.inventory:
            print("Product not found")
            return

        if quantity > self.get_quantity(product_code):
            print("Not enough products in stock")
            return

        removed_batches = []
        left_to_remove = quantity

        self.inventory[product_code].sort(key=lambda batch: batch.days_left())

        for batch in self.inventory[product_code][:]:
            if left_to_remove == 0:
                break

            taken = min(batch.quantity, left_to_remove)

            removed_batches.append(
                InventoryBatch(batch.product, taken, batch.exp_date)
            )

            batch.quantity -= taken
            left_to_remove -= taken

            if batch.quantity == 0:
                self.inventory[product_code].remove(batch)

        if len(self.inventory[product_code]) == 0:
            del self.inventory[product_code]

        return removed_batches

    def get_quantity(self, product_code):
        if product_code not in self.inventory:
            return 0

        total = 0

        for batch in self.inventory[product_code]:
            total += batch.quantity

        return total

    def has_product(self, product_code):
        return self.get_quantity(product_code) > 0

    def get_product(self, product_code):
        if product_code not in self.inventory:
            print("Product not found")
            return

        return self.inventory[product_code][0].product

    def print_inventory(self):
        print(f"Inventory for {self.name}:")
        print(f"Location: {self.lat}, {self.lon}")
        print(f"Used volume: {self.current_volume():.3f}/{self.capacity_m3:.3f} m3")

        if len(self.inventory) == 0:
            print("Empty warehouse")
            return

        for product_code, batches in self.inventory.items():
            print(product_code)

            for batch in batches:
                print(f"  {batch.product.name}: {batch.quantity}, exp: {batch.exp_date}")

    def __repr__(self):
        return f"Warehouse({self.name}, lat={self.lat}, lon={self.lon})"