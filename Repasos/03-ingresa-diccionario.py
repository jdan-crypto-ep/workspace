# DICCIONARIOS
# OBJETIVO
# crear y acceder a diccionarios
8


mi_diccionario = {}
limite = 3

while len(mi_diccionario) < limite:  # len cuenta cantidad de atributos
    nombre = input("ingresa el nombre del lenguaje: ")
    año = input("Ingresa el año de creación:  ")

    mi_diccionario[nombre] = año

# print(f"Lenguaje agregado. Total: {len(mi_diccionario)/{limite}}")


print(mi_diccionario)
