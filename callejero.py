"""
callejero.py

Matemática Discreta - IMAT
ICAI, Universidad Pontificia Comillas

Grupo: GP05A
Integrantes:
    - Liam Esgueva González
    - Sergo Fernández Cordero
    
Descripción:
Librería con herramientas y clases auxiliares necesarias para la representación de un callejero en un grafo.

Complétese esta descripción según las funcionalidades agregadas por el grupo.
"""
Normal = "\033[0m"
Azul = "\033[34m"
Rojo = "\033[31m"
Verde = "\033[32m"

import osmnx as ox
import networkx as nx
import pandas as pd
import re
from typing import Tuple
import matplotlib.pyplot as plt
from rapidfuzz import process
import os
from typing import Union, Callable, Any, Optional, Tuple, List


STREET_FILE_NAME="direcciones.csv"

PLACE_NAME = "Madrid, Spain"
MAP_FILE_NAME="madrid.graphml"

MAX_SPEEDS={'living_street': '20',
 'residential': '30',
 'primary_link': '40',
 'unclassified': '40',
 'secondary_link': '40',
 'trunk_link': '40',
 'secondary': '50',
 'tertiary': '50',
 'primary': '50',
 'trunk': '50',
 'tertiary_link':'50',
 'busway': '50',
 'motorway_link': '70',
 'motorway': '100'}


class ServiceNotAvailableError(Exception):
    "Excepción que indica que la navegación no está disponible en este momento"
    pass


class AdressNotFoundError(Exception):
    "Excepción que indica que una dirección buscada no existe en la base de datos"
    pass


############## Parte 2 ##############


def conversion_to_number(pattern: str, x: str) -> Optional[float]:
    """
    Convierte una cadena que representa coordenadas en grados, minutos y segundos
    (DMS) a un número decimal.

    Args:
        pattern (str): Expresión regular para buscar el formato DMS en la cadena.
        x (str): Cadena de entrada que contiene las coordenadas.

    Returns:
        Optional[float]: El valor convertido en decimal si tiene éxito, 
        o None si ocurre un error o el formato no es válido.
    """
    # Buscar el patrón en la cadena
    match = re.search(pattern, x)
    if match:
        try:
            # Extraer grados, minutos y segundos del patrón
            degrees = float(match.group(1))
            minutes = float(match.group(2))
            seconds = float(match.group(3))
        except ValueError:
            print(f"{Rojo}Los valores no son enteros, no se puede hacer la conversión{Normal}")
            return None
        # Obtener la dirección (N, S, E, W)
        direction = match.group(4)
        # Calcular la conversión a formato decimal
        conversion = degrees + (minutes / 60) + (seconds / 3600)
        # Ajustar el signo si la dirección es S (sur) o W (oeste)
        if direction in ["S", "W"]:
            return -1 * conversion
        return conversion
    else:
        print(f"{Rojo}Los datos no tienen el formato correcto{Normal}")
        return None
    
def carga_callejero() -> pd.DataFrame:
    """
    Carga el callejero de Madrid desde un archivo CSV, lo procesa y devuelve un DataFrame
    con los datos transformados, incluyendo las coordenadas en formato decimal.

    Args:
        None

    Returns:
        pd.DataFrame: DataFrame procesado con las columnas "VIA_CLASE", "VIA_PAR", 
        "VIA_NOMBRE", "NUMERO", "LATITUD", "LONGITUD", donde las coordenadas 
        están en formato decimal.

    Raises:
        FileNotFoundError: Si el archivo CSV no existe o no puede ser cargado.
    """
    try:
        # Cargar el archivo CSV con las columnas relevantes
        df = pd.read_csv(
            STREET_FILE_NAME,
            sep=";",
            encoding="ISO-8859-1",
            usecols=["VIA_CLASE", "VIA_PAR", "VIA_NOMBRE", "NUMERO", "LATITUD", "LONGITUD"]
        )
    except Exception as e:
        raise FileNotFoundError(f"{Rojo}El fichero no existe{Normal}") from e

    # Crear una copia del DataFrame para procesamiento
    copy = df.copy()

    # Expresión regular para identificar coordenadas en formato DMS
    pattern = r"(\d{1,3})°(\d{1,2})'(\d{1,2}\.?\d*)''\s(\w)"

    # Convertir LATITUD y LONGITUD a formato decimal
    copy["LATITUD"] = copy["LATITUD"].apply(lambda x: conversion_to_number(pattern, x))
    copy["LONGITUD"] = copy["LONGITUD"].apply(lambda x: conversion_to_number(pattern, x))

    return copy



