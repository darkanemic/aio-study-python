while True:
    a = input('Введите число A: ')
    if a.isdigit():
        a = int(a)
        break
    else:
        print('Требуется ввести числовое значение.')
while True:
    b = input('Введите число B: ')
    if b.isdigit():
        b = int(b)
        break
    else:
        print('Требуется ввести числовое значение.')

valid_operations = ['+', '-', '/', '*']

while True:
    action = input(f'Выберите операцию которая будет применена к числам {valid_operations}')
    if action in valid_operations:
        break
    else:
        print(f'Недопустимая арифметическая операция. Пожалуйста выберите одну из {valid_operations}')

division_by_zero = False

if action == '+':
    result = a + b
if action == '-':
    result = a - b
if action == '/':
    if b != 0:
        result = a / b
    else:
        print('Нельзя делить на ноль.')
        division_by_zero = True
if action == '*':
    result = a * b

if division_by_zero:
    print('Запустите программу заново и введите коректные значения.')
else:
    print(f'Результат {a} {action} {b} = {result}')