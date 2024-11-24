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

import osmnx as ox
import networkx as nx
import pandas as pd
import re
from typing import Tuple
import matplotlib.pyplot as plt
from rapidfuzz import process

import os


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


def conversion_to_number(pattern,x):
    match=re.search(pattern,x)
    if match:
        try: 
            degrees = float(match.group(1))
            minutes = float(match.group(2))
            seconds = float(match.group(3))
        except ValueError:
            print("Los valores no son enteros, no se puede hacer la conversión")
            return None
        direction = match.group(4)
        conversion = degrees*(minutes/60)*(seconds/3600)
        if direction in ["S","W"]:
            return -1*conversion
        return conversion
    else:
        print("Los datos no tienen el formato correcto")
        return None
    
def carga_callejero() -> pd.DataFrame:
    """ Función que carga el callejero de Madrid, lo procesa y devuelve
    un DataFrame con los datos procesados
    
    Args: None
    Returns:
        Dict[object,object]: Devuelve un diccionario que indica, para cada vértice del
            grafo, qué vértice es su padre en el árbol abarcador mínimo.
    Raises:
        FileNotFoundError si el fichero csv con las direcciones no existe
    """
    try:

        df = pd.read_csv(STREET_FILE_NAME, sep=";", encoding="ISO-8859-1",usecols=["VIA_CLASE", "VIA_PAR", "VIA_NOMBRE", "NUMERO", "LATITUD", "LONGITUD"])
        

        
    except Exception as e:
        FileNotFoundError("EL fichero no existe")
    copy = df.copy()
    pattern = r"(\d{1,3})°(\d{1,2})'(\d{1,2}\.?\d*)''\s(\w)"

    copy["LATITUD"] = copy["LATITUD"].apply(lambda x: conversion_to_number(pattern,x))
    copy["LONGITUD"] = copy['LONGITUD'].apply(lambda x: conversion_to_number(pattern,x))
    return copy 
       
callejero=carga_callejero()

print(callejero)






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
    street,number = direccion.split(",")
    callejero["total_street"] = callejero["VIA_CLASE"] + " " + callejero["VIA_PAR"].fillna("") + " " + callejero["VIA_NOMBRE"]
    
    street_coincidence = callejero[callejero['total_street'] == street.upper()] 
    number_coincidence = street_coincidence[street_coincidence["NUMERO"]==int(number)]
    print(number_coincidence)
    try:

        if len(number_coincidence) <=0:
            raise AdressNotFoundError("La calle no fue encontrada")
        else:
            return (number_coincidence["LATITUD"].iloc[0],number_coincidence["LONGITUD"].iloc[0])
        
    except AdressNotFoundError as a_e:
        print(a_e)

direccion = "Calle de Alberto Aguilera, 1"
print(busca_direccion(direccion,callejero))


def fuzzy_search(direccion:str, callejero:pd.DataFrame, threshold:float) -> Tuple[float,float]:
    """
    Función que realiza una búsqueda aproximada de una dirección en el callejero.
    
    Args:
        direccion (str): Nombre completo de la calle con número, en formato "Calle, num".
        callejero (DataFrame): DataFrame con la información de las calles.
        threshold (float): Porcentaje de similitud necesario para que la coincidencia se detecte.
        
    Returns:
        Tuple[float, float]: Par de float (latitud, longitud) de la dirección más cercana encontrada.
        
    Raises:
        AdressNotFoundError: Si no se encuentra una coincidencia suficiente.
    """
    street, number = direccion.split(",")
    number = int(number.strip())
    callejero["total_street"] = callejero["VIA_CLASE"] + " " + callejero["VIA_PAR"].fillna("") + " " + callejero["VIA_NOMBRE"]
    best_match = process.extractOne(street.upper(), callejero["total_street"].unique().tolist())

    if best_match and best_match[1] >= threshold:

        matched_street = best_match[0]
        street_coincidence = callejero[callejero["total_street"] == matched_street]
        number_coincidence = street_coincidence[street_coincidence["NUMERO"] == number]
        
        if not number_coincidence.empty:
            return (number_coincidence["LATITUD"].iloc[0], number_coincidence["LONGITUD"].iloc[0])
        else:
            raise AdressNotFoundError(f"No se encontró el número {number} en {matched_street}.")
        
    else:
        raise AdressNotFoundError("No se encontró una dirección similar en el callejero.")






############## Parte 4 ##############


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
            print(f"Cargando grafo desde el archivo {MAP_FILE_NAME}")
            graph = ox.load_graphml(MAP_FILE_NAME)
            if not isinstance(graph, nx.MultiDiGraph):
                print("El argumento 'multidigrafo' debe ser un nx.MultiDiGraph.")
                print("hola")
        else:
            print("Descargando grafo desde OpenStreetMap...")
            graph = ox.graph_from_place(PLACE_NAME,network_type="drive")
            ox.save_graphml(graph,MAP_FILE_NAME)
            print(f"Grafo guardado exitosamente en {MAP_FILE_NAME}")
            if not isinstance(graph, nx.MultiDiGraph):
                    print("El argumento 'multidigrafo' debe ser un nx.MultiDiGraph.")
        fig, ax = ox.plot_graph(graph, node_size=0, edge_linewidth=0.5)
        return graph
        
    except Exception as e:
        raise ServiceNotAvailableError("No se pudo recuperar el grafo de OpenStreetMap")
    


def procesa_grafo(multidigrafo:nx.MultiDiGraph) -> nx.DiGraph:
    """ Función que recupera el quiver de calles de Madrid de OpenStreetMap.
    Args:
        multidigrafo: multidigrafo de las calles de Madrid obtenido de OpenStreetMap.
    Returns:
        nx.DiGraph: Grafo dirigido y sin bucles asociado al multidigrafo dado.
    Raises: None
    """
    if not isinstance(multidigrafo, nx.MultiDiGraph):
        print("El argumento 'multidigrafo' debe ser un nx.MultiDiGraph.")
    directed_graph = ox.convert.to_digraph(multidigrafo)
    print("termino de procesar")
    loops = list(nx.selfloop_edges(directed_graph))  # Encuentra los bucles
    directed_graph.remove_edges_from(loops)  # Elimina todos los bucles de una vez
    print("termino de eliminar bucles")
    

    if not isinstance(directed_graph, nx.DiGraph):
        print("No se construyo bien")
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
    plt.figure(figsize=(10, 10))
    nx.draw(graph, pos, node_size=10, edge_color="gray", with_labels=False)
    plt.show()