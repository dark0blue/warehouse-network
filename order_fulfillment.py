from abc import ABC, abstractmethod
from datetime import date

from warehouse_network import WarehouseNetwork
from errors import (
    InvalidQuantityError,
    OrderCannotBeFulfilledError,
)


class FulfillmentStrategy(ABC):
    @abstractmethod
    def create_plan(self, service, order, customer_lat, customer_lon, k):
        pass


class TransportCostWasteStrategy(FulfillmentStrategy):
    def create_plan(self, service, order, customer_lat, customer_lon, k):
        return service.create_greedy_plan(
            order,
            customer_lat,
            customer_lon,
            k,
            sort_key=lambda item: item["score"]
        )


class ClosestThenOldestStrategy(FulfillmentStrategy):
    def create_plan(self, service, order, customer_lat, customer_lon, k):
        return service.create_greedy_plan(
            order,
            customer_lat,
            customer_lon,
            k,
            sort_key=lambda item: (
                item["distance_km"],
                item["days_left"]
            )
        )





class OrderFulfillmentService:
    def __init__(self, network: WarehouseNetwork, strategy: FulfillmentStrategy | None = None):
        self.network = network
        self.strategy = strategy or ClosestThenOldestStrategy()

    def available_batches(self, product_code: str, customer_lat: float, customer_lon: float, k: float = 2.0):
        today = date.today()

        for warehouse in self.network.list_warehouses():
            if product_code not in warehouse.inventory:
                continue

            route = self.network.route_between_customer(
                warehouse.name,
                customer_lat,
                customer_lon
            )

            distance_km = route["distance_km"]

            for batch in warehouse.inventory[product_code]:
                days_left = (batch.exp_date - today).days if batch.exp_date else 9999

                if days_left < 0:
                    continue

                score = distance_km + k * days_left

                yield {
                    "warehouse": warehouse,
                    "batch": batch,
                    "distance_km": distance_km,
                    "days_left": days_left,
                    "score": score,
                }

    def create_greedy_plan(
        self,
        order: dict[str, int],
        customer_lat: float,
        customer_lon: float,
        k: float,
        sort_key
    ):
        plan = []

        for product_code, wanted_quantity in order.items():
            if wanted_quantity <= 0:
                raise InvalidQuantityError(
                    f"Invalid order quantity {wanted_quantity} for product '{product_code}'. "
                    f"Quantity must be positive."
                )

            candidates = list(
                self.available_batches(
                    product_code,
                    customer_lat,
                    customer_lon,
                    k
                )
            )

            candidates.sort(key=sort_key)

            remaining = wanted_quantity

            for item in candidates:
                if remaining == 0:
                    break

                batch = item["batch"]
                taken = min(batch.quantity, remaining)

                plan.append({
                    "warehouse_name": item["warehouse"].name,
                    "product_code": product_code,
                    "quantity": taken,
                    "exp_date": batch.exp_date,
                    "distance_km": item["distance_km"],
                    "days_left": item["days_left"],
                    "score": item["score"],
                    "algorithm": self.strategy.__class__.__name__
                })

                remaining -= taken

            if remaining > 0:
                available_quantity = wanted_quantity - remaining

                raise OrderCannotBeFulfilledError(
                    f"Cannot fulfill order for product '{product_code}'. "
                    f"Requested: {wanted_quantity}, available: {available_quantity}, "
                    f"missing: {remaining}."
                )

        return plan

    def plan_order(
        self,
        order: dict[str, int],
        customer_lat: float,
        customer_lon: float,
        k: float = 2.0
    ):
        return self.strategy.create_plan(
            self,
            order,
            customer_lat,
            customer_lon,
            k
        )

    def fulfill_order(
        self,
        order: dict[str, int],
        customer_lat: float,
        customer_lon: float,
        k: float = 2.0
    ):
        plan = self.plan_order(order, customer_lat, customer_lon, k)

        for item in plan:
            warehouse = self.network.get_warehouse(item["warehouse_name"])

            warehouse.remove_from_batch(
                item["product_code"],
                item["exp_date"],
                item["quantity"]
            )

        return plan