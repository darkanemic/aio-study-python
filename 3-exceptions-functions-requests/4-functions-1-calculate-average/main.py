def check_is_numbers(numbers_for_check):
    return all(isinstance(num, (int, float)) for num in numbers_for_check)


def calculate_average(numbers_to_calculate):
    return sum(numbers_to_calculate) / len(numbers_to_calculate)


numbers = [100, 200, 300, 400, 'не число!']
if numbers:
    if check_is_numbers(numbers):
        print(f'Среднее арифметическое данного списка: {calculate_average(numbers)}')
    else:
        print('Не все элементы в списке являются числами, поэтому посчитать среднее арифметическое не возможно.')
else:
    print('Список пуст. Для подсчета среднего арифметического, заполните список числами.')
