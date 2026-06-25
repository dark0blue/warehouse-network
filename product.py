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

    def to_dict(self):
        return {
            "name": self.name,
            "code": self.code,
            "weight_kg": self.weight_kg,
            "volume_m3": self.volume_m3
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data["code"],
            data["weight_kg"],
            data["volume_m3"]
        )

    def __repr__(self):
        return f"Product(name = {self.name}, code = {self.code})"
    
