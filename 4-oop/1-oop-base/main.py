class Fruit:
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name


class Apple(Fruit):
    def taste(self):
        print(f'{self.name} сладкое.')


class Banana(Fruit):
    def taste(self):
        print(f'{self.name} мягкий.')


# Создание экземпляра класса Fruit
fruit = Fruit(name="Фрукт")
print(fruit.get_name())  # Вывод: Фрукт

# Создание экземпляра класса Apple
apple = Apple(name="Яблоко")
print(apple.get_name())  # Вывод: Яблоко
apple.taste()  # Вывод: Яблоко сладкое

# Создание экземпляра класса Banana
banana = Banana(name="Банан")
print(banana.get_name())  # Вывод: Банан
banana.taste()  # Вывод: Банан мягки
