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
print(f'Получился список {numbers}')
print(f'Сумма всех чисел : {sum(numbers)}')
print(f'Максимальное число в списке : {max(numbers)}')
print(f'Минимальное число в списке : {min(numbers)}')