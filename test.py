class FiveError(Exception):
    print("Деление на 5 недопустимо")
    pass


def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Деление на ноль недопустимо")
    if b == 5:
        raise FiveError("Не хочу делить на 5")
    return a / b


try:
    result = divide(10, 5)
except ZeroDivisionError as e:
    print(e)
except FiveError as e:
    print(e)