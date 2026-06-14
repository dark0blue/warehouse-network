from abc import ABC, abstractmethod
from datetime import date


class FulfillmentStrategy(ABC):
    @abstractmethod
    def create_plan(self, service, order, customer_lat, customer_lon, k):
        pass


class WeightedDistanceExpirationStrategy(FulfillmentStrategy):
    def create_plan(self, service, order, customer_lat, customer_lon, k):
        return service._create_greedy_plan(
            order,
            customer_lat,
            customer_lon,
            k,
            sort_key=lambda item: item["score"]
        )


class ClosestThenOldestStrategy(FulfillmentStrategy):
    def create_plan(self, service, order, customer_lat, customer_lon, k):
        return service._create_greedy_plan(
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
    def __init__(self, network, strategy=None):
        self.network = network
        self.strategy = strategy or WeightedDistanceExpirationStrategy()

    def available_batches(self, product_code, customer_lat, customer_lon, k=2):
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
                if batch.exp_date is None:
                    days_left = 9999
                else:
                    days_left = (batch.exp_date - today).days

                if days_left < 0:
                    continue

                score = distance_km + k * days_left

                yield {
                    "warehouse": warehouse,
                    "batch": batch,
                    "distance_km": distance_km,
                    "days_left": days_left,
                    "score": score
                }

    def _create_greedy_plan(self, order, customer_lat, customer_lon, k, sort_key):
        plan = []

        for product_code, wanted_quantity in order.items():
            if wanted_quantity <= 0:
                print("Invalid quantity")
                return

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
                print(f"Cannot fulfill order for {product_code}")
                print(f"Missing quantity: {remaining}")
                return

        return plan

    def plan_order(self, order, customer_lat, customer_lon, k=2):
        return self.strategy.create_plan(
            self,
            order,
            customer_lat,
            customer_lon,
            k
        )

    def fulfill_order(self, order, customer_lat, customer_lon, k=2):
        plan = self.plan_order(order, customer_lat, customer_lon, k)

        if plan is None:
            return

        for item in plan:
            warehouse = self.network.get_warehouse(item["warehouse_name"])
            warehouse.remove_product(
                item["product_code"],
                item["quantity"]
            )

        return plan

    @staticmethod
    def print_plan(plan):
        if plan is None:
            return

        print("Order fulfillment plan:")

        for item in plan:
            print(
                f"{item['warehouse_name']} -> "
                f"{item['product_code']} | "
                f"quantity: {item['quantity']} | "
                f"exp: {item['exp_date']} | "
                f"distance: {item['distance_km']:.2f} km | "
                f"days left: {item['days_left']} | "
                f"score: {item['score']:.2f} | "
                f"{item['algorithm']}"
            )