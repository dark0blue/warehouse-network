from warehouse import Warehouse
from routing_services import get_route_info


class WarehouseNetwork:
    def __init__(self):
        self.warehouses = {}

    def add_warehouse(self, warehouse: Warehouse):
        if warehouse.name in self.warehouses:
            print("Warehouse already exists")
            return

        self.warehouses[warehouse.name] = warehouse

    def remove_warehouse(self, warehouse_name):
        if warehouse_name not in self.warehouses:
            print("Warehouse not found")
            return

        del self.warehouses[warehouse_name]

    def get_warehouse(self, warehouse_name):
        if warehouse_name not in self.warehouses:
            print("Warehouse not found")
            return

        return self.warehouses[warehouse_name]

    def list_warehouses(self):
        return list(self.warehouses.values())

    def print_warehouses(self):
        if len(self.warehouses) == 0:
            print("No warehouses in network")
            return

        for warehouse in self.warehouses.values():
            print(warehouse)

    def transfer_products(self, source_name, destination_name, items):
        source = self.get_warehouse(source_name)
        destination = self.get_warehouse(destination_name)

        if source is None or destination is None:
            return

        total_needed_volume = 0

        for product_code, quantity in items.items():
            if quantity <= 0:
                print("Invalid quantity")
                return

            if not source.has_product(product_code):
                print("Product not found in source warehouse")
                return

            if source.get_quantity(product_code) < quantity:
                print("Not enough products in source warehouse")
                return

            product = source.get_product(product_code)
            total_needed_volume += product.volume_m3 * quantity

        if total_needed_volume > destination.remaining_volume():
            print("Not enough space in destination warehouse")
            return

        for product_code, quantity in items.items():
            product = source.get_product(product_code)

            source.remove_product(product_code, quantity)
            destination.add_product(product, quantity)

    def route_between(self, source_name, destination_name):
        source = self.get_warehouse(source_name)
        destination = self.get_warehouse(destination_name)

        if source is None or destination is None:
            return

        return get_route_info(
            source.lat,
            source.lon,
            destination.lat,
            destination.lon
        )

    def route_between_customer(self, warehouse_name, customer_lat, customer_lon):
        warehouse = self.get_warehouse(warehouse_name)

        if warehouse is None:
            return

        return get_route_info(
            warehouse.lat,
            warehouse.lon,
            customer_lat,
            customer_lon
        )

    def print_network_inventory(self):
        for warehouse in self.warehouses.values():
            warehouse.print_inventory()
            print()

    def total_product_quantity(self, product_code):
        total = 0

        for warehouse in self.warehouses.values():
            total += warehouse.get_quantity(product_code)

        return total

    def __repr__(self):
        return f"WarehouseNetwork({len(self.warehouses)} warehouses)"