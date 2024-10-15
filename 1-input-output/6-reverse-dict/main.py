original_dict = {'apple': 'fruit', 'carrot': 'vegetable', 'banana': 'fruit'}
reverse_dict = {}
for key, value in original_dict.items():
    reverse_dict[value] = key
print(reverse_dict)
