import pandas as pd
from typing import Tuple
import callejero as c

class AdressNotFoundError(Exception):
    """Excepción personalizada para direcciones no encontradas."""
    pass
def seleccion_interactiva(callejero: pd.DataFrame, threshold: float = 80) -> Tuple[str, Tuple[float, float]]:
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
            with open("search/recent_searchs.txt","r") as s:
                for line in s.readlines():
                    print(line.rstrip())

            while "," not in direction_input:
                print("Recuerda meter la coma y el número!!")
                direction_input = input("Introduce otra vez la dirección: ")

                while not direction_input.split(",")[1].isnumeric():
                    print("Recuerda la estructura! 'Calle Mayor, 10'. El número debe de ser formato numérico")
                    direction_input = input("Introduce otra vez la dirección: ")
            
            # Realizar búsqueda aproximada
            coords = c.fuzzy_search(direction_input, callejero, threshold)
            
            # Confirmar la dirección al usuario
            print(f"\nSe encontró una coincidencia cercana para: '{direction_input}'")
            print(f"Coordenadas: {coords}")
            confirmacion = input("¿Es correcta esta dirección? (S/N): ").strip().lower()
            if confirmacion == "s":
                with open("search/recent_searchs.txt","a") as s:
                    s.write(direction_input +"\n")

                return direction_input, coords
        except AdressNotFoundError as e:
            print(f"Error: {e}")
            print("Por favor, intenta de nuevo con un nombre más completo o correcto.")


def main():
    print("Cargando direcciones desde 'direcciones.csv'...")
    callejero = pd.read_csv("direcciones.csv")
    
    print("\nSelecciona la dirección de origen:")
    origen, coords_origen = seleccion_interactiva(callejero)
    print(f"Origen seleccionado: {origen}, Coordenadas: {coords_origen}")
    
    print("\nSelecciona la dirección de destino:")
    destino, coords_destino = seleccion_interactiva(callejero)
    print(f"Destino seleccionado: {destino}, Coordenadas: {coords_destino}")
    
    print("\nProceso completado. Gracias por usar GPS!")

if __name__ == "__main__":
    main()