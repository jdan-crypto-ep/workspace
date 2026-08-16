#  Encontrar el número máximo en una lista sin usar funciones incorporadas
# Objetivo: Enseñar cómo iterar a través de una lista y comparar valores.

lista_1 = [1, 2, 3, 7, 5]
max_num = 0

for num in lista_1:
    if num >= max_num:
        max_num = num

print(f"El número máximo es {max_num}")
