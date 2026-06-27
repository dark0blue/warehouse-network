from datetime import date, timedelta

from product import Product
from warehouse import Warehouse
from warehouse_network import WarehouseNetwork
from order_fulfillment import OrderFulfillmentService
from errors import BaseWarehouseException


def read_int(text):
    return int(input(text))


def read_float(text):
    return float(input(text))


def read_date(text):
    value = input(text)

    if value == "":
        return None

    return date.fromisoformat(value)


def read_items():
    items = {}

    print("Add items.")
    print("Empty product code stops.")

    while True:
        product_code = input("Product code: ")

        if product_code == "":
            break

        quantity = read_int("Quantity: ")
        items[product_code] = quantity

    return items


def show_warehouses(network):
    for warehouse in network.list_warehouses():
        print()
        print(warehouse)
        print(f"load: {warehouse.load_ratio() * 100:.2f}%")
        print(f"remaining volume: {warehouse.remaining_volume():.3f} m3")


def show_inventory(network):
    for warehouse in network.list_warehouses():
        print()
        print("=" * 40)
        print(warehouse.name)
        print("=" * 40)

        if len(warehouse.inventory) == 0:
            print("empty")
            continue

        for product_code, batches in warehouse.inventory.items():
            product = batches[0].product

            print()
            print(f"{product_code} - {product.name} - {product.category}")

            for batch in batches:
                print(
                    f"  quantity: {batch.quantity}, "
                    f"exp_date: {batch.exp_date}"
                )


def add_warehouse(network):
    name = input("Warehouse name: ")
    capacity = read_float("Capacity m3: ")
    lat = read_float("Latitude: ")
    lon = read_float("Longitude: ")

    warehouse = Warehouse(name, capacity, lat, lon)
    network.add_warehouse(warehouse)

    print("Warehouse added.")


def add_product_to_warehouse(network):
    warehouse_name = input("Warehouse name: ")
    warehouse = network.get_warehouse(warehouse_name)

    name = input("Product name: ")
    code = input("Product code: ")
    weight_kg = read_float("Weight kg: ")
    volume_m3 = read_float("Volume m3: ")
    category = input("Category or empty: ")
    quantity = read_int("Quantity: ")
    exp_date = read_date("Expiration date yyyy-mm-dd or empty: ")

    if category == "":
        category = "general"

    product = Product(name, code, weight_kg, volume_m3, category)
    warehouse.add_product(product, quantity, exp_date)

    print("Product added.")


def transfer_products(network):
    source = input("Source warehouse: ")
    destination = input("Destination warehouse: ")

    items = read_items()

    network.transfer_products(source, destination, items)

    print("Transfer done.")


def plan_order(network):
    customer_lat = read_float("Customer latitude: ")
    customer_lon = read_float("Customer longitude: ")

    items = read_items()

    service = OrderFulfillmentService(network)
    plan = service.plan_order(items, customer_lat, customer_lon)

    print_plan(plan)


def fulfill_order(network):
    customer_lat = read_float("Customer latitude: ")
    customer_lon = read_float("Customer longitude: ")

    items = read_items()

    service = OrderFulfillmentService(network)
    plan = service.fulfill_order(items, customer_lat, customer_lon)

    print_plan(plan)
    print("Order fulfilled.")


def print_plan(plan):
    print()
    print("=" * 40)
    print("PLAN")
    print("=" * 40)

    for item in plan:
        print(
            f"{item['warehouse_name']} -> "
            f"{item['product_code']} | "
            f"quantity: {item['quantity']} | "
            f"exp: {item['exp_date']} | "
            f"distance: {item['distance_km']:.2f} km | "
            f"days left: {item['days_left']} | "
            f"score: {item['score']:.2f}"
        )


def show_overloaded(network):
    warehouses = network.overloaded_warehouses()

    if len(warehouses) == 0:
        print("No overloaded warehouses.")
        return

    for warehouse in warehouses:
        print(
            f"{warehouse.name}: "
            f"{warehouse.load_ratio() * 100:.2f}% full"
        )


