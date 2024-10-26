import asyncio
import random
import time


async def multiplication_by_two(number, pause_time):
    await asyncio.sleep(pause_time)
    result = number * 2
    return result


async def main():
    numbers_list = [1, 2, 3, 4, 5]
    tasks = []

    # Создадим список задержек, чтоб асинхронный и синхронный вариант запускались с одинаковыми задержками
    pauses_list = []
    for index in range(0, len(numbers_list)):
        pauses_list.append(random.randint(1, 3))

    # Замерим асинхронное выполнение
    asynchronous_start_time = time.time()
    for number in range(0, len(numbers_list)):

        tasks.append(
            asyncio.create_task(
                multiplication_by_two(numbers_list[number], pauses_list[number])
            )
        )
    multiplications_results = await asyncio.gather(*tasks)
    asynchronous_execution_time = round(time.time() - asynchronous_start_time)
    print(
        f"В асинхронном режиме получили результаты: {multiplications_results} за {asynchronous_execution_time} сек."
    )

    # Замерим последовательное выполнение. Сделаем await для самих корутиных функций, не создавая таски, это приведёт
    # к их исполнению в синхронном режиме
    synchronous_start_time = time.time()
    for number in range(0, len(numbers_list)):
        await multiplication_by_two(numbers_list[number], pauses_list[number])
    synchronous_execution_time = round(time.time() - synchronous_start_time)
    print(
        f"В последовательном режиме получили результаты: {multiplications_results} за {synchronous_execution_time} сек."
    )

    # Подведём итоги
    acceleration_time = synchronous_execution_time - asynchronous_execution_time
    print(
        f"Таким образом благодаря использованию асинхронности мы ускорили наши расчеты на {acceleration_time} сек."
    )


if __name__ == "__main__":
    asyncio.run(main())
