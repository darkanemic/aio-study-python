with open('input.txt', 'r') as file:
    data = file.read()
    replaced_data = data.replace(" ", "_")

with open('output', 'w') as file:
    file.write(replaced_data)