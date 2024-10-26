class Vehicle:
    def __init__(self, make, model, year):
        self.make = make
        self.model = model
        self.year = year

    def get_info(self):
        return f"Марка: {self.make}, Модель: {self.model}, Год: {self.year}"


class Car(Vehicle):
    def start_engine(self):
        print(f"Машина {self.model} завелась!")


class Bicycle(Vehicle):

    def ring_bell(self):
        print(f"Звенит звонок велосипеда {self.model}!")


vehicle = Vehicle("Москвич", "412", "1977")
cybertruck = Car("Tesla", "Cybertruck", "2023")
orlenok = Bicycle("Вайрас", "Орлёнок", "1962")
print(vehicle.get_info())
print(cybertruck.get_info())
cybertruck.start_engine()
print(orlenok.get_info())
orlenok.ring_bell()
