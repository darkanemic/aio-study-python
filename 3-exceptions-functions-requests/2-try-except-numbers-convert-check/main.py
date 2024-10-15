while True:
    try:
        input_number = input('Введите число: ')
        output_number = int(input_number)
    except ValueError:
        print('Ошибка: введенное значение не является числом. Попробуйте еще раз.')
    except TypeError:
        print('Ошибка: введенное значение не является числом. Попробуйте еще раз.')
    else:
        print(f'Ваши данные успешно преобразованы в число {output_number}.')
        break