def dibuja_grafo(graph: nx.MultiDiGraph, path: List[int]) -> None:
    """
    Dibuja un grafo de OpenStreetMap resaltando las aristas que están en el camino (path),
    y ajusta la vista para mostrar solo el área donde está el camino.

    Args:
        graph (nx.MultiDiGraph): El grafo de las calles.
        path (List[int]): Lista de nodos que forman el camino a resaltar.

    Returns:
        None
    """
    # Asegurarse de que los nodos del path están en el grafo
    valid_path = [node for node in path if node in graph.nodes]

    # Obtener los colores para las aristas
    edge_colors = []
    edge_widths = []
    edges = list(graph.edges(keys=True))
    path_edges = list(zip(valid_path[:-1], valid_path[1:]))

    for u, v, key in edges:
        if (u, v) in path_edges or (v, u) in path_edges:
            edge_colors.append("red")  # Resaltar las aristas del camino en rojo
            edge_widths.append(2)      # Ancho de línea más grueso para el camino
        else:
            edge_colors.append("gray")  # Resto de las aristas en gris
            edge_widths.append(0.5)     # Ancho de línea por defecto

    # Obtener los colores y tamaños para los nodos
    node_colors = []
    node_sizes = []
    for node in graph.nodes():
        if node == valid_path[0]:
            node_colors.append("green")  # Nodo inicial en verde
            node_sizes.append(100)       # Tamaño más grande
        elif node == valid_path[-1]:
            node_colors.append("red")    # Nodo final en rojo
            node_sizes.append(100)       # Tamaño más grande
        else:
            node_colors.append("gray")   # Otros nodos en gris o no mostrarlos
            node_sizes.append(0)         # Tamaño cero para no mostrarlos

    # Dibujar el grafo sin mostrarlo aún
    fig, ax = ox.plot_graph(
        graph,
        node_color=node_colors,
        node_size=node_sizes,
        edge_linewidth=edge_widths,
        edge_color=edge_colors,
        show=False,
        close=False
    )

    # Ajustar los límites del eje para centrarse en el camino
    # Obtener las coordenadas de los nodos en el camino
    x_values = [graph.nodes[node]['x'] for node in valid_path]
    y_values = [graph.nodes[node]['y'] for node in valid_path]

    # Calcular el bounding box con un margen
    margin = 0.001  # Puedes ajustar este valor según sea necesario
    min_x = min(x_values) - margin
    max_x = max(x_values) + margin
    min_y = min(y_values) - margin
    max_y = max(y_values) + margin

    # Establecer los límites del eje
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)

    # Mostrar el gráfico
    plt.show()




