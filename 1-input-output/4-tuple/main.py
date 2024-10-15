numbers = []
print('Введите 5 чисел.')
for i in range(5):
    while True:
        push = input(f'Введите число №{i+1}: ')
        if push.isdigit():
            push = int(push)
            break
        else:
            print('Требуется ввести числовое значение.')
    numbers.append(push)
tuple_numbers = (numbers)
print(f'Первый элемент кортежа {tuple_numbers[0]}')
print(f'Длина кортежа: {len(tuple_numbers)}')
print(f'Сумма всех чисел в кортеже: {sum(tuple_numbers)}')
searched_number = int(input('Введите число для поиска: '))
if searched_number in tuple_numbers:
    print(f'Искомое число {searched_number} найдено в кортеже. Его индекс: {tuple_numbers.index(searched_number)} ')
else:
    print('Искомое число не найдено в кортеже')