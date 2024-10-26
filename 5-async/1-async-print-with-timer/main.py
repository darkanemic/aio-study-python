import asyncio
import random
import time


async def send_message(message, pause_time):
    print(message)
    await asyncio.sleep(pause_time)
    return pause_time


async def main():
    message_list = ["Привет!", "Как дела?", "До свидания!"]
    tasks = []
    for message in range(0, len(message_list)):
        pause_time = random.randint(1, 3)
        tasks.append(
            asyncio.create_task(send_message(message_list[message], pause_time))
        )
    tasks_start_time = time.time()
    tasks_delays = await asyncio.gather(*tasks)
    asynchronous_execution_time = time.time() - tasks_start_time
    sequence_execution_time = 0
    for index, task_delay in enumerate(tasks_delays, 1):
        print(f"Время выполнения задачи №{index} заняло: {task_delay} секунд(ы)")
        sequence_execution_time += task_delay

    print(
        f"Последовательное выполнение этих задач заняло бы {sequence_execution_time} секунд(ы)"
    )
    print(
        f"Но благодаря применению асинхронности выполнение этих задач заняло: {round(asynchronous_execution_time)} "
        f"секунд(ы)"
    )


if __name__ == "__main__":
    asyncio.run(main())
