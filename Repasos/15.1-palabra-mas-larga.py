# Encontrar la longitud de la palabra más larga en una lista
# Objetivo: Enseñar la iteración sobre listas y
# el cálculo de la longitud de cadenas

n1 = input("Ingresa palabra: ")
n2 = input("Ingresa palabra: ")
n3 = input("Ingresa palabra: ")
lista = []
lista.append(n1)
lista.append(n2)
lista.append(n3)
print(lista)

palabra_larga = max(lista, key=len)

print(f"La palabra mas larga es {palabra_larga}")
