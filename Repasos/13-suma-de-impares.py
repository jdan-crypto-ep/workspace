# Encontrar la suma de todos los números impares entre 1 y 50
# Objetivo: Usar bucles y condicionales para filtrar y sumar valores.

suma = 0

for i in range(1, 51):
    if i % 2 != 0:
        suma += i

print(suma)
