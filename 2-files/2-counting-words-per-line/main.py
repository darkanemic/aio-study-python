with open('input.txt', 'r') as file:
    for line_number, line in enumerate(file, start=1):
        words = line.split()
        long_words_count = len([word for word in words if len(word) > 2])
        print(f"В {line_number} строке {long_words_count} слов(а)")