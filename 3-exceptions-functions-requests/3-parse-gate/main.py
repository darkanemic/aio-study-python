import requests

host = 'https://api.gateio.ws'
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/spot/order_book'
query_param = ('currency_pair=BTC_USDT', 'currency_pair=ETH_USDT', 'currency_pair=SOL_USDT')
for currency_pair in query_param:
    try:
        response = requests.request('GET', host + prefix + url + '?' + currency_pair, headers=headers)
        response.raise_for_status()
        print(response.json())
    except requests.exceptions.HTTPError as http_error:
        if http_error.response is not None:
            status_code = http_error.response.status_code
            if status_code == 400:
                print("Ошибка 400: Неверный запрос. Проверьте корректность параметров запроса.")
            elif status_code == 401:
                print("Ошибка 401: Неавторизованный доступ. Проверьте токен или учетные данные.")
            elif status_code == 404:
                print("Ошибка 404: Ресурс не найден.Проверьте правильность URL.")
            elif status_code == 429:
                print("Ошибка 429: Превышено количество запросов. Попробуйте снова позже или используйте прокси.")
            elif status_code == 500:
                print("Ошибка 500: Внутренняя ошибка сервера. Попробуйте снова позже.")
            elif status_code == 502:
                print("Ошибка 502: Неверный ответ шлюза. Возможно, сервер перегружен.")
            elif status_code == 503:
                print("Ошибка 503: Сервис временно недоступен. Сервер перегружен или на обслуживании.")
            elif status_code == 504:
                print("Ошибка 504: Превышено время ожидания ответа от шлюза.")
            else:
                print(f"Произошла HTTP ошибка с кодом {status_code}.")
        else:
            print(f"Ошибка HTTP {http_error}")
    except requests.exceptions.ConnectionError as error:
        print(f'Ошибка соединения: {error}')
    except requests.exceptions.Timeout as error:
        print(f'Превышено время ожидания: {error}')
    except requests.exceptions.RequestException as error:
        print(f'Произошла ошибка при попытке запроса: {error}')

