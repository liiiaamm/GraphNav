"""
grafo.py

Matemática Discreta - IMAT
ICAI, Universidad Pontificia Comillas

Grupo: GP05A
Integrantes:
    - Liam Esgueva González
    - Sergio Fernandez Cordero

Descripción:
Librería para el análisis de grafos pesados.
"""

from typing import List,Tuple,Dict,Callable,Union
import networkx as nx
import sys
from heapq import heappush, heappop

INFTY=sys.float_info.max #Distincia "infinita" entre nodos de un grafo

"""
En las siguientes funciones, las funciones de peso son funciones que reciben un grafo o digrafo y dos vértices y devuelven un real (su peso)
Por ejemplo, si las aristas del grafo contienen en sus datos un campo llamado 'valor', una posible función de peso sería:

def mi_peso(G:nx.Graph,u:object, v:object):
    return G[u][v]['valor']

y, en tal caso, para calcular Dijkstra con dicho parámetro haríamos

camino=dijkstra(G,mi_peso,origen, destino)


"""

def dijkstra(G:Union[nx.Graph, nx.DiGraph], peso:Union[Callable[[nx.Graph,object,object],float], Callable[[nx.DiGraph,object,object],float]], origen:object)-> Dict[object,object]:
    """ Calcula un Árbol de Caminos Mínimos para el grafo pesado partiendo
    del vértice "origen" usando el algoritmo de Dijkstra. Calcula únicamente
    el árbol de la componente conexa que contiene a "origen".
    
    Args:
        G (Union[nx.Graph, nx.DiGraph]): El grafo (puede ser dirigido o no).
        peso (Union[Callable, Callable]): Función de peso que recibe el grafo y dos vértices
                                          y devuelve el peso de la arista entre esos vértices.
        origen (object): vértice del grafo de origen.
    Returns:
        Dict[object,object]: Devuelve un diccionario que indica, para cada vértice alcanzable
            desde "origen", qué vértice es su padre en el árbol de caminos mínimos.
    Raises:
        TypeError: Si origen no es "hashable".
    Example:
        Si G.dijksra(1)={2:1, 3:2, 4:1} entonces 1 es padre de 2 y de 4 y 2 es padre de 3.
        En particular, un camino mínimo desde 1 hasta 3 sería 1->2->3.
    """
    # Verificar que el origen sea "hashable"
    try:
        hash(origen)
    except TypeError:
        raise TypeError("El origen no es hashable. Usa un tipo inmutable como int, str, tuple, etc.")
    
    # Inicialización
    padre = {v: None for v in G.nodes}
    d = {v: float('inf') for v in G.nodes}
    d[origen] = 0

    # Cola de prioridad para mantener las distancias
    # Añadimos un índice único para garantizar que los nodos no se comparen directamente.
    cola_prioridad = [(0, id(origen), origen)]  # (distancia_acumulada, id_unico, nodo_actual)

    while cola_prioridad:
        distancia_actual, _, nodo_actual = heappop(cola_prioridad)

        # Si la distancia es mayor que la registrada, ignorar (nodo ya procesado)
        if distancia_actual > d[nodo_actual]:
            continue

        # Relajar todas las aristas desde el nodo actual
        for vecino in G.neighbors(nodo_actual):
            w = peso(G, nodo_actual, vecino)
            nueva_distancia = distancia_actual + w

            if nueva_distancia < d[vecino]:  # Si se encuentra un camino más corto
                d[vecino] = nueva_distancia
                padre[vecino] = nodo_actual
                # Añadimos un identificador único al heap
                heappush(cola_prioridad, (nueva_distancia, id(vecino), vecino))  # Añadir a la cola

    return padre


def camino_minimo(G:Union[nx.Graph, nx.DiGraph], peso:Union[Callable[[nx.Graph,object,object],float], Callable[[nx.DiGraph,object,object],float]] ,origen:object,destino:object)->List[object]:
    """ Calcula el camino mínimo desde el vértice origen hasta el vértice
    destino utilizando el algoritmo de Dijkstra.
    
    Args:
        G (nx.Graph o nx.Digraph): grafo a grado dirigido
        peso (función): función que recibe un grafo o grafo dirigido y dos vértices del mismo y devuelve el peso de la arista que los conecta
        origen (object): vértice del grafo de origen
        destino (object): vértice del grafo de destino
    Returns:
        List[object]: Devuelve una lista con los vértices del grafo por los que pasa
            el camino más corto entre el origen y el destino. El primer elemento de
            la lista es origen y el último destino.
    Example:
        Si dijksra(G,peso,1,4)=[1,5,2,4] entonces el camino más corto en G entre 1 y 4 es 1->5->2->4.
    Raises:
        TypeError: Si origen o destino no son "hashable".
    """
    min_rut = [destino]

    try:
        acm=dijkstra(G,peso,origen)
    except:
        raise TypeError("El origen o el destino no es hashable")
    
    if destino not in acm or acm[destino] is None:
        raise TypeError("El destino introducido no está en el grafo")
    
    while min_rut[-1] != origen:
        parent = acm[min_rut[-1]]
        min_rut.append(parent)
        
    min_rut.reverse()
    return min_rut




