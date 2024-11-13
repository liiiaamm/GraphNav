"""
callejero.py

Matemática Discreta - IMAT
ICAI, Universidad Pontificia Comillas

Grupo: GP05A
Integrantes:
    - Liam Esgueva González
    - Sergio Fernandez Cordero

Descripción:
Librería con herramientas y clases auxiliares necesarias para la representación de un callejero en un grafo.

Complétese esta descripción según las funcionalidades agregadas por el grupo.
"""

import osmnx as ox
import networkx as nx
import pandas as pd
import re
from typing import Tuple



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

        df = pd.read_csv("direcciones.csv", sep=";", encoding="ISO-8859-1",usecols=["VIA_CLASE", "VIA_PAR", "VIA_NOMBRE", "NUMERO", "LATITUD", "LONGITUD"])
        

        
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






############## Parte 4 ##############


def carga_grafo() -> nx.MultiDiGraph:
    """ Función que recupera el quiver de calles de Madrid de OpenStreetMap.
    Args: None
    Returns:
        nx.MultiDiGraph: Quiver de las calles de Madrid.
    Raises:
        ServiceNotAvailableError: Si no es posible recuperar el grafo de OpenStreetMap.
    """
    pass


def procesa_grafo(multidigrafo:nx.MultiDiGraph) -> nx.DiGraph:
    """ Función que recupera el quiver de calles de Madrid de OpenStreetMap.
    Args:
        multidigrafo: multidigrafo de las calles de Madrid obtenido de OpenStreetMap.
    Returns:
        nx.DiGraph: Grafo dirigido y sin bucles asociado al multidigrafo dado.
    Raises: None
    """
    pass