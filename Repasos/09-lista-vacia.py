# Crear una función que verifique si una lista está vacía
# Objetivo: Introducir funciones, operaciones con listas y condicionales


lis_1 = [1, 2]


def verificar(lista):
    if lista == []:
        print("Lista esta vacia")
    else:
        print("Lista contiene datos")


# verificar(lis_1)

# Metodo 2 Maestro


def lista_vacia(lista):
    return len(lista) == 0


print(f"La lista está vacia? {lista_vacia(lis_1)}")
