
import unittest
from datetime import date
from unittest.mock import mock_open, patch
import json

from product import Product
from warehouse import Warehouse
from warehouse_network import WarehouseNetwork
from errors import (
    ProductNotFoundError,
    InsufficientStockError,
    WarehouseCapacityError,
    InvalidQuantityError,
    DuplicateWarehouseError,
    WarehouseNotFoundError
)

class TestWarehouseNetwork(unittest.TestCase):

    def setUp(self):
        self.milk = Product("Milk", "Milk001", 1, 0.001)
        self.bread = Product("Bread", "Bread001", 0.5, 0.005)

        self.wh1 = Warehouse("Sofia", 10)
        self.wh2 = Warehouse("Varna", 10)
        self.wh3 = Warehouse("Dobrich", 0.001)

        self.network = WarehouseNetwork()
        self.network.add_warehouse(self.wh1)
        self.network.add_warehouse(self.wh2)
        self.network.add_warehouse(self.wh3)

        self.wh1.add_product(self.milk, 100)
        self.wh1.add_product(self.bread, 50)

    def test_transfer_products_successful(self):
        self.network.transfer_products(
            "Sofia",
            "Varna",
            {"Milk001": 30, "Bread001": 10}
        )

        self.assertEqual(self.wh1.get_quantity("Milk001"), 70)
        self.assertEqual(self.wh2.get_quantity("Milk001"), 30)

        self.assertEqual(self.wh1.get_quantity("Bread001"), 40)
        self.assertEqual(self.wh2.get_quantity("Bread001"), 10)

    def test_transfer_products_not_found(self):
        with self.assertRaises(ProductNotFoundError):
            self.network.transfer_products(
                "Sofia",
                "Varna",
                {"NOTDEFINED": 10}
            )

    def test_transfer_products_not_enough_quantity(self):
        with self.assertRaises(InsufficientStockError):
            self.network.transfer_products(
                "Sofia",
                "Varna",
                {"Milk001": 999}
            )

    def test_transfer_products_not_enough_destination_capacity(self):
        with self.assertRaises(WarehouseCapacityError):
            self.network.transfer_products(
                "Sofia",
                "Dobrich",
                {"Milk001": 2}
            )

    def test_transfer_products_negative_quantity(self):
        with self.assertRaises(InvalidQuantityError):
            self.network.transfer_products(
                "Sofia",
                "Varna",
                {"Milk001": -1}
            )

    def test_transfer_products_preserves_batches(self):
        self.wh1.inventory = {}
        self.wh1.add_product(self.milk, 10, date(2026, 6, 20))
        self.wh1.add_product(self.milk, 20, date(2026, 7, 20))

        self.network.transfer_products(
            "Sofia",
            "Varna",
            {"Milk001": 15}
        )

        batch1 = self.wh2.find_batch("Milk001", date(2026, 6, 20))
        batch2 = self.wh2.find_batch("Milk001", date(2026, 7, 20))

        self.assertIsNotNone(batch1)
        self.assertIsNotNone(batch2)

        self.assertEqual(batch1.quantity, 10)
        self.assertEqual(batch2.quantity, 5)

    def test_save_to_file(self):
        self.milk.category = "dairy"
        mocked_open = mock_open()

        with patch("builtins.open", mocked_open):
            self.network.save_to_file("ntwrk.json")

        mocked_open.assert_called_once_with("ntwrk.json", "w", encoding = "utf-8")

        saved_text = ""

        for call in mocked_open().write.call_args_list:
            saved_text += call.args[0]

        data = json.loads(saved_text)

        self.assertIn("warehouses", data)
        self.assertEqual(data["warehouses"][0]["name"], "Sofia")

        milk_batch = data["warehouses"][0]["inventory"]["Milk001"][0]

        self.assertEqual(milk_batch["quantity"], 100)
        self.assertEqual(milk_batch["product"]["category"],"dairy")

    def test_load_from_file(self):
            
        data = {
            "warehouses": [
                {
                    "name": "Sofia",
                    "capacity_m3": 10,
                    "lat": 42.6977,
                    "lon": 23.3219,
                    "inventory": {
                        "Milk001": [
                            {
                                "product": {
                                    "name": "Milk",
                                    "code": "Milk001",
                                    "weight_kg": 1,
                                    "volume_m3": 0.001,
                                    "category": "dairy"
                                },
                                "quantity": 15,
                                "exp_date": "2026-07-20"
                            }
                        ]
                    }
                }
            ]
        }

        mocked_open = mock_open(read_data=json.dumps(data))

        with patch("builtins.open", mocked_open):
            loaded_network = WarehouseNetwork.load_from_file("ntwrk.json")

        mocked_open.assert_called_once_with("ntwrk.json", "r", encoding = "utf-8")
        warehouse = loaded_network.get_warehouse("Sofia")
        batch = warehouse.find_batch("Milk001", date(2026, 7, 20))

        self.assertIsNotNone(batch)
        self.assertEqual(batch.quantity, 15)
        self.assertEqual(batch.product.name, "Milk")
        self.assertEqual(batch.product.category, "dairy")

    def test_add_duplicate_warehouse(self):
        duplicate = Warehouse("Sofia", 10)

        with self.assertRaises(DuplicateWarehouseError):
            self.network.add_warehouse(duplicate)

    def test_redistribution_moves_from_overloaded(self):
        product = Product("Box", "Box001", 1, 1)

        source = Warehouse("Sofia", 100)
        destination = Warehouse("Varna", 100)

        network = WarehouseNetwork()
        network.add_warehouse(source)
        network.add_warehouse(destination)

        source.add_product(product, 90, date(2027, 1, 1))


        with patch.object(network, "route_between") as mocked_route:
            mocked_route.return_value = {"distance_km": 100, "duration_h": 2}
            plan = network.redistribute_overloaded_warehouses()

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["from"], "Sofia")
        self.assertEqual(plan[0]["to"], "Varna")
        self.assertEqual(plan[0]["product_code"], "Box001")
        self.assertEqual(plan[0]["quantity"], 15)
        self.assertEqual(source.get_quantity("Box001"), 75)
        self.assertEqual(destination.get_quantity("Box001"), 15)

    def test_no_redistribution_if_no_space(self):
        product = Product("Box", "Box001", 1, 1)

        source = Warehouse("Sofia", 100)
        destination = Warehouse("Varna", 1)

        network = WarehouseNetwork()
        network.add_warehouse(source)
        network.add_warehouse(destination)

        source.add_product(product, 90, date(2027, 1, 1))
        destination.add_product(product, 1, date(2027, 1, 1))

        with patch.object(network, "route_between") as mocked_routes:
            mocked_routes.return_value = {"distance_km": 100, "duration_h": 2}
            plan = network.redistribute_overloaded_warehouses()

        self.assertEqual(plan, [])
        self.assertEqual(source.get_quantity("Box001"), 90)
        self.assertEqual(destination.get_quantity("Box001"), 1)

    def test_get_missing_warehouse(self):
        with self.assertRaises(WarehouseNotFoundError):
            self.network.get_warehouse("omggggggggggggggggggg")

if __name__ == "__main__":
    unittest.main()