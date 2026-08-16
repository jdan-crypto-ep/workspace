# Cuadrado de un numero
# OBJETIVO
# Introducir funciones, argumentos y valores de retorno

# Estudiante
# num = int(input("introduce un ńumero: "))
# cuadrado = num * num
# print(f"el cuadrado de {num} es {cuadrado}")


# Maestro
def cuadrado_num(num):
    return num**2


num = int(input("ingresa un numero para calcular su cuadrado:  "))
print(f"El cuadrado de {num} es {cuadrado_num(num)}")