def busca_direccion(direccion:str, callejero:pd.DataFrame) -> Tuple[float,float]:
    """ Función que busca una dirección, dada en el formato
        calle, numero
    en el DataFrame callejero de Madrid y devuelve el par (latitud, longitud) en grados de la
    hubicación geográfica de dicha dirección
    
    Args:
        direccion (str): Nombre completo de la calle con número, en formato "Calle, num"
        callejero (DataFrame): DataFrame con la información de las calles
    Returns:
        Tuple[float,float]: Par de float (latitud,longitud) de la dirección buscada, expresados en grados
    Raises:
        AdressNotFoundError: Si la dirección no existe en la base de datos
    Example:
        busca_direccion("Calle de Alberto Aguilera, 23", data)=(40.42998055555555,3.7112583333333333)
        busca_direccion("Calle de Alberto Aguilera, 25", data)=(40.43013055555555,3.7126916666666667)
    """
    try:
        street, number = direccion.split(",")
        number = int(number.strip())
    except ValueError:
        raise ValueError(f"{Rojo}La dirección debe estar en el formato 'Calle, Número'.{Normal}")

    callejero["total_street"] = (
        callejero["VIA_CLASE"] + " " + callejero["VIA_PAR"].fillna("") + " " + callejero["VIA_NOMBRE"]
    )

    street_coincidence = callejero[callejero['total_street'] == street.upper()]
    number_coincidence = street_coincidence[street_coincidence["NUMERO"] == number]

    if not number_coincidence.empty:
        print(f"{Azul}Se encontró la dirección exacta: {direccion.capitalize()}{Normal}")
        return number_coincidence["LONGITUD"].iloc[0], number_coincidence["LATITUD"].iloc[0]
    else: 
        raise AdressNotFoundError(f"{Rojo}La dirección no fue encontrada de forma exacta.{Normal}")



def fuzzy_search(direccion: str, callejero: pd.DataFrame, threshold=80) -> Tuple[float, float]:
    """
    Función que realiza una búsqueda de una dirección en el callejero.
    Primero intenta una búsqueda exacta usando busca_direccion.
    Si no la encuentra, realiza una búsqueda aproximada.
 
    Args:
        direccion (str): Nombre completo de la calle con número, en formato "Calle, num".
        callejero (DataFrame): DataFrame con la información de las calles.
        threshold (float): Porcentaje de similitud necesario para que la coincidencia se detecte.
 
    Returns:
        Tuple[float, float]: Par de float (latitud, longitud) de la dirección encontrada.
        str: Dirección bien escrita (si se usó la búsqueda aproximada).
 
    Raises:
        AdressNotFoundError: Si no se encuentra una coincidencia suficiente.
    """
    try:
        # Intentamos la búsqueda exacta
        coords = busca_direccion(direccion, callejero)
        return coords, "Calle_Iterada"  # Devolvemos también la dirección original
    except AdressNotFoundError:
        # Si no se encuentra, realizamos la búsqueda aproximada
        street, number = direccion.split(",")
        number = int(number.strip())
        callejero["total_street"] = (
            callejero["VIA_CLASE"] + " " + callejero["VIA_PAR"].fillna("") + " " + callejero["VIA_NOMBRE"]
        )
        unique_streets = callejero["total_street"].unique().tolist()
 
        best_match = process.extractOne(street.upper(), unique_streets)
 
        if best_match and best_match[1] >= threshold:
            matched_street = best_match[0]
            street_coincidence = callejero[callejero["total_street"] == matched_street].copy()
 
            # Comprobar si el número exacto está disponible
            if number in street_coincidence["NUMERO"].values:
                match = street_coincidence[street_coincidence["NUMERO"] == number]
                print(f"{Azul}Coincidencia encontrada en la calle similar: {matched_street}, {str(number)}{Normal}")
                return (match["LONGITUD"].iloc[0],match["LATITUD"].iloc[0]), f"{matched_street}, {str(number)}{Normal}"
            else:
                # Buscar el número más cercano
                street_coincidence["distance"] = abs(street_coincidence["NUMERO"] - number)
                closest_match = street_coincidence.loc[street_coincidence["distance"].idxmin()]
                print(f"{Azul}Coincidencia encontrada en la calle similar: {matched_street}, {str(closest_match['NUMERO'])}{Normal}")
                return (closest_match["LONGITUD"], closest_match["LATITUD"]), f"{matched_street}, {str(closest_match['NUMERO'])}"
        else:
            raise AdressNotFoundError("No se encontró una dirección similar en el callejero.")


