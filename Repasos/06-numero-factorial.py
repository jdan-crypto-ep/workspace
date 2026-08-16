# Numero Factorial
# n! = n * (n-1) * (n-2) * ... * 2 * 1
# OBEJETIVO
# Bucle While


num = int(input("Ingresa un número:  "))
factorial = num
contador = 1

if num == 0:
    print(f"El factorial de {num} es 1")
elif num < 0:
    print(f"El factorial de {num} no existe, usa números enteros")
else:
    while contador < num:
        factorial *= num - contador
        contador = contador + 1
    print(f"El factorial de {num} es {factorial}")
