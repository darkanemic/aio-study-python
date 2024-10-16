def clean_text(text_to_clean):
    return ''.join(char.lower() for char in text_to_clean if char.isalnum())


def is_palindrome(text_to_check):
    reverse = text_to_check[::-1]
    return text_to_check == reverse


income_text = input('Введите строку и мы проверим является ли она: ')
if is_palindrome(clean_text(income_text)):
    print('Даная строка является палидромом.')
else:
    print('Данная строка не палиндром.')
