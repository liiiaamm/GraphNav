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
from threading import Thread
from typing import Union, Callable, Any, Optional, Tuple, List

flecha_arriba = "⬆️"   
flecha_derecha = "➡️"   
flecha_izquierda = "⬅️"
Normal = "\033[0m"
Azul = "\033[34m"
Rojo = "\033[31m"
Verde = "\033[32m"

GPS = f"""{Azul}
   _____  _____    _____    _____ __     __
  / ____||  __ \  / ____|  |  __ \\ \   / /
 | |  __ | |__) || (___    | |__) |\ \_/ / 
 | | |_ ||  ___/  \___ \   |  ___/  \   /  
 | |__| || |      ____) |_ | |       | |   
  \_____||_|     |_____/(_)|_|       |_|   
                                           
                                           

{Normal}"""

from grafo_pesado import NoWayFoundError as NoWay

class CloseGPS (Exception):
    pass

def step_with_header(
    step_message: str,
    function_to_call: Optional[Callable] = None,
    *args: Any,
    **kwargs: Any
) -> Optional[Any]:
    """
    Muestra el encabezado "GPS" y un mensaje, luego ejecuta una función si es necesario.

    Args:
        step_message (str): Mensaje que se mostrará junto al encabezado.
        function_to_call (Optional[Callable]): Una función opcional a ejecutar.
            Si se proporciona, se llamará con los argumentos `*args` y `**kwargs`.
        *args (Any): Argumentos posicionales para `function_to_call`.
        **kwargs (Any): Argumentos de palabras clave para `function_to_call`.

    Returns:
        Optional[Any]: El resultado de `function_to_call` si se proporciona,
        de lo contrario, None.
    """
    os.system('cls' if os.name == 'nt' else 'clear')  
    print(GPS)
    print(f"{Azul}{step_message}{Normal}")
    try:
        if function_to_call:
            result = function_to_call(*args, **kwargs)
            return result  
    except:
        return None

def check_input(ubi_input: str) -> str:
    """
    Verifica y valida el formato de una cadena de entrada que representa una ubicación.

    Args:
        ubi_input (str): La entrada inicial del usuario, que debería tener el formato "Calle,número".

    Returns:
        str: La entrada validada en el formato correcto "Calle,número".
    """
    while "," not in ubi_input:  
        print(f"{Rojo}El formato debe de ser: 'Calle,número'{Normal}")
        ubi_input = input(f"{Rojo}Introduce la ubicación de nuevo: {Normal}")
        while "," in ubi_input and (not ubi_input.split(",")[1].strip().isnumeric()):
            print(f"{Rojo}El número a introducir debe de ser un número{Normal}")
            ubi_input = input(f"{Verde}Introduce la ubicación de nuevo:{Normal} ")
    
    return ubi_input

def seleccion_interactiva(streetmap: pd.DataFrame) -> Tuple[List[Tuple[float, float]], str]:
    """
    Proporciona una interfaz interactiva para que el usuario seleccione ubicaciones de origen y destino,
    valida las entradas y utiliza direcciones exactas y fuzzy search para obtener las coordenadas además de
    guardar un fichero con las últimas 5 ubicaciones introducidas

    Args:
        streetmap (pd.DataFrame): Un DataFrame que contiene información de las calles.

    Returns:
        Tuple[List[Tuple[float, float]], str]: 
            - Una lista de coordenadas (latitud, longitud) para las ubicaciones seleccionadas.
            - La última entrada de ubicación validada por el usuario.
    """
    path_file = "results/latest_results.txt"
    directory = os.path.dirname(path_file)

    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.isfile(path_file):
        with open(path_file, "w") as file:
            pass

    print(f"{Azul}Últimas ubicaciones buscadas...{Normal}")
    with open(path_file, "r") as p:
        for line in p.readlines()[::-1]:  
            print(f"{Azul}{line.rstrip()}{Normal}")

    ubications = ["origen", "destino"]
    coords = []

    for ubication in ubications:
        while True:
            if ubication == "origen":
                print("Si desea salir del GPS, pulse intro sin escribir nada")
                ubi_input = input(f"{Verde}Introduce la ubicacion {ubication} en el formato 'Calle,Número' (ejemplo: Calle Mayor,5): {Normal}")
                if ubi_input == "":
                    coords = None
                    return coords, ubi_input
                
            elif ubication == "destino":
                ubi_input = input(f"{Verde}Introduce la ubicacion {ubication} en el formato 'Calle,Número' (ejemplo: Calle Mayor,5): {Normal}")

            ubi_input = ubi_input.strip()

            ubi_input = check_input(ubi_input)
            ubi_input = ubi_input.upper()
            try:
                choice = str()
                while choice != "S":
                    coord, street_well_wroten = c.fuzzy_search(ubi_input, streetmap)
                    if street_well_wroten == "Calle_Iterada":
                        ubi_to_csv = ubi_input.upper() 
                        choice = "S"
                    else:
                        ubi_to_csv = street_well_wroten.upper()
                        choice = input(f"{Verde}Escribe S si es la dirección deseada, cualquier otra cosa sino: {Normal}")
                        if choice != "S":
                            ubi_input = input(f"{Verde}Introduce la ubicacion {ubication} en el formato 'Calle,Número' (ejemplo: Calle Mayor,5): {Normal}")
                    ubi_input = check_input(ubi_input)
                    ubi_input = ubi_input.upper()

                with open(path_file, "r") as p:
                    lines = p.readlines()

                lines = [line.strip() for line in lines]

                if ubi_to_csv not in lines:
                    lines.append(ubi_to_csv)

                lines = lines[-5:]

                with open(path_file, "w") as p:
                    for line in lines:
                        p.write(f"{line}\n")
                coords.append(coord)  
                break
            except Exception as e:
                print(f"{Rojo}Error: {e}{Normal}")  

    return coords, ubi_input  


