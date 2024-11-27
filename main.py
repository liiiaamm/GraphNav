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

from typing import Union, Callable, Any, Optional, Tuple, List


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
    os.system('cls' if os.name == 'nt' else 'clear')  # Limpia la consola dependiendo del sistema operativo
    print(GPS)  # Imprime el encabezado estático
    print(step_message)  # Muestra el mensaje del paso actual
    if function_to_call:
        result = function_to_call(*args, **kwargs)  # Llama a la función con los argumentos proporcionados
        return result  # Retorna el resultado de la función llamada, si existe

def check_input(ubi_input: str) -> str:
    """
    Verifica y valida el formato de una cadena de entrada que representa una ubicación.

    Args:
        ubi_input (str): La entrada inicial del usuario, que debería tener el formato "Calle,número".

    Returns:
        str: La entrada validada en el formato correcto "Calle,número".
    """
    while "," not in ubi_input:  # Asegurarse de que la entrada contenga una coma
        print("El formato debe de ser: 'Calle,número'")
        ubi_input = input("Introduce la ubicación de nuevo: ")
        # Validación secundaria: el número después de la coma debe ser numérico
        while "," in ubi_input and (not ubi_input.split(",")[1].isnumeric()):
            print("El número a introducir debe de ser un número")
            ubi_input = input("Introduce la ubicación de nuevo: ")
    
    return ubi_input

def seleccion_interactiva(streetmap: pd.DataFrame) -> Tuple[List[Tuple[float, float]], str]:
    """
    Proporciona una interfaz interactiva para que el usuario seleccione ubicaciones de origen y destino,
    valida las entradas y utiliza fuzzy search para obtener las coordenadas.

    Args:
        streetmap (pd.DataFrame): Un DataFrame que contiene información de las calles.

    Returns:
        Tuple[List[Tuple[float, float]], str]: 
            - Una lista de coordenadas (latitud, longitud) para las ubicaciones seleccionadas.
            - La última entrada de ubicación validada por el usuario.
    """
    # Archivo donde se almacenan las ubicaciones recientes
    path_file = "results/latest_results.txt"
    directory = os.path.dirname(path_file)

    # Crear el directorio si no existe
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Crear el archivo si no existe
    if not os.path.isfile(path_file):
        with open(path_file, "w") as file:
            pass

    # Mostrar ubicaciones buscadas recientemente
    print("Ubicaciones buscadas recientemente...")
    with open(path_file, "r") as p:
        for line in p.readlines()[::-1]:  # Leer y mostrar líneas en orden inverso
            print(line.rstrip())

    ubications = ["origen", "destino"]
    coords = []

    for ubication in ubications:
        # Solicitar entrada de ubicación al usuario
        ubi_input = input(f"Introduce la ubicacion {ubication} en el formato 'Calle,Número' (ejemplo: Calle Mayor,5): ")
        ubi_input = ubi_input.strip()

        # Validar el formato de la entrada
        ubi_input = check_input(ubi_input)
        ubi_input = ubi_input.upper()

        try:
            choice = str()
            while choice != "S":
                # Realizar búsqueda fuzzy y obtener coordenadas
                coord, street_well_wroten = c.fuzzy_search_2(ubi_input, streetmap)
                print("COORDENADAS: ", coord)
                if street_well_wroten == "Calle_Iterada":
                    choice = "S"
                else:
                    choice = input("Escribe S si es la dirección deseada, cualquier otra cosa sino: ")
                    if choice != "S":
                        ubi_input = input(f"Introduce la ubicacion {ubication} en el formato 'Calle,Número' (ejemplo: Calle Mayor,5): ")
                ubi_input = check_input(ubi_input)
                ubi_input = ubi_input.upper()

            # Actualizar el archivo de ubicaciones recientes
            with open(path_file, "r+") as p:
                lines = p.readlines()  # Leer todas las líneas existentes
                if len(lines) >= 5:  # Limitar a 5 líneas
                    lines = lines[1:]  # Eliminar la más antigua
                if ubi_input not in lines:  # Verificar si ya existe
                    lines.append(ubi_input + "\n")
                p.seek(0)  # Volver al inicio del archivo
                p.writelines(lines)  # Escribir las líneas actualizadas
                p.truncate()  # Eliminar contenido residual si existe

            coords.append(coord)  # Guardar las coordenadas seleccionadas

        except Exception as e:
            print(f"Error: {e}")  # Manejar errores y mostrar mensajes

    return coords, ubi_input  # Retornar coordenadas y última entrada validada


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
    # Mostrar las opciones al usuario
    print("Tendrás tres modos de ruta a escoger:")
    print("Ruta más corta, Ruta más rápida, ruta más rápida optimizando señales")
    
    # Solicitar la elección del usuario
    choice = input("Para la más corta -> C \nPara la más rápida -> R\nPara la más rápida optimizada con señales -> RS\n").upper()
    
    # Validar que la entrada sea correcta
    while choice not in ["C", "R", "RS"]:
        print("Introduce una opción correcta")
        choice = input("Para la más corta -> C \nPara la más rápida -> R\nPara la más rápida optimizada con señales -> RS\n").upper()
    
    return choice  # Retornar la elección validada


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
    closest_nodes = []  # Lista para almacenar los nodos más cercanos
    for coord in coords:
        x, y = coord  # Desempaquetar las coordenadas (longitud, latitud)
        print(x, y)  # Mostrar las coordenadas actuales
        nodes = G.nodes(data=True)  # Obtener los nodos del grafo con sus datos
        closest_node = ox.nearest_nodes(G, x, y)  # Encontrar el nodo más cercano
        closest_nodes.append(closest_node)  # Añadir el nodo más cercano a la lista

    return closest_nodes  # Retornar la lista de nodos más cercanos

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


def aplicar_peso_corto(G: Union[nx.Graph, nx.DiGraph], origen: object, neighbour: Any) -> float:
    """
    Calcula el peso (distancia) entre dos nodos en un grafo. Si no existe un atributo "length"
    en la arista entre los nodos o si es `None`, calcula la distancia usando la fórmula de Haversine.

    Args:
        G (Union[nx.Graph, nx.DiGraph]): 
            Grafo (no dirigido o dirigido) que contiene los nodos y aristas.
        origen (Any): 
            Nodo inicial.
        neighbour (Any): 
            Nodo vecino (adyacente al nodo inicial).

    Returns:
        float: 
            La distancia entre el nodo `origen` y el nodo `neighbour`.
            Puede ser la longitud especificada en la arista o la distancia calculada con Haversine.
    """
    # Verificar si el atributo "length" está disponible en la arista
    if "length" not in G[origen][neighbour] or G[origen][neighbour]["length"] is None:
        # Obtener las coordenadas de los nodos
        x1 = G.nodes[origen]["y"]  # Latitud del nodo origen
        x2 = G.nodes[origen]["x"]  # Longitud del nodo origen
        y1 = G.nodes[neighbour]["y"]  # Latitud del nodo vecino
        y2 = G.nodes[neighbour]["x"]  # Longitud del nodo vecino

        # Calcular la distancia usando Haversine
        dist = haversine(x1, x2, y1, y2)
    else:
        # Usar la longitud especificada en la arista
        dist = G[origen][neighbour]["length"]

    return dist
        
