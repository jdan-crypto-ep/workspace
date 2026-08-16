# Obejetivo
# crear lista, iteración básica y el uso de funciones integradas


# Solicitar numero
num = int(input("Introduce el numero final de la lista: "))
lista = list(range(1, num + 1))  # range crea una secuencia desde 1
resultado = sum(lista)  # calcula la suma de la lista
print(f"la suma de la lista hasta {num} es {resultado}")