def elige_modo() -> str:
    """
    Permite al usuario elegir entre tres modos de ruta:
    - Ruta más corta.
    - Ruta más rápida.
    - Ruta más rápida optimizando señales.

    Returns:
        str: La elección del usuario, que será una de las siguientes:
            - "C" para la ruta más corta.
            - "R" para la ruta más rápida.
            - "RS" para la ruta más rápida optimizada con señales.
    """
    print(f"{Azul}Tendrás tres modos de ruta a escoger:{Normal}")
    print(f"{Azul}Ruta más corta, Ruta más rápida, ruta más rápida optimizando señales{Normal}")
    
    choice = input(f"{Verde}Para la más corta -> C \nPara la más rápida -> R\nPara la más rápida optimizada con señales -> RS{Normal}\n").upper()
    
    while choice not in ["C", "R", "RS"]:
        print(f"{Azul}Introduce una opción correcta{Normal}")
        choice = input(f"{Verde}Para la más corta -> C \nPara la más rápida -> R\nPara la más rápida optimizada con señales -> RS{Normal}\n").upper()
    
    return choice 


def encontrar_nodo_acc_mas_cercano(coords: List[Tuple[float, float]], G: nx.MultiDiGraph) -> List[Any]:
    """
    Encuentra los nodos más cercanos a un conjunto de coordenadas específicas en un grafo de OpenStreetMap.

    Args:
        coords (List[Tuple[float, float]]): 
            Lista de tuplas con coordenadas (longitud, latitud) de las ubicaciones objetivo.
        G (nx.MultiDiGraph): 
            Grafo de calles generado con OSMnx, donde los nodos tienen datos de coordenadas.

    Returns:
        List[Any]: 
            Lista de nodos más cercanos a cada una de las coordenadas proporcionadas.
    """
    closest_nodes = []  
    for coord in coords:
        x, y = coord  
        nodes = G.nodes(data=True)  
        closest_node = ox.nearest_nodes(G, x, y)
        closest_nodes.append(closest_node)

    return closest_nodes  

def haversine(lat1: np.float64, lon1:np.float64, lat2:np.float64, lon2:np.float64) -> np.float64:
    """
    Calcula la distancia de Haversine entre dos puntos geográficos.

    Args:
        lat1 (np.float64): Latitud del primer punto (en grados decimales).
        lon1 (np.float64): Longitud del primer punto (en grados decimales).
        lat2 (np.float64): Latitud del segundo punto (en grados decimales).
        lon2 (np.float64): Longitud del segundo punto (en grados decimales).

    Returns:
        np.float64: Distancia entre los dos puntos en kilómetros.
    """
    dLat = (lat2 - lat1) * np.pi / 180.0
    dLon = (lon2 - lon1) * np.pi / 180.0
 
    lat1 = (lat1) * np.pi / 180.0
    lat2 = (lat2) * np.pi / 180.0
 
    a = (pow(np.sin(dLat / 2), 2) +
         pow(np.sin(dLon / 2), 2) *
             np.cos(lat1) * np.cos(lat2));
    rad = 6371
    c = 2 * np.arcsin(np.sqrt(a))

    return rad * c


