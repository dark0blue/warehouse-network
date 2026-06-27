import unittest
from datetime import date, timedelta
from unittest.mock import patch

from warehouse import Warehouse
from product import Product

from warehouse_network import WarehouseNetwork
from order_fulfillment import OrderFulfillmentService, TransportCostWasteStrategy, ClosestThenOldestStrategy

from errors import OrderCannotBeFulfilledError, InvalidQuantityError


class TestOrderFulfillment(unittest.TestCase):
    def setUp(self):
        self.milk = Product("Milk", "Milk001", 1, 0.001)
        self.bread = Product("Bread", "Bread001", 0.5, 0.005)

        self.sofia = Warehouse("Sofia", 10, 42.68, 23.32)
        self.varna = Warehouse("Varna", 10, 43.21, 27.91)
        self.network = WarehouseNetwork()
        self.network.add_warehouse(self.sofia)
        self.network.add_warehouse(self.varna)

        self.service = OrderFulfillmentService(self.network)

        self.today = date.today()
        self.old_exp = self.today + timedelta(days=5)
        self.expired = self.today - timedelta(days=1)
        self.new_exp = self.today + timedelta(days = 30)

    def test_plan_order_simple(self):
        self.sofia.add_product(self.milk, 20, self.new_exp)

        with patch.object(self.network, "route_between_customer") as mocked_route:
            mocked_route.return_value = {"distance_km": 10, "duration": 1}
            plan = self.service.plan_order({"Milk001": 5}, 1, 1)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["warehouse_name"], "Sofia")
        self.assertEqual(plan[0]["product_code"], "Milk001")
        self.assertEqual(plan[0]["quantity"], 5)

        self.assertEqual(self.sofia.get_quantity("Milk001"), 20)

    def test_fulfill_order_simple(self):
        self.sofia.add_product(self.milk, 20, self.new_exp)
        with patch.object(self.network, "route_between_customer") as mocked_route:
            mocked_route.return_value = {"distance_km": 10, "duration": 1}
            plan = self.service.fulfill_order({"Milk001": 7}, 1, 1)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["quantity"], 7)
        self.assertEqual(self.sofia.get_quantity("Milk001"), 13)

    def test_order_uses_old_batches_first(self):
        self.sofia.add_product(self.milk, 10, self.new_exp)
        self.sofia.add_product(self.milk, 10, self.old_exp)

        with patch.object(self.network, "route_between_customer") as mocked_route:
            mocked_route.return_value = {"distance_km": 10, "duration_h": 1}
            plan = self.service.plan_order({"Milk001": 12}, 6, 7)

        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["exp_date"], self.old_exp)
        self.assertEqual(plan[0]["quantity"], 10)
        self.assertEqual(plan[1]["exp_date"], self.new_exp)
        self.assertEqual(plan[1]["quantity"], 2)

    def test_fulfill_order_removes_from_correct_batches(self):
        self.sofia.add_product(self.milk, 10, self.old_exp)
        self.sofia.add_product(self.milk, 10, self.new_exp)

        with patch.object(self.network, "route_between_customer") as mocked_route:
            mocked_route.return_value = {"distance_km": 10, "duration_h": 1}
            self.service.fulfill_order({"Milk001": 12}, 1, 1)

        old_batch = self.sofia.find_batch("Milk001", self.old_exp)
        new_batch = self.sofia.find_batch("Milk001", self.new_exp)

        self.assertIsNone(old_batch)
        self.assertIsNotNone(new_batch)
        self.assertEqual(new_batch.quantity, 8)

    def test_order_not_enough_stock(self):
        self.sofia.add_product(self.milk, 3, self.new_exp)

        with patch.object(self.network, "route_between_customer") as mocked_route:
            mocked_route.return_value = {"distance_km": 10, "duration_h": 1}
            with self.assertRaises(OrderCannotBeFulfilledError):
                self.service.plan_order({"Milk001": 100}, 1, 1)

    def test_order_negative_quantity(self):
        with self.assertRaises(InvalidQuantityError):
            self.service.plan_order({"Milk001": -100}, 1, 1)

    def test_closest_then_oldest_strat(self):
        milk = Product("Milk", "Milk001", 1, 0.001)
        today = date.today()
        old_exp = today + timedelta(days = 2)
        new_exp = today +timedelta(days = 30)

        close = Warehouse("Close", 10, 42, 23)
        far = Warehouse("Far", 10, 43, 24)

        network = WarehouseNetwork()
        network.add_warehouse(close)
        network.add_warehouse(far)

        close.add_product(milk, 10, new_exp)
        far.add_product(milk, 10, old_exp)

        service = OrderFulfillmentService(network, strategy=ClosestThenOldestStrategy())
        def fake_route(name, c_lat, c_lon):
            distances = {"Close": 10, "Far": 40}

            return {"distance_km": distances[name], "duration_h": 1}
        
        with patch.object(network, "route_between_customer", side_effect = fake_route):
            plan = service.plan_order({"Milk001": 5}, 42, 23)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["warehouse_name"], "Close")
        self.assertEqual(plan[0]["exp_date"], new_exp)

    def test_transport_cost_waste_strat(self):
        old_exp = self.today + timedelta(days = 2)
        new_exp = self.today + timedelta(days = 30)

        close = Warehouse("Close", 10, 42, 23)
        far = Warehouse("Far", 10, 43, 24)

        network = WarehouseNetwork()
        network.add_warehouse(close)
        network.add_warehouse(far)

        close.add_product(self.milk, 10, new_exp)
        far.add_product(self.milk, 10, old_exp)

        service = OrderFulfillmentService(network, strategy=TransportCostWasteStrategy())

        def fake_route(name, c_lat, c_lon):
            distances = {"Close": 10, "Far": 40}
            return {"distance_km": distances[name], "duration_h": 1}
        
        with patch.object(network, "route_between_customer", side_effect = fake_route):
            plan = service.plan_order({"Milk001": 5}, 42, 23, k=2)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["warehouse_name"], "Far")
        self.assertEqual(plan[0]["exp_date"], old_exp)
        


if __name__ == "__main__":
    unittest.main()
