import callejero as c
import osmnx as ox
import networkx as nx
import pandas as pd
import re
from typing import Tuple
import os
import time
from math import sqrt
GPS = """
   _____  _____    _____    _____ __     __
  / ____||  __ \  / ____|  |  __ \\ \   / /
 | |  __ | |__) || (___    | |__) |\ \_/ / 
 | | |_ ||  ___/  \___ \   |  ___/  \   /  
 | |__| || |      ____) |_ | |       | |   
  \_____||_|     |_____/(_)|_|       |_|   
                                           
                                           

"""
def step_with_header(step_message, function_to_call=None, *args, **kwargs):
    """
    Muestra el encabezado "GPS" y un mensaje, luego ejecuta una función si es necesario.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print(GPS)   # Imprime el encabezado estático
    print(step_message)  # Muestra el mensaje del paso actual
    if function_to_call:
        result = function_to_call(*args, **kwargs)  # Llama a la función con los argumentos proporcionados
        return result

def check_input(ubi_input:str):
    while "," not in ubi_input: 
        print("El formato debe de ser: 'Calle,número")
        while "," in ubi_input and (not ubi_input.split(",")[1].isnumeric()):
            print("El número a introducir debe de ser un número")
        ubi_input = input("Introduce la ubicación de nuevo: ")

    return ubi_input
def seleccion_interactiva(streetmap:pd.DataFrame):
    path_file = "results/latest_results.txt"
    directory = os.path.dirname(path_file) 

    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.isfile(path_file):
        with open(path_file, "w") as file:
            pass 
    print("Ubicaciones buscadas recientemente...")
    with open(path_file, "r") as p:
        for line in p.readlines()[::-1]:
            print(line.rstrip())
    ubications = ["inicio", "final"]
    coords = []
    for ubication in ubications:
        ubi_input = input(f"Introduce la ubicacion {ubication} en el formato 'Calle,Número' (ejemplo: Calle Mayor,5): ")
        ubi_input = ubi_input.strip()

        ubi_input=check_input(ubi_input)

        print("Ubicación introducida en el formato correcto")
        print("Buscando coincidencias con la ubicación en la base de datos...")
        try:
            choice=str()
            while choice != "S":
                street_well_wroten,coord = c.fuzzy_search(ubi_input,streetmap)
                print(f"Se encontró una calle similar a la introducida: {street_well_wroten.capitalize()}")
                choice = input("Escribe S si es la indicada y cualquier otra cosa sino: ")
                ubi_input=check_input(ubi_input)

            with open(path_file, "r+") as p:
                lines = p.readlines()
                if (ubi_input + "\n") not in lines:
                    p.write(ubi_input+"\n")
            coords.append(coord)

        except Exception as e:
            print(e)

    return coords


def elige_modo():
    print("Tendrás tres modos de ruta a escoger:")
    print("Ruta más corta, Ruta más rápida, ruta más rápida optimizando señales")
    choice = input("Para la más corta -> C \nPara la más rápida -> R\nPara la más rápida optimizada con señales -> RS\n").upper()
    while choice not in ["C","R","RF"]:
        print("Introduce una opción correcta")
        choice = input("Para la más corta -> C \nPara la más rápida -> R\nPara la más rápida optimizada con señales -> RS\n").upper()
    return choice


def encontrar_nodo_acc_mas_cercano(coord,nodes,edges,exit_direction=True):
    """
    Encuentra el nodo más cercano a unas coordenadas específicas que sea accesible según la dirección de las aristas.

    Args:
        coords (tuple): Coordenadas (latitud, longitud) de la ubicación objetivo.
        nodes (dict): Diccionario de nodos, donde cada nodo tiene sus coordenadas como atributos.
        edges (dict): Diccionario de aristas, donde cada arista tiene información sobre dirección y accesibilidad.
        exit_direction (bool): Si es True, busca nodos donde el acceso sea de salida desde las coordenadas. Si es False, entrada.

    Returns:
        object: El nodo más cercano accesible.
    """
    x,y = coord
    closest_node = None

def calculo_rutas(choice:str,coords:list,streetmap:pd.DataFrame):
    if choice == "C":
        i_coord = coords[0]
        distance = 2      #algoritmo sergio con pesos -> 


def main():
    opt_title = input("Desea ver el título continuamente? Escribe S para ver el título continuamente")
    if opt_title.upper() == "S":
        print(GPS)
        streetmap = step_with_header("Cargando callejero...", c.carga_callejero)
        graph = step_with_header("Cargando grafo...", c.carga_grafo)
        time.sleep(2)
        directed_graph = step_with_header("Procesando grafo...", c.procesa_grafo, graph)
        time.sleep(2)
        step_with_header("Explorando grafo...", c.explora_grafo, directed_graph)
        time.sleep(20)
        direction = step_with_header("Buscando dirección...", seleccion_interactiva, streetmap)
        time.sleep(2)
        step_with_header("¡Proceso completado con éxito!")
    else:
        print(GPS)
        street=c.carga_callejero()
        direction=c.busca_direccion("Calle de Alberto Aguilera, 1",street)
        graph=c.carga_grafo()
        directed_graph=c.procesa_grafo(graph)
        c.explora_grafo(directed_graph)



if __name__=="__main__":
    main()
    
"Calle de Alberto Aguilera,25"