import callejero as c
import osmnx as ox
import networkx as nx
import pandas as pd
import re
from typing import Tuple
import os
import time
from math import atan2, degrees, radians, sin, cos,sqrt
import grafo_pesado as g
import numpy as np


GPS = """
   _____  _____    _____    _____ __     __
  / ____||  __ \  / ____|  |  __ \\ \   / /
 | |  __ | |__) || (___    | |__) |\ \_/ / 
 | | |_ ||  ___/  \___ \   |  ___/  \   /  
 | |__| || |      ____) |_ | |       | |   
  \_____||_|     |_____/(_)|_|       |_|   
                                           
                                           

"""

from typing import Union

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
    ubications = ["origen", "destino"]
    coords = []
    for ubication in ubications:
        ubi_input = input(f"Introduce la ubicacion {ubication} en el formato 'Calle,Número' (ejemplo: Calle Mayor,5): ")
        ubi_input = ubi_input.strip()

        ubi_input=check_input(ubi_input)
        ubi_input = ubi_input.upper()
        try:
            choice=str()
            while choice != "S":
                coord, street_well_wroten = c.fuzzy_search_2(ubi_input,streetmap)
                print("COORDENADAS: ",coord)
                if street_well_wroten == "Calle_Iterada":
                    choice = "S"
                else:    
                    choice = input("Escribe S si es la dirección deseada, cualquier otra cosa sino: ")
                    if choice != "S":
                        ubi_input = input(f"Introduce la ubicacion {ubication} en el formato 'Calle,Número' (ejemplo: Calle Mayor,5): ")
                ubi_input=check_input(ubi_input)
                ubi_input = ubi_input.upper()

            with open(path_file, "r+") as p:
                # Leer todas las líneas existentes
                lines = p.readlines()
                # Si hay más de 5 líneas, elimina las más antiguas
                if len(lines) >= 5:
                    lines = lines[1:]  # Elimina la primera línea (la más antigua)
                # Verificar si la entrada ya existe
                if ubi_input not in lines:
                    lines.append(ubi_input"+\n")  # Añadir solo si no existe
                # Reescribir el archivo con las nuevas líneas
                p.seek(0)  # Volver al principio del archivo
                p.writelines(lines)  # Escribir las líneas actualizadas
                p.truncate()  # Asegurar que el archivo no contenga contenido residual

            coords.append(coord)

        except Exception as e:
            print(f"Error: {e}")

    return coords,ubi_input


def elige_modo():
    print("Tendrás tres modos de ruta a escoger:")
    print("Ruta más corta, Ruta más rápida, ruta más rápida optimizando señales")
    choice = input("Para la más corta -> C \nPara la más rápida -> R\nPara la más rápida optimizada con señales -> RS\n").upper()
    while choice not in ["C","R","RS"]:
        print("Introduce una opción correcta")
        choice = input("Para la más corta -> C \nPara la más rápida -> R\nPara la más rápida optimizada con señales -> RS\n").upper()
    return choice


def encontrar_nodo_acc_mas_cercano(coords,G):
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
    closest_nodes = []
    for coord in coords:
        x,y = coord
        print(x,y)
        nodes = G.nodes(data=True)
        closest_node= ox.nearest_nodes(G, x, y)
        closest_nodes.append(closest_node)
        # Obtener índice del nodo


    return closest_nodes

def haversine(lat1: np.float64, lon1:np.float64, lat2:np.float64, lon2:np.float64) -> np.float64:
    """
        Method to compute the haversite distance between 2 pair of coordinates

        :param lat1: first latitude
        :param lon1: first longitude
        :param lat2: second latitude
        :param lon2: second longitude
    """
    dLat = (lat2 - lat1) * np.pi / 180.0
    dLon = (lon2 - lon1) * np.pi / 180.0
 
    # convert to radians
    lat1 = (lat1) * np.pi / 180.0
    lat2 = (lat2) * np.pi / 180.0
 
    # apply formulae
    a = (pow(np.sin(dLat / 2), 2) +
         pow(np.sin(dLon / 2), 2) *
             np.cos(lat1) * np.cos(lat2));
    rad = 6371
    c = 2 * np.arcsin(np.sqrt(a))

    # return the distance in km
    return rad * c
def aplicar_peso_corto(G:Union[nx.Graph, nx.DiGraph], origen:object,neighbour:object):
    if "length" not in G[origen][neighbour] or G[origen][neighbour]["length"]==None:
        x1 = G.nodes[origen]["y"]
        x2 = G.nodes[origen]["x"]
        y1 = G.nodes[neighbour]["y"]
        y2 = G.nodes[neighbour]["x"]
        dist = haversine(x1,x2,y1,y2)

    else:
        dist= G[origen][neighbour]["length"]
    return dist
        
