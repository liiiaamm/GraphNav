import callejero as c
import osmnx as ox
import networkx as nx
import pandas as pd
import re
from typing import Tuple
import os
import time

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
def seleccion_interactiva(callejero: pd.DataFrame) -> Tuple[str, Tuple[float, float]]:
    """
    Permite al usuario introducir la dirección de forma interactiva con sugerencias en tiempo real.
    
    Args:
        callejero (DataFrame): DataFrame con las direcciones.
        threshold (float): Umbral de similitud para las coincidencias aproximadas.
        
    Returns:
        Tuple[str, Tuple[float, float]]: La dirección seleccionada y sus coordenadas (lat, lon).
    """
    while True:
        try:
            print("\nIntroduce el nombre de la calle seguido del número (ejemplo: 'Calle Mayor, 10'):")
            direction_input = input("Dirección: ").strip()
            print("Búsquedas recientes: ")
            file_path = "searchs/recent_searchs.txt"

            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "r") as s:
                    print("Contenido del archivo:")
                    for line in s.readlines()[::-1]:
                        print(line.rstrip())
            
            coords = c.fuzzy_search(direction_input, callejero)
            
            print(f"\nSe encontró una coincidencia cercana para: '{direction_input}'")
            print(f"Coordenadas: {coords}")
            confirmacion = input("¿Es correcta esta dirección? (S/N): ").strip().lower()
            if confirmacion == "s":
                with open(file_path,"a") as s:
                    s.write(direction_input +"\n")

                return direction_input, coords
        except c.AdressNotFoundError as e:
            print(f"Error: {e}")
            print("Por favor, intenta de nuevo con un nombre más completo o correcto.")


def main():
    opt_title = input("Desea ver el título continuamente? Escribe S para ver el título continuamente")
    if opt_title.upper() == "S":
        print(GPS)
        streetmap = step_with_header("Cargando callejero...", c.carga_callejero)
        time.sleep(2)
        direction = step_with_header("Buscando dirección: Calle de Alberto Aguilera, 1...", seleccion_interactiva, streetmap)
        time.sleep(4)
        graph = step_with_header("Cargando grafo...", c.carga_grafo)
        time.sleep(2)
        directed_graph = step_with_header("Procesando grafo...", c.procesa_grafo, graph)
        time.sleep(2)
        step_with_header("Explorando grafo...", c.explora_grafo, directed_graph)
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
    
