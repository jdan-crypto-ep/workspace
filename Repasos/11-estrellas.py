# Usar un bucle para imprimir un patrón de estrellas
# Objetivo: Practicar bucles anidados y la creación de patrones.

patron = int(input("Ingresa numero de extrellas: "))
contador = 0
estrellas = ""

while contador < patron:
    estrellas = estrellas + "*"
    contador += 1

print(estrellas)
