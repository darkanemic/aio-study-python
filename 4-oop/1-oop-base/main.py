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


fruit = Fruit(name="Фрукт")
print(fruit.get_name())

apple = Apple(name="Яблоко")
print(apple.get_name())
apple.taste()

banana = Banana(name="Банан")
print(banana.get_name())
banana.taste()