def prim(G: nx.Graph, peso: Callable[[nx.Graph, object, object], float]) -> Dict[object, object]:
    """
    Calcula un Árbol Abarcador Mínimo (o bosque si hay componentes desconexas)
    para el grafo pesado usando el algoritmo de Prim.

    Args:
        G (nx.Graph): Grafo no dirigido.
        peso (función): Función que recibe un grafo y dos vértices, y devuelve el peso de la arista que los conecta.

    Returns:
        Dict[object, object]: Diccionario que indica el padre de cada nodo en el Árbol Abarcador Mínimo.
                              Los nodos raíces tendrán `None` como padre.
    """
    padre = {v: None for v in G.nodes}
    visitado = set()
    heap = []
    contador = 0  

    nodo_inicial = list(G.nodes)[0]
    heappush(heap, (0, contador, nodo_inicial))  
    contador += 1

    while heap:
        peso_actual, _, nodo_actual = heappop(heap)

        if nodo_actual in visitado:
            continue

        visitado.add(nodo_actual)

        for vecino in G.neighbors(nodo_actual):
            if vecino not in visitado:
                w = peso(G, nodo_actual, vecino)
                heappush(heap, (w, contador, vecino))
                contador += 1
                if padre[vecino] is None or w < peso(G, padre[vecino], vecino):
                    padre[vecino] = nodo_actual

    return padre

class UnionFind:
    """
    Implementación de una estructura de unión y búsqueda (Union-Find/Disjoint Set Union).
    """
    def __init__(self, elementos):
        self.padre = {x: x for x in elementos}  # Inicialmente, cada nodo es su propio padre
        self.rango = {x: 0 for x in elementos}  # Inicialmente, todos tienen rango 0

    def find(self, x):
        """
        Encuentra el representante del conjunto al que pertenece x.
        Aplica compresión de caminos para optimización.
        """
        if self.padre[x] != x:
            self.padre[x] = self.find(self.padre[x])  # Compresión de caminos
        return self.padre[x]

    def union(self, x, y):
        """
        Une los conjuntos de x e y. Usa unión por rango para optimización.
        """
        raiz_x = self.find(x)
        raiz_y = self.find(y)

        if raiz_x != raiz_y:
            if self.rango[raiz_x] > self.rango[raiz_y]:
                self.padre[raiz_y] = raiz_x
            elif self.rango[raiz_x] < self.rango[raiz_y]:
                self.padre[raiz_x] = raiz_y
            else:
                self.padre[raiz_y] = raiz_x
                self.rango[raiz_x] += 1


# Algoritmo de Kruskal
def kruskal(G: nx.Graph, peso: Callable[[nx.Graph, object, object], float]) -> List[Tuple[object, object]]:
    """
    Calcula un Árbol Abarcador Mínimo para el grafo usando el algoritmo de Kruskal.

    Args:
        G (nx.Graph): Grafo no dirigido.
        peso (Callable): Función que recibe un grafo y dos vértices del grafo 
                         y devuelve el peso de la arista que los conecta.

    Returns:
        List[Tuple[object, object]]: Lista de aristas que forman el Árbol Abarcador Mínimo.
    """
    # Lista para almacenar las aristas del MST
    mst = []

    # Ordenar las aristas por peso usando la función proporcionada
    aristas_ordenadas = sorted(G.edges, key=lambda edge: peso(G, edge[0], edge[1]))

    # Inicializar Union-Find para manejar los conjuntos
    uf = UnionFind(G.nodes)

    # Procesar las aristas
    for u, v in aristas_ordenadas:
        if uf.find(u) != uf.find(v):  # Si los nodos no están en el mismo conjunto
            uf.union(u, v)  # Unir los conjuntos
            mst.append((u, v))  # Añadir la arista al MST

            # Parada anticipada: Si el MST tiene |V| - 1 aristas, está completo
            if len(mst) == len(G.nodes) - 1:
                break

    return mst