def aplicar_peso_rapido(G: Union[nx.Graph, nx.DiGraph], origen: Any, destino: Any) -> float:
    """
    Calcula el peso entre dos nodos considerando la velocidad, la longitud de la vía
    y el tiempo esperado debido a semáforos en los cruces.

    Args:
        G (Union[nx.Graph, nx.DiGraph]): 
            El grafo que contiene los nodos y aristas.
        origen (Any): 
            Nodo de origen.
        destino (Any): 
            Nodo destino.

    Returns:
        float: 
            El peso calculado, considerando el tiempo esperado de viaje (en horas).
    """
    # Calcular la distancia entre los nodos usando aplicar_peso_corto
    distance = aplicar_peso_corto(G, origen, destino)

    # Determinar la velocidad máxima de la vía
    if "maxspeed" not in G[origen][destino] or G[origen][destino]["maxspeed"] is None:
        # Usar una conversión de velocidades basada en el tipo de vía
        conversion = c.MAX_SPEEDS  # Diccionario de tipos de calles a velocidades predeterminadas
        street_type = G[origen][destino]["highway"]  # Obtener el tipo de vía
        
        # Si el tipo de vía es una lista, promediar las velocidades aplicables
        if isinstance(street_type, list):
            speeds = [conversion[street] for street in street_type if street in conversion]
            speed = np.mean(list(map(int, speeds))) if speeds else 30  # Velocidad predeterminada: 30 km/h
        else:
            speed = int(conversion.get(street_type, 30))  # Velocidad predeterminada: 30 km/h
    else:
        # Procesar el atributo maxspeed de la vía
        speeds = G[origen][destino]["maxspeed"]
        if isinstance(speeds, list):  # Si es una lista de velocidades, calcular la media
            speed = np.mean(list(map(int, speeds)))
        elif isinstance(speeds, str) and "|" in speeds:  # Si es una cadena separada por "|", dividir y promediar
            speed = np.mean(list(map(int, speeds.split("|"))))
        else:
            speed = int(speeds)  # Si es un solo valor, convertir a entero

    # Calcular el tiempo de movimiento (tiempo = distancia / velocidad)
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
        

def calculo_rutas(coords: List[Any], graph: nx.Graph) -> List[Any]:
    """
    Calcula una ruta óptima entre dos coordenadas basándose en el modo elegido por el usuario.
    Elige entre la ruta más corta, más rápida o más rápida optimizando señales de tráfico.

    Args:
        coords (List[Any]): Lista de coordenadas de los puntos de inicio y destino.
        graph (nx.Graph): Grafo que contiene los nodos y aristas del mapa.

    Returns:
        List[Any]: Lista que representa el camino calculado (secuencia de nodos).
    """
    # Permitir al usuario elegir el modo de cálculo de la ruta
    choice = elige_modo()

    # Encontrar los nodos más cercanos a las coordenadas proporcionadas
    nodes = encontrar_nodo_acc_mas_cercano(coords, graph)
    print(nodes)  # Mostrar los nodos encontrados

    # Calcular la ruta en función de la elección del usuario
    if choice == "C":
        path = g.camino_minimo(graph, aplicar_peso_corto, nodes[0], nodes[1])
        print(path)  # Mostrar la ruta calculada
    elif choice == "R":
        path = g.camino_minimo(graph, aplicar_peso_rapido, nodes[0], nodes[1])
        print(path)  # Mostrar la ruta calculada
    else:
        path = g.camino_minimo(graph, aplicar_peso_rapido_sem, nodes[0], nodes[1])

    return path


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
    # Calcular la diferencia entre los dos azimuts
    diferencia = (bearing2 - bearing1 + 360) % 360

    # Determinar la dirección del giro
    if diferencia == 0:
        return "Recto"  # No hay cambio de dirección
    elif diferencia < 180:
        return "Derecha"  # Giro hacia la derecha
    else:
        return "Izquierda"
    
def instrucciones(path: List[int], graph: nx.Graph, max_distance: float = 100) -> None:
    """
    Genera instrucciones basadas en un camino de nodos en un grafo.

    Args:
        path (List[int]): 
            Lista de identificadores de nodos que forman un camino.
        graph (nx.Graph): 
            Grafo que contiene nodos y aristas.
        max_distance (float, optional): 
            Máxima distancia (en metros) a considerar antes de decidir instrucciones.
            Por defecto es 100.
    """
    # Obtener los nodos del camino
    study_nodes = [graph.nodes[path[j]] for j in range(len(path))]
    # Obtener las aristas entre los nodos del camino
    streets = [graph.edges[path[j], path[j+1]] for j in range(len(path) - 1)]

    # Identificar y corregir calles sin nombre
    fail_index_one = [j for j, street in enumerate(streets) if "name" not in street or street["name"] is None]
    for idx in fail_index_one:
        if idx < len(streets) - 1:
            if idx > 0 and streets[idx - 1].get("name") == streets[idx + 1].get("name"):
                streets[idx]["name"] = streets[idx - 1]["name"]
            else:
                streets[idx]["name"] = streets[idx + 1].get("name", "Unknown Street")
        else:
            streets[idx]["name"] = streets[idx - 1].get("name", "Unknown Street")

    # Manejar calles con nombres no válidos
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