def aplicar_peso_rapido(G:Union[nx.Graph, nx.DiGraph], origen:object, destino:object):
    """
    Calcula el peso entre dos nodos considerando la velocidad, la longitud de la vía
    y el tiempo esperado debido a semáforos en los cruces.

    Args:
        G (Union[nx.Graph, nx.DiGraph]): El grafo que contiene los nodos y aristas.
        origen (object): Nodo de origen.
        destino (object): Nodo destino.

    Returns:
        float: El peso calculado, considerando tiempo esperado de viaje.
    """
    distance = aplicar_peso_corto(G, origen, destino)  

    if "maxspeed" not in G[origen][destino] or G[origen][destino]["maxspeed"] is None:
        conversion = c.MAX_SPEEDS 
        street_type = G[origen][destino]["highway"]
        if type(street_type) == list:
            speeds = [conversion[street] for street in street_type if street in conversion]
            speed = np.mean(list(map(int, speeds))) if speeds else 30  
        else:
            speed = int(conversion.get(street_type, 30)) 
    else:
        speeds = G[origen][destino]["maxspeed"]
        if isinstance(speeds, list):
            speed = np.mean(list(map(int, speeds)))
        elif isinstance(speeds, str) and "|" in speeds:
            speed = np.mean(list(map(int, speeds.split("|"))))
        else:
            speed = int(speeds)
    
    movement_time = distance / speed  
    return movement_time
        
    
def aplicar_peso_rapido_sem(G:Union[nx.Graph, nx.DiGraph], origen:object, destino:object):
    """
    Calcula el peso entre dos nodos considerando la velocidad, la longitud de la vía
    y el tiempo esperado debido a semáforos en los cruces.

    Args:
        G (Union[nx.Graph, nx.DiGraph]): El grafo que contiene los nodos y aristas.
        origen (object): Nodo de origen.
        destino (object): Nodo destino.

    Returns:
        float: El peso calculado, considerando tiempo esperado de viaje.
    """
    movement_time = aplicar_peso_rapido(G,origen,destino)
    signal_time = 0
    if "highway" in G[origen][destino] and "crossing" in G[origen][destino]["highway"]:
        stop_probability = 0.8  
        stop_time = 30 / 3600 
        signal_time = stop_probability * stop_time  

    total_time = movement_time + signal_time

    return total_time
        

def calculo_rutas(coords:list,graph:nx.Graph):
    choice = elige_modo()
    nodes = encontrar_nodo_acc_mas_cercano(coords,graph)
    print(nodes)
    if choice == "C":
        path = g.camino_minimo(graph,aplicar_peso_corto,nodes[0],nodes[1])
        print(path)

    elif choice == "R":
        path = g.camino_minimo(graph,aplicar_peso_rapido,nodes[0],nodes[1])
        print(path)
    else:
        path = g.camino_minimo(graph,aplicar_peso_rapido_sem,nodes[0],nodes[1])
    return path 


def calcular_grados(long1, lat1, long2, lat2):
    """
    Calcula el azimut (ángulo o dirección) entre dos puntos geográficos.

    Args:
        long1 (float): Longitud del primer punto.
        lat1 (float): Latitud del primer punto.
        long2 (float): Longitud del segundo punto.
        lat2 (float): Latitud del segundo punto.

    Returns:
        float: Azimut en grados, de 0° a 360°.
    """
    # Convertir latitudes y longitudes de grados a radianes
    lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])

    # Calcular la diferencia en la longitud
    delta_long = long2 - long1

    # Calcular el azimut usando la fórmula de atan2
    x = sin(delta_long) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_long)
    azimut = atan2(x, y)

    # Convertir el azimut de radianes a grados y normalizar entre 0° y 360°
    azimut = degrees(azimut)
    azimut = (azimut + 360) % 360

    return azimut

def determinar_giro(bearing1, bearing2):
    """
    Determina la dirección del giro en función de dos azimuts consecutivos.

    Args:
        bearing1 (float):  inicial grados.
        bearing2 (float): final grados.

    Returns:
        str: Dirección del giro ('Izquierda', 'Derecha' o 'Recto').
    """
    # Calcular la diferencia entre los dos azimuts
    diferencia = (bearing2 - bearing1 + 360) % 360

    # Determinar la dirección del giro
 # No hay cambio de dirección
    if diferencia < 180:
        return "Derecha"  # Giro hacia la derecha
    else:
        return "Izquierda"  # Giro hacia la izquierda