def redistribute(network):
    plan = network.redistribute_overloaded_warehouses()

    if len(plan) == 0:
        print("Nothing was redistributed.")
        return

    for item in plan:
        print(
            f"{item['from']} -> {item['to']} | "
            f"{item['product_code']} | "
            f"quantity: {item['quantity']} | "
            f"exp: {item['exp_date']}"
        )


def save_network(network):
    filename = input("Filename: ")
    network.save_to_file(filename)

    print("Saved.")


def load_network():
    filename = input("Filename: ")
    network = WarehouseNetwork.load_from_file(filename)

    print("Loaded.")
    return network


def print_menu():
    print()
    print("=" * 40)
    print("WAREHOUSE SYSTEM")
    print("=" * 40)
    print("1. Show warehouses")
    print("2. Show inventory")
    print("3. Add warehouse")
    print("4. Add product to warehouse")
    print("5. Transfer products")
    print("6. Plan order")
    print("7. Fulfill order")
    print("8. Show overloaded warehouses")
    print("9. Redistribute overloaded warehouses")
    print("10. Save network")
    print("11. Load network")
    print("0. Exit")


def main():
    network = WarehouseNetwork()

    while True:
        print_menu()

        choice = input("Choose: ")

        try:
            if choice == "1":
                show_warehouses(network)

            elif choice == "2":
                show_inventory(network)

            elif choice == "3":
                add_warehouse(network)

            elif choice == "4":
                add_product_to_warehouse(network)

            elif choice == "5":
                transfer_products(network)

            elif choice == "6":
                plan_order(network)

            elif choice == "7":
                fulfill_order(network)

            elif choice == "8":
                show_overloaded(network)

            elif choice == "9":
                redistribute(network)

            elif choice == "10":
                save_network(network)

            elif choice == "11":
                network = load_network()

            elif choice == "0":
                print("bye bye :D")
                break

            elif choice == "omg":
                network = load_demo_data()

            else:
                print("Invalid choice.")

        except BaseWarehouseException as error:
            print()
            print("Warehouse error:")
            print(error)

        except ValueError as error:
            print()
            print("Invalid input:")
            print(error)

        except Exception as error:
            print()
            print("Something went wrong:")
            print(error)










def load_demo_data():
    network = WarehouseNetwork()

    today = date.today()

    milk = Product("Milk", "Milk001", 1, 0.001, "dairy")
    bread = Product("Bread", "Bread001", 0.5, 0.003, "bakery")
    water = Product("Water", "Water001", 1.5, 0.0015, "drinks")
    cheese = Product("Cheese", "Cheese001", 0.3, 0.002, "dairy")

    sofia = Warehouse("Sofia", 6, 42.6977, 23.3219)
    plovdiv = Warehouse("Plovdiv", 8, 42.1354, 24.7453)
    varna = Warehouse("Varna", 8, 43.2141, 27.9147)
    burgas = Warehouse("Burgas", 7, 42.5048, 27.4626)

    network.add_warehouse(sofia)
    network.add_warehouse(plovdiv)
    network.add_warehouse(varna)
    network.add_warehouse(burgas)

    sofia.add_product(milk, 400, today + timedelta(days=8))
    sofia.add_product(milk, 600, today + timedelta(days=25))
    sofia.add_product(bread, 700, today + timedelta(days=4))
    sofia.add_product(water, 1200, today + timedelta(days=90))
    sofia.add_product(cheese, 400, today + timedelta(days=15))

    plovdiv.add_product(milk, 300, today + timedelta(days=12))
    plovdiv.add_product(bread, 400, today + timedelta(days=5))
    plovdiv.add_product(water, 800, today + timedelta(days=120))
    plovdiv.add_product(cheese, 200, today + timedelta(days=20))

    varna.add_product(milk, 500, today + timedelta(days=7))
    varna.add_product(bread, 300, today + timedelta(days=3))
    varna.add_product(water, 1000, today + timedelta(days=100))

    burgas.add_product(milk, 250, today + timedelta(days=18))
    burgas.add_product(bread, 250, today + timedelta(days=6))
    burgas.add_product(cheese, 150, today + timedelta(days=10))

    return network




            


if __name__ == "__main__":
    main()