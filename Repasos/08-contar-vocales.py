# Contar el número de vocales en una cadena de texto
# Objetivo: Practicar bucles, condicionales y trabajar con cadenas.
caracteres = input("ingresa palabra:  ")
contador = 0

for caracter in caracteres:
    if caracter == "a":
        contador += 1
    elif caracter == "e":
        contador += 1
    elif caracter == "i":
        contador += 1
    elif caracter == "o":
        contador += 1
    elif caracter == "u":
        contador += 1

print(f"En la palabra {caracteres} hay {contador} vocales")

# Mejor VERSION MAESTRO

# Definir vocales
vocales = "aeiouAEIOU"
cadena = input("Introduce una palabra  ")
contador_vocales = 0
# usar bucle para contar
for letra in cadena:
    if letra in vocales:
        contador_vocales += 1

print(f"El número de vocales en la palabra {cadena} es {contador_vocales}")
