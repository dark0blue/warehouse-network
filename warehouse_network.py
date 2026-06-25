from warehouse import Warehouse
from routing_services import get_route_info
from errors import (
    DuplicateWarehouseError,
    WarehouseNotFoundError,
    InvalidQuantityError,
    ProductNotFoundError,
    InsufficientStockError,
    WarehouseCapacityError,
)
import json

class WarehouseNetwork:
    def __init__(self):
        self.warehouses = {}

    def add_warehouse(self, warehouse: Warehouse):
        if warehouse.name in self.warehouses:
            raise DuplicateWarehouseError(
                f"Warehouse '{warehouse.name}' already exists in the network."
            )

        self.warehouses[warehouse.name] = warehouse

    def remove_warehouse(self, warehouse_name: str):
        if warehouse_name not in self.warehouses:
            raise WarehouseNotFoundError(
                f"Warehouse '{warehouse_name}' not found in the network."
            )

        del self.warehouses[warehouse_name]

    def get_warehouse(self, warehouse_name: str) -> Warehouse:
        if warehouse_name not in self.warehouses:
            raise WarehouseNotFoundError(
                f"Warehouse '{warehouse_name}' not found in the network."
            )

        return self.warehouses[warehouse_name]

    def list_warehouses(self):
        return list(self.warehouses.values())

    def __repr__(self):
        return f"WarehouseNetwork(warehouses={len(self.warehouses)})"

    def transfer_products(self, source_name: str, destination_name: str, items: dict[str, int]):
        source = self.get_warehouse(source_name)
        destination = self.get_warehouse(destination_name)

        total_needed_volume = 0

        for product_code, quantity in items.items():
            if quantity <= 0:
                raise InvalidQuantityError(
                    f"Invalid transfer quantity {quantity} for product '{product_code}'. "
                    f"All quantities must be positive."
                )

            if product_code not in source.inventory:
                raise ProductNotFoundError(
                    f"Product '{product_code}' not found in source warehouse '{source_name}'."
                )

            available_quantity = source.get_quantity(product_code)

            if available_quantity < quantity:
                raise InsufficientStockError(
                    f"Not enough quantity of product '{product_code}' in source warehouse '{source_name}'. "
                    f"Requested: {quantity}, available: {available_quantity}."
                )

            product = source.get_product(product_code)
            total_needed_volume += product.volume_m3 * quantity

        remaining_volume = destination.remaining_volume()

        if total_needed_volume > remaining_volume:
            raise WarehouseCapacityError(
                f"Not enough capacity in destination warehouse '{destination_name}'. "
                f"Needed volume: {total_needed_volume:.3f} m³, "
                f"remaining volume: {remaining_volume:.3f} m³."
            )

        for product_code, quantity in items.items():
            removed = source.remove_product(product_code, quantity)

            for removed_batch in removed:
                destination.add_product(
                    removed_batch["product"],
                    removed_batch["quantity"],
                    removed_batch["exp_date"]
                )

    def route_between(self, source_name: str, destination_name: str):
        source = self.get_warehouse(source_name)
        destination = self.get_warehouse(destination_name)

        return get_route_info(
            source.lat,
            source.lon,
            destination.lat,
            destination.lon
        )

    def route_between_customer(self, warehouse_name: str, customer_lat: float, customer_lon: float):
        warehouse = self.get_warehouse(warehouse_name)

        return get_route_info(
            warehouse.lat,
            warehouse.lon,
            customer_lat,
            customer_lon
        )
    
    def overloaded_warehouses(self, threshold: float = 0.85):
        return [
            warehouse
            for warehouse in self.warehouses.values()
            if warehouse.is_overloaded(threshold)
        ]
    
    def redistribute_overloaded_warehouses(
        self,
        threshold: float = 0.85,
        target_threshold: float = 0.75
    ):
        redistribution_plan = []

        for source in self.overloaded_warehouses(threshold):
            excess_volume = source.current_volume() - source.capacity_m3 * target_threshold

            if excess_volume <= 0:
                continue

            for product_code, batches in list(source.inventory.items()):
                for batch in list(batches):
                    if excess_volume <= 0:
                        break

                    product = batch.product
                    product_volume = product.volume_m3

                    if product_volume <= 0:
                        continue

                    max_quantity_to_move = min(
                        batch.quantity,
                        int(excess_volume / product_volume)
                    )

                    if max_quantity_to_move <= 0:
                        continue

                    destinations = [
                        warehouse
                        for warehouse in self.warehouses.values()
                        if warehouse.name != source.name
                        and warehouse.remaining_volume() >= product_volume
                    ]

                    destinations.sort(
                        key=lambda warehouse: self.route_between(
                            source.name,
                            warehouse.name
                        )["distance_km"]
                    )

                    for destination in destinations:
                        free_quantity = int(destination.remaining_volume() / product_volume)

                        quantity_to_move = min(max_quantity_to_move, free_quantity)

                        if quantity_to_move <= 0:
                            continue

                        self.transfer_products(
                            source.name,
                            destination.name,
                            {product_code: quantity_to_move}
                        )

                        moved_volume = quantity_to_move * product_volume
                        excess_volume -= moved_volume

                        redistribution_plan.append({
                            "from": source.name,
                            "to": destination.name,
                            "product_code": product_code,
                            "quantity": quantity_to_move,
                            "exp_date": batch.exp_date,
                            "moved_volume": moved_volume,
                        })

                        break

                if excess_volume <= 0:
                    break

        return redistribution_plan
    
    def to_dict(self):
        warehouses = []

        for warehouse in self.warehouses.values():
            warehouses.append(warehouse.to_dict())

        return {
            "warehouses": warehouses
        }
    
    @classmethod
    def from_dict(cls, data):
        network = cls()

        for warehouse_data in data["warehouses"]:
            warehouse = Warehouse.from_dict(warehouse_data)
            network.add_warehouse(warehouse)

        return network

    def save_to_file(self, filename):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                self.to_dict(),
                file,
                indent=4
            )

    @classmethod
    def load_from_file(cls, filename):
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        return cls.from_dict(data)
    