# Crear un diccionario para contar la cantidad de veces que aparece cada carácter en
# una cadena
# Objetivo: Enseñar el uso de diccionarios y la iteración sobre cadenas.


cadena = "abracadabra"

conteos = {}

for char in cadena:
    if char in conteos:
        conteos[char] += 1
    else:
        conteos[char] = 1


print(conteos)