def aplicar_peso_corto(G: nx.DiGraph, origen: object, neighbour: object) -> float:
    """
    Calcula el peso (distancia) entre dos nodos en un grafo. Si no existe un atributo "length"
    en la arista entre los nodos o si es `None`, calcula la distancia usando la fórmula de Haversine.

    Args:
        G (Union[nx.Graph, nx.DiGraph]): 
            Grafo dirigido que contiene los nodos y aristas.
        origen (object): 
            Nodo inicial.
        neighbour (object): 
            Nodo vecino (adyacente al nodo inicial).

    Returns:
        float: 
            La distancia entre el nodo `origen` y el nodo `neighbour`.
            Puede ser la longitud especificada en la arista o la distancia calculada con Haversine.
    """
    if "length" not in G[origen][neighbour] or G[origen][neighbour]["length"] is None:
        x1 = G.nodes[origen]["y"]  
        x2 = G.nodes[origen]["x"]  
        y1 = G.nodes[neighbour]["y"]
        y2 = G.nodes[neighbour]["x"]  

        dist = haversine(x1, x2, y1, y2)
    else:
        dist = G[origen][neighbour]["length"]

    return dist
        
def aplicar_peso_rapido(G: Union[nx.Graph, nx.DiGraph], origen: Any, destino: Any) -> float:
    """
    Calcula el peso entre dos nodos considerando la velocidad, la longitud de la vía
    y el tiempo esperado debido a semáforos en los cruces.

    Args:
        G (nx.DiGraph): 
            El grafo que contiene los nodos y aristas.
        origen (object): 
            Nodo de origen.
        destino (object): 
            Nodo destino.

    Returns:
        float: 
            El peso calculado, considerando el tiempo esperado de viaje (en horas).
    """
    distance = aplicar_peso_corto(G, origen, destino)

    if "maxspeed" not in G[origen][destino] or G[origen][destino]["maxspeed"] is None:
        conversion = c.MAX_SPEEDS  
        street_type = G[origen][destino]["highway"]
        
        if isinstance(street_type, list):
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
        G (nx.DiGraph): El grafo que contiene los nodos y aristas.
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
        

def calculo_rutas(coords: List[Any], graph: nx.Graph) -> List[Any]:
    """
    Calcula una ruta óptima entre dos coordenadas basándose en el modo elegido por el usuario.
    Elige entre la ruta más corta, más rápida o más rápida optimizando señales de tráfico.

    Args:
        coords (List): Lista de coordenadas de los puntos de inicio y destino.
        graph (nx.Graph): Grafo que contiene los nodos y aristas del mapa.

    Returns:
        List: Lista que representa el camino calculado (secuencia de nodos).
    """
    choice = elige_modo()

    nodes = encontrar_nodo_acc_mas_cercano(coords, graph)

    try:
        if choice == "C":
            path = g.camino_minimo(graph, aplicar_peso_corto, nodes[0], nodes[1])
        elif choice == "R":
            path = g.camino_minimo(graph, aplicar_peso_rapido, nodes[0], nodes[1])
        else:
            path = g.camino_minimo(graph, aplicar_peso_rapido_sem, nodes[0], nodes[1])
        return path
    
    except (TypeError, NoWay) as e:
        print(e)
        return None


def calcular_grados(long1: float, lat1: float, long2: float, lat2: float) -> float:
    """
    Calcula el azimut (ángulo o dirección) entre dos puntos geográficos.

    Args:
        long1 (float): Longitud del primer punto en grados.
        lat1 (float): Latitud del primer punto en grados.
        long2 (float): Longitud del segundo punto en grados.
        lat2 (float): Latitud del segundo punto en grados.

    Returns:
        float: Azimut en grados, de 0° a 360°.
    """
    lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])

    delta_long = long2 - long1

    x = sin(delta_long) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_long)
    azimut = atan2(x, y)

    azimut = degrees(azimut)
    azimut = (azimut + 360) % 360

    return azimut

def determinar_giro(bearing1: float, bearing2: float) -> str:
    """
    Determina la dirección del giro en función de dos azimuts consecutivos.

    Args:
        bearing1 (float): Azimut inicial en grados (de 0° a 360°).
        bearing2 (float): Azimut final en grados (de 0° a 360°).

    Returns:
        str: Dirección del giro:
            - 'Derecha' si el giro es hacia la derecha.
            - 'Izquierda' si el giro es hacia la izquierda.
            - 'Recto' si no hay cambio significativo en la dirección.
    """
    diferencia = (bearing2 - bearing1 + 540) % 360 - 180

    umbral_recto = 5  

    if abs(diferencia) < umbral_recto:
        return "Recto"
    elif diferencia > 0:
        return "Derecha" 
    else:
        return "Izquierda"

    
