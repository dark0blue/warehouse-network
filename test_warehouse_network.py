import unittest
from datetime import date

from product import Product
from warehouse import Warehouse
from warehouse_network import WarehouseNetwork
from errors import (
    ProductNotFoundError,
    InsufficientStockError,
    WarehouseCapacityError,
    InvalidQuantityError,
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


if __name__ == "__main__":
    unittest.main()