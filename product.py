class Product:
    def __init__(
        self,
        name: str,
        code: str,
        weight_kg: float,
        volume_m3: float,
        category: str = "general",
    ):
        self.name = name
        self.code = code
        self.weight_kg = weight_kg
        self.volume_m3 = volume_m3
        self.category = category

    def __repr__(self):
        return f"Product(name={self.name}, code={self.code})"