"""Data models."""


class User:
    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}"


class Admin(User):
    def __init__(self, name: str, level: int):
        super().__init__(name)
        self.level = level

    def permissions(self) -> list:
        return ["read", "write", "admin"]
