import tkinter as tk
from tkinter import messagebox
import callejero as c
import grafo_pesado  # Asumo que tu módulo con Dijkstra se llama "grafo_pesado"
import osmnx as ox
import networkx as nx

# Función para reconstruir la ruta a partir del diccionario de padres
def reconstruir_ruta(padre, origen, destino):
    ruta = []
    actual = destino
    while actual is not None:
        ruta.append(actual)
        actual = padre[actual]
    ruta.reverse()
    if ruta[0] != origen:
        raise ValueError(f"No existe un camino desde {origen} hasta {destino}.")
    return ruta

class GPSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS Navigation System")
        
        # Input fields
        tk.Label(root, text="Dirección de Inicio:").grid(row=0, column=0, padx=10, pady=5)
        self.start_entry = tk.Entry(root, width=50)
        self.start_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="Dirección de Destino:").grid(row=1, column=0, padx=10, pady=5)
        self.end_entry = tk.Entry(root, width=50)
        self.end_entry.grid(row=1, column=1, padx=10, pady=5)

        # Buttons
        tk.Button(root, text="Cargar Grafo", command=self.load_graph).grid(row=2, column=0, pady=10)
        tk.Button(root, text="Calcular Ruta", command=self.calculate_route).grid(row=2, column=1, pady=10)
        tk.Button(root, text="Explorar Grafo", command=self.explore_graph).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Output
        self.result_label = tk.Label(root, text="Resultados aparecerán aquí", wraplength=500, justify="left")
        self.result_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        self.graph = None
        self.street_data = None

    def load_graph(self):
        try:
            self.street_data = c.carga_callejero()
            self.graph = c.carga_grafo()
            self.processed_graph = c.procesa_grafo(self.graph)
            self.result_label.config(text="Grafo cargado y procesado exitosamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el grafo: {e}")

    def calculate_route(self):
        if not self.graph or not self.street_data:
            messagebox.showerror("Error", "Primero debe cargar el grafo.")
            return
        
        start = self.start_entry.get()
        end = self.end_entry.get()
        
        try:
            # Obtener coordenadas de las direcciones
            start_coords = c.busca_direccion(start, self.street_data)
            end_coords = c.busca_direccion(end, self.street_data)
            
            # Encontrar los nodos más cercanos en el grafo
            start_node = ox.distance.nearest_nodes(self.processed_graph, start_coords[1], start_coords[0])
            end_node = ox.distance.nearest_nodes(self.processed_graph, end_coords[1], end_coords[0])
            
            # Ejecutar Dijkstra
            peso_funcion = lambda G, u, v: G[u][v].get('length', float('inf'))  # Usamos la longitud como peso
            padres = grafo_pesado.dijkstra(self.processed_graph, peso_funcion, start_node)
            
            # Reconstruir la ruta
            ruta = reconstruir_ruta(padres, start_node, end_node)
            ruta_nodos = " -> ".join(map(str, ruta))
            
            self.result_label.config(text=f"Ruta más corta:\n{ruta_nodos}")
        
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo calcular la ruta: {e}")

    def explore_graph(self):
        if not self.graph:
            messagebox.showerror("Error", "Primero debe cargar el grafo.")
            return
        
        try:
            c.explora_grafo(self.processed_graph)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo explorar el grafo: {e}")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = GPSApp(root)
    root.mainloop()
