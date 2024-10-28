iterations = 0

for i in range(1, 100):
    iterations += 1
    for k in range(1, 5):
        iterations += 1
print(iterations)

for i in range(1, 5):
    iterations += 1
    for k in range(1, 100):
        iterations += 1
print(iterations)
