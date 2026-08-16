# CREAR LISTA DE PARES
# Objetivo
# Bucles (for y lógica condicional)

# Estudiante

lista_1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

lista_par = []

for lista in lista_1:
    if lista % 2 == 0:
        lista_par.append(lista)

print(lista_par)

# Maestro
lista_pares = []
for num in range(1, 21):
    if num % 2 == 0:
        lista_pares.append(num)

print(lista_pares)
