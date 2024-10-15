while True:
    try:
        path = input('Введити путь к файлу: ')
        with open(path, 'r') as file:
            data = file.read()
    except FileNotFoundError:
        print('Файл по указанному пути не найден. Пожалуйста, проверьте путь и повторите попытку.')
    else:
        print(f'Файл {path} найден успешно!')
        break