flecha_arriba = "⬆️"
flecha_derecha = "➡️"
flecha_izquierda = "⬅️"
Normal = "\033[0m"
Azul = "\033[34m"
Rojo = "\033[31m"
Verde = "\033[32m"

def instrucciones(path: List[int], graph: nx.Graph, max_distance: float = 100) -> None:
    """
    Genera instrucciones basadas en un camino de nodos en un grafo con un diseño visual atractivo.

    Args:
        path (List[int]): 
            Lista de identificadores de nodos que forman un camino.
        graph (nx.Graph): 
            Grafo que contiene nodos y aristas.
        max_distance (float, optional): 
            Máxima distancia (en metros) a considerar antes de decidir instrucciones.
            Por defecto es 100.
    """
    study_nodes = [graph.nodes[path[j]] for j in range(len(path))]
    streets = [graph.edges[path[j], path[j + 1]] for j in range(len(path) - 1)]

    fail_index_one = [j for j, street in enumerate(streets) if "name" not in street or street["name"] is None]
    for idx in fail_index_one:
        streets[idx]["name"] = None  

    for idx, street in enumerate(streets):
        if "distance" not in street or street["distance"] is None:
            origen = path[idx]
            destino = path[idx + 1]
            street["distance"] = aplicar_peso_corto(graph, origen, destino)

    last_instruction = {"street": None, "distance": 0}

    i = 0
    while i < len(path) - 1:
        current_street = streets[i]["name"]
        e_sum = 0
        j = i

        while j < len(path) - 1 and streets[j]["name"] == current_street:
            e_sum += streets[j]["distance"]
            j += 1

        next_street = streets[j]["name"] if j < len(streets) else "Destino final"

        current_street_formatted = current_street if current_street is not None else "calle"
        next_street_formatted = next_street if next_street is not None else "calle"

        if last_instruction["street"] != current_street or abs(last_instruction["distance"] - e_sum) > 1e-2:
            print(f"{flecha_arriba}  {Azul}Sigue recto{Normal} por {Rojo}{current_street_formatted}{Normal} durante {Verde}{int(e_sum)} metros{Normal} hasta llegar a {Rojo}{next_street_formatted}.{Normal}")
            print("\n")
            last_instruction = {"street": current_street, "distance": e_sum}

        i = j  

        if i < len(path) - 1:
            t_sum = streets[i]["distance"]
            p_degrees = calcular_grados(
                graph.nodes[path[i - 2]]["x"], graph.nodes[path[i - 2]]["y"],
                graph.nodes[path[i - 1]]["x"], graph.nodes[path[i - 1]]["y"]
            ) if i - 2 >= 0 else None
            n_degrees = calcular_grados(
                graph.nodes[path[i - 1]]["x"], graph.nodes[path[i - 1]]["y"],
                graph.nodes[path[i]]["x"], graph.nodes[path[i]]["y"]
            )

            if p_degrees is not None:
                turn_to = determinar_giro(p_degrees, n_degrees)
                arrow = flecha_izquierda if turn_to == "Izquierda" else flecha_derecha

                current_street_formatted = current_street if current_street is not None else "calle"
                next_street_formatted = next_street if next_street is not None else "calle"

                print(f"{arrow}  {Azul}Gira a la {Rojo}{turn_to}{Normal} desde {Rojo}{current_street_formatted}{Normal} hacia {Rojo}{next_street_formatted}{Normal} en {Verde}{int(t_sum)} metros.{Normal}")
                print("\n")

            







def main():
    print(GPS)
    streetmap = step_with_header("Cargando callejero...", c.carga_callejero)
    graph = step_with_header("Cargando grafo...", c.carga_grafo)
    time.sleep(2)
    directed_graph = step_with_header("Procesando grafo...", c.procesa_grafo, graph)
    time.sleep(2)
    step_with_header("Explorando grafo...", c.explora_grafo, directed_graph)
    time.sleep(2)
    while True: 
        coords, direction = step_with_header("Buscando dirección...", seleccion_interactiva, streetmap)
        time.sleep(1)
        if direction == "":
            print(f"{Azul}Gracias por utilizar nuestro GPS!{Normal}")
            break
        path = step_with_header("Calculando rutas", calculo_rutas, coords, directed_graph)  
        time.sleep(1)
        if path is not None:   
            step_with_header("Mostrando Instrucciones...", instrucciones, path, directed_graph)
            print(f"{Azul}Dibujando el grafo con el camino calculado...{Normal}")
            c.dibuja_grafo(graph, path)



if __name__=="__main__":
    main()
    
