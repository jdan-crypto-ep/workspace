# Escribir una función para verificar si una cadena es un palíndromo
# Objetivo: Introducir la manipulación de cadenas y la comparación de texto.


def eliminar_espacios(cadena):
    sin_espacios = ""
    for char in cadena:
        if char != " ":
            sin_espacios += char
    return sin_espacios.lower()


def invertir_cadena(sin_espacios):
    reverse = ""
    for char in sin_espacios:
        reverse = char + reverse
    return reverse.lower()


def comparar(cadena):
    sin_espacios = eliminar_espacios(cadena)
    reverse = invertir_cadena(sin_espacios)

    if sin_espacios == reverse:
        print("Es palindromo")
    else:
        print("No es palindromo")


cadena = input("Ingresa cadena: ")
comparar(cadena)
