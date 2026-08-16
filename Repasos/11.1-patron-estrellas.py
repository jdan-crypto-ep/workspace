n = int(input("Ingresa patron: "))

# Método de Triangulo
# for i in range(1, n + 1):
#     for j in range(i):
#         print("*", end="")
#     print("")

# Forma Ascendente
# for i in range(1, n + 1):
#     print("*" * i)


# Forma Ascendente
for i in range(n, 0, -1):
    print("*" * i)
