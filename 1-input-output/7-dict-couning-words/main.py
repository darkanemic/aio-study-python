text = ("Я прохожу курсы на крутом сайте ‘AIO STUDY’. Тут я обучусь программированию на python и коду под web3. Это "
        "даст мне в дальнейшем сильный буст. Тут много домашки, что дает мне хорошую практику. Python - идеальный "
        "выбор. Всем успехов!")
text_cleaned = ''.join(char.lower() for char in text if char.isalnum() or char == ' ')
text_split = text_cleaned.split()
words_count = {}
for word in text_split:
    words_count[word] = words_count.get(word, 0) + 1
print(words_count)