def instrucciones(path: list, graph: nx.Graph, max_distance: float = 100):
    """
    Genera instrucciones basadas en un camino de nodos en un grafo.

    Args:
        path (list): Lista de identificadores de nodos que forman un camino.
        graph (nx.Graph): Grafo que contiene nodos y aristas.
        max_distance (float): Máxima distancia (en metros) a considerar antes de decidir instrucciones.
    """
    study_nodes = [graph.nodes[path[j]] for j in range(len(path))]
    streets = [graph.edges[path[j], path[j+1]] for j in range(len(path) - 1)]

    # Comprobaciones iniciales para limpiar el grafo
    fail_index_one = [j for j, street in enumerate(streets) if "name" not in street or street["name"] is None]
    for idx in fail_index_one:
        if idx < len(streets) - 1:
            if idx > 0 and streets[idx - 1].get("name") == streets[idx + 1].get("name"):
                streets[idx]["name"] = streets[idx - 1]["name"]
            else:
                streets[idx]["name"] = streets[idx + 1].get("name", "Unknown Street")
        else:
            streets[idx]["name"] = streets[idx - 1].get("name", "Unknown Street")

    fail_index_two = [j for j, street in enumerate(streets) if not isinstance(street.get("name", None), str)]
    for idx in fail_index_two:
        if idx < len(streets) - 1:
            if idx > 0 and streets[idx - 1].get("name") == streets[idx + 1].get("name"):
                streets[idx]["name"] = streets[idx - 1]["name"]
            else:
                streets[idx]["name"] = streets[idx + 1].get("name", "Unknown Street")
        else:
            streets[idx]["name"] = streets[idx - 1].get("name", "Unknown Street")

    # Variable para rastrear la última instrucción generada
    last_instruction = {"street": None, "distance": 0}

    i = 0
    while i < len(path) - 1:
        current_street = streets[i]["name"]
        e_sum = 0
        j = i

        # Acumular distancia mientras sea la misma calle
        while j < len(path) - 1 and streets[j]["name"] == current_street:
            e_sum += aplicar_peso_corto(graph, path[j], path[j+1])
            j += 1

        # Evitar imprimir instrucciones redundantes
        if last_instruction["street"] != current_street or abs(last_instruction["distance"] - e_sum) > 1e-2:
            print(f"Sigue recto por la calle {current_street} durante {int(e_sum)} metros.")
            last_instruction = {"street": current_street, "distance": e_sum}

        i = j  # Avanzar al siguiente tramo de calle

        # Manejar giros si hay un cambio de calle
        if i < len(path) - 1:
            t_sum = aplicar_peso_corto(graph, path[i-1], path[i])
            p_degrees = calcular_grados(
                graph.nodes[path[i-2]]["x"], graph.nodes[path[i-2]]["y"],
                graph.nodes[path[i-1]]["x"], graph.nodes[path[i-1]]["y"]
            )
            n_degrees = calcular_grados(
                graph.nodes[path[i-1]]["x"], graph.nodes[path[i-1]]["y"],
                graph.nodes[path[i]]["x"], graph.nodes[path[i]]["y"]
            )
            turn_to = determinar_giro(n_degrees, p_degrees)
            mv_street = streets[i]["name"]
            print(f"Gira a la {turn_to} por la calle {mv_street} en {int(t_sum)} metros.")


            
            







def main():
    opt_title = input("Desea ver el título continuamente? Escribe S para ver el título continuamente: ")
    if opt_title.upper() == "S":
        print(GPS)
        streetmap = step_with_header("Cargando callejero...", c.carga_callejero)
        graph = step_with_header("Cargando grafo...", c.carga_grafo)
        time.sleep(2)
        directed_graph = step_with_header("Procesando grafo...", c.procesa_grafo, graph)
        time.sleep(2)
        step_with_header("Explorando grafo...", c.explora_grafo, directed_graph)
        time.sleep(2)
        coords, direction = step_with_header("Buscando dirección...", seleccion_interactiva, streetmap)
        print(coords)
        time.sleep(5)
        path = step_with_header("Calculando rutas", calculo_rutas, coords, directed_graph)  # Camino nodo
        time.sleep(5)
        step_with_header("Mostrando Instrucciones...", instrucciones, path, directed_graph)
        print("Dibujando el grafo con el camino calculado...")
        c.dibuja_grafo(graph, path)
        time.sleep(2000000)
        step_with_header("¡Proceso completado con éxito!")
    else:
        print(GPS)
        street = c.carga_callejero()
        direction = c.busca_direccion("Calle de Alberto Aguilera, 1", street)
        graph = c.carga_grafo()
        directed_graph = c.procesa_grafo(graph)
        c.explora_grafo(directed_graph)



if __name__=="__main__":
    main()
    
"Calle de Alberto Aguilera,25"