class BaseWarehouseException(Exception):
    def __init__(self, message = ""):
        super().__init__(message)

class ProductNotFoundError(BaseWarehouseException):
    pass

class WarehouseNotFoundError(BaseWarehouseException):
    pass

class InvalidQuantityError(BaseWarehouseException):
    pass

class InsufficientStockError(BaseWarehouseException):
    pass

class WarehouseCapacityError(BaseWarehouseException):
    pass

class DuplicateWarehouseError(BaseWarehouseException):
    pass

class BatchNotFoundError(BaseWarehouseException):
    pass

class OrderCannotBeFulfilledError(BaseWarehouseException):
    pass

class OptimizationError(BaseWarehouseException):
    pass

class RoutingError(BaseWarehouseException):
    pass


