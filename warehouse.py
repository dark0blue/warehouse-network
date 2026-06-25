from product import Product
from datetime import date
from errors import (
    InvalidQuantityError,
    WarehouseCapacityError,
    BatchNotFoundError,
    InsufficientStockError,
    ProductNotFoundError,
)


class InventoryBatch:
    def __init__(
            self,
            product: Product,
            quantity: int,
            exp_date: date | None = None
    ):
        if quantity <= 0:
            raise InvalidQuantityError(
                f"Invalid batch quantity {quantity}. Quantity must be positive."
            )
        self.product = product
        self.quantity = quantity
        self.exp_date = exp_date

    def __repr__(self):
        return (
            f"InventoryBatch("
            f"product={self.product.code}, "
            f"quantity={self.quantity}, "
            f"exp_date={self.exp_date}"
            f")"
        )
    
    def to_dict(self):
        return {
            "product": self.product.to_dict(),
            "quantity": self.quantity,
            "exp_date": self.exp_date.isoformat() if self.exp_date else None
        }


    @classmethod
    def from_dict(cls, data):
        exp_date = None

        if data["exp_date"] is not None:
            exp_date = date.fromisoformat(data["exp_date"])

        return cls(
            Product.from_dict(data["product"]),
            data["quantity"],
            exp_date
        )


class Warehouse:
    def __init__(self, name: str, capacity: float, lat: float = 0.0, lon: float = 0.0):
        self.name = name
        self.capacity_m3 = capacity
        self.lat = lat
        self.lon = lon
        self.inventory = {}

    def current_volume(self) -> float:
        total_volume = 0

        for batches in self.inventory.values():
            for batch in batches:
                total_volume += batch.product.volume_m3 * batch.quantity
        return total_volume

    def remaining_volume(self) -> float:
        return self.capacity_m3 - self.current_volume()

    def add_product(self, product: Product, quantity: int, exp_date: date | None = None):
        if quantity <= 0:
            raise InvalidQuantityError(
                f"Invalid quantity {quantity} for product '{product.code}'. "
                f"Quantity must be positive."
            )
        needed_volume = product.volume_m3 * quantity
        remaining_volume = self.remaining_volume()
        if needed_volume > remaining_volume:
            raise WarehouseCapacityError(
                f"Not enough capacity in warehouse '{self.name}'. "
                f"Product: '{product.code}', quantity: {quantity}. "
                f"Needed volume: {needed_volume:.3f} m³, "
                f"remaining volume: {remaining_volume:.3f} m³."
            )
        existing_batch = self.find_batch(product.code, exp_date)
        if existing_batch is not None:
            existing_batch.quantity += quantity
            return
        batch = InventoryBatch(product, quantity, exp_date)
        if product.code not in self.inventory:
            self.inventory[product.code] = []
        self.inventory[product.code].append(batch)

    def remove_from_batch(self, product_code: str, exp_date: date | None, quantity: int):
        if quantity <= 0:
            raise InvalidQuantityError(
                f"Invalid quantity {quantity} for product '{product_code}'. "
                f"Quantity must be positive."
            )

        batch = self.find_batch(product_code, exp_date)
        if batch is None:
            raise BatchNotFoundError(
                f"Batch not found in warehouse '{self.name}'. "
                f"Product: '{product_code}', expiration date: {exp_date}."
            )

        if batch.quantity < quantity:
            raise InsufficientStockError(
                f"Not enough quantity in batch. "
                f"Warehouse: '{self.name}', product: '{product_code}', "
                f"expiration date: {exp_date}. "
                f"Requested: {quantity}, available: {batch.quantity}."
            )
        batch.quantity -= quantity
        if batch.quantity == 0:
            self.inventory[product_code].remove(batch)

            if len(self.inventory[product_code]) == 0:
                del self.inventory[product_code]

    def remove_product(self, product_code: str, quantity: int):
        if quantity <= 0:
            raise InvalidQuantityError(
                f"Invalid quantity {quantity} for product '{product_code}'. "
                f"Quantity must be positive."
            )

        if product_code not in self.inventory:
            raise ProductNotFoundError(
                f"Product '{product_code}' not found in warehouse '{self.name}'."
            )

        available_quantity = self.get_quantity(product_code)
        if available_quantity < quantity:
            raise InsufficientStockError(
                f"Not enough quantity in warehouse '{self.name}'. "
                f"Product: '{product_code}'. "
                f"Requested: {quantity}, available: {available_quantity}."
            )
        batches = sorted(
            self.inventory[product_code],
            key=lambda batch: batch.exp_date or date.max
        )

        remaining = quantity
        removed_batches = []

        for batch in batches:
            if remaining == 0:
                break

            taken = min(batch.quantity, remaining)

            removed_batches.append({
                "product": batch.product,
                "quantity": taken,
                "exp_date": batch.exp_date
            })

            self.remove_from_batch(product_code, batch.exp_date, taken)
            remaining -= taken
        return removed_batches

    def get_quantity(self, product_code: str) -> int:
        if product_code not in self.inventory:
            return 0
        return sum(batch.quantity for batch in self.inventory[product_code])

    def has_product(self, product_code: str) -> bool:
        return self.get_quantity(product_code) > 0

    def get_product(self, product_code: str) -> Product:
        if product_code not in self.inventory:
            raise ProductNotFoundError(
                f"Product '{product_code}' not found in warehouse '{self.name}'."
            )
        return self.inventory[product_code][0].product

    def find_batch(self, product_code: str, exp_date: date | None):
        if product_code not in self.inventory:
            return None

        for batch in self.inventory[product_code]:
            if batch.exp_date == exp_date:
                return batch
        return None

    def __repr__(self):
        return (
            f"Warehouse("
            f"name={self.name}, "
            f"capacity_m3={self.capacity_m3}, "
            f"used_volume={self.current_volume():.2f}"
            f")"
        )
    

    def load_ratio(self) -> float:
        if self.capacity_m3 == 0:
            return 1.0  
        return self.current_volume() / self.capacity_m3


    def is_overloaded(self, threshold: float = 0.85) -> bool:
        return self.load_ratio() > threshold
    
    def to_dict(self):
        inventory = {}

        for product_code, batches in self.inventory.items():
            inventory[product_code] = []

            for batch in batches:
                inventory[product_code].append(batch.to_dict())

        return {
            "name": self.name,
            "capacity_m3": self.capacity_m3,
            "lat": self.lat,
            "lon": self.lon,
            "inventory": inventory
        }


    @classmethod
    def from_dict(cls, data):
        warehouse = cls(
            data["name"],
            data["capacity_m3"],
            data["lat"],
            data["lon"]
        )

        for product_code, batches_data in data["inventory"].items():
            warehouse.inventory[product_code] = []

            for batch_data in batches_data:
                batch = InventoryBatch.from_dict(batch_data)
                warehouse.inventory[product_code].append(batch)

        return warehouse