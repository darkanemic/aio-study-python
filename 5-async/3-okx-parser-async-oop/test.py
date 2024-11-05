import timeit


def fast_function():
    total = 0
    for i in range(1000):
        total += i
    return total


def slow_function():
    total = 0
    for i in range(1000000):
        total += i
    return total


# Замер времени для fast_function
fast_time = timeit.timeit(fast_function, number=100)
print(f"Среднее время выполнения fast_function за 100 запусков: {fast_time:.5f} секунд")

# Замер времени для slow_function
slow_time = timeit.timeit(slow_function, number=100)
print(f"Среднее время выполнения slow_function за 100 запусков: {slow_time:.5f} секунд")

# Сравнение
if fast_time < slow_time:
    print("fast_function быстрее slow_function")
else:
    print("slow_function быстрее fast_function")
