# : Usar un bucle para imprimir la secuencia de Fibonacci hasta el décimo término
# Objetivo: Practicar la iteración con bucles y la generación de secuencias.

# n1, n2 = 0, 1

# for i in range(10):
#     print(n1, end=(", "))
#     num = n1 + n2
#     n1 = n2
#     n2 = num

n = int(input("ingresa la posicion de la serie a mostrar: "))
lista = []
n1 = 0
n2 = 1

for i in range(0, n):
    lista.append(n1)
    num = n1 + n2
    n1 = n2
    n2 = num
print(lista)