def carga_grafo() -> nx.MultiDiGraph:
    """ Función que recupera el quiver de calles de Madrid de OpenStreetMap.
    Args: None
    Returns:
        nx.MultiDiGraph: Quiver de las calles de Madrid.
    Raises:
        ServiceNotAvailableError: Si no es posible recuperar el grafo de OpenStreetMap.
    """
    try:
        if os.path.exists(MAP_FILE_NAME):
            print(f"{Azul}Cargando grafo desde el archivo {MAP_FILE_NAME}{Normal}")
            graph = ox.load_graphml(MAP_FILE_NAME)
            if not isinstance(graph, nx.MultiDiGraph):
                print(f"{Rojo}El argumento 'multidigrafo' debe ser un nx.MultiDiGraph.{Normal}")
        else:
            print(f"{Azul}Descargando grafo desde OpenStreetMap...{Normal}")
            graph = ox.graph_from_place(PLACE_NAME,network_type="drive")
            ox.save_graphml(graph,MAP_FILE_NAME)
            print(f"{Azul}Grafo guardado exitosamente en {MAP_FILE_NAME}{Normal}")
            if not isinstance(graph, nx.MultiDiGraph):
                    print(f"{Rojo}El argumento 'multidigrafo' debe ser un nx.MultiDiGraph.{Normal}")
        return graph
        
    except Exception as e:
        raise ServiceNotAvailableError(f"{Rojo}No se pudo recuperar el grafo de OpenStreetMap{Normal}")
    


def procesa_grafo(multidigrafo:nx.MultiDiGraph) -> nx.DiGraph:
    """ Función que recupera el quiver de calles de Madrid de OpenStreetMap.
    Args:
        multidigrafo: multidigrafo de las calles de Madrid obtenido de OpenStreetMap.
    Returns:
        nx.DiGraph: Grafo dirigido y sin bucles asociado al multidigrafo dado.
    Raises: None
    """
    if not isinstance(multidigrafo, nx.MultiDiGraph):
        print(f"{Rojo}El argumento 'multidigrafo' debe ser un nx.MultiDiGraph.{Normal}")
    directed_graph = ox.convert.to_digraph(multidigrafo)
    loops = list(nx.selfloop_edges(directed_graph))  # Encuentra los bucles
    directed_graph.remove_edges_from(loops)  # Elimina todos los bucles de una vez

    if not isinstance(directed_graph, nx.DiGraph):
        print(f"{Rojo}No se construyo bien{Normal}")
    return directed_graph

def explora_grafo(graph:nx.DiGraph)->None:
    """
    Explora los datos de nodos y aristas del grafo y lo dibuja basado en la posición geográfica.
    
    Args:
        grafo: Grafo dirigido (`DiGraph`) a explorar y dibujar.
    
    Returns:
        None: Imprime la información en la consola y muestra el grafo visualizado.
    """
    #Exploración de los nodos
    print("Exploramos los nodos: \n")
    print(f"El total de nodos es: {graph.number_of_nodes()}")
    
    #Atributos de nodo
    for node,data in graph.nodes(data=True):
        n_example = (node,data)
        break
    print(f"Atributos de un nodo de ejemplo (Nodo {n_example[0]}): {n_example[1]}")
    node_pos = [n for n,data in graph.nodes(data=True) if "x" not in data or "y" not in data]
    if node_pos:
        print(f"El número de nodos que no tiene infomración geográfica es: {len(node_pos)}")

    else:
        print("Todos los nodos tienen información geográfica")

    print("Exploramos las aristas: \n")
    print(f"El total de aristas es: {graph.number_of_edges()}")
    
    #Atributos de nodo
    for u, v, data in graph.edges(data=True):
        e_example = (u,v,data)
        break
    print(f"Atributos de una arista de ejemplo (Nodo {e_example[0],e_example[1]}): {e_example[2]}")
    edge_len = [(u,v) for u,v,data in graph.edges(data=True) if "length" not in data]
    if edge_len:
        print(f"El numero de aristas que no tienen longitud es: {len(edge_len)}")
    else:
        print("Todas las aristas tienen información de longitud.")

    pos = {nodo: (datos["x"], datos["y"]) for nodo, datos in graph.nodes(data=True)}