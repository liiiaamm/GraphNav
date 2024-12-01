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
class NoWayFoundError (Exception):
    pass
from typing import List,Tuple,Dict,Callable,Union
import networkx as nx
import sys
from heapq import heappush, heappop
Normal = "\033[0m"
Azul = "\033[34m"
Rojo = "\033[31m"
Verde = "\033[32m"
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
        TypeError: Si origen no es "hashable"
        NoWayFoundError: Si no encuentra el camino
        
    Example:
        Si G.dijksra(1)={2:1, 3:2, 4:1} entonces 1 es padre de 2 y de 4 y 2 es padre de 3.
        En particular, un camino mínimo desde 1 hasta 3 sería 1->2->3.
    """
    #Se verifica que el origen sea "hashable"
    if origen not in G:
        raise NoWayFoundError(f"El nodo de origen no está en el grafo o no tiene camino definido.")
    try:
        hash(origen)
    except:
        raise TypeError("El origen no es hashable. Usa un tipo inmutable como int, str, tuple, etc.")
    
    # Inicialización
    padre = {v: None for v in G.nodes}
    d = {v: float('inf') for v in G.nodes}
    d[origen] = 0

    #Se pone la cola de prioridad
    #Se añade un solo índice para asegurarse de que los nodos no se comparen directamente (puesto que hay str e int).
    cola_prioridad = [(0, id(origen), origen)]  # (distancia_acumulada, id_unico, nodo_actual)

    while cola_prioridad:
        distancia_actual, _, nodo_actual = heappop(cola_prioridad)
        #Si la distancia es mayor que la registrada significa que el nodo ya se ha analizado
        if distancia_actual > d[nodo_actual]:
            continue
        for vecino in G.neighbors(nodo_actual):
            #Se calcula el peso de los nodos vecinos
            w = peso(G, nodo_actual, vecino)
            nueva_distancia = distancia_actual + w
            #Esto por si se encuentra un camino más corto
            if nueva_distancia < d[vecino]:  
                d[vecino] = nueva_distancia
                padre[vecino] = nodo_actual
                #Se le añade un id único al heap y se introduce en la cola
                heappush(cola_prioridad, (nueva_distancia, id(vecino), vecino)) 

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
        NoWayFoundError: Si no encuentra el camino
    """
    min_rut = [destino]
    #Se ejecuta dijkstra
    if origen == destino:
        print(f"{Rojo}El origen y destino son iguales{Normal}")
        return None
    try:
        acm = dijkstra(G, peso, origen)
    except TypeError as e:
        raise e
    except NoWayFoundError as e:
        raise e
    
    if destino not in acm or acm[destino] is None:
        raise NoWayFoundError("El destino introducido no está en el grafo")
    #Se itera sobre la lista al revés hasta llegar al nodo inicial
    while min_rut[-1] != origen:
        parent = acm[min_rut[-1]]
        if parent is None and min_rut[-1] != origen:
            raise NoWayFoundError(f"No se encontró un camino desde {origen} hasta {destino}.")
        min_rut.append(parent)
    #Se le da la vuelta a la lista para ponerla en orden y se devuelve    
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
    padre = {}
    try:
        if not G.nodes:
            return padre 
        visitado = set()
        heap = []
        contador = 0
        #Se itera sobre todos los nodos (por si es un árbol)
        for nodo_inicial in G.nodes:
            if nodo_inicial in visitado:
                continue
            padre[nodo_inicial] = None
            heappush(heap, (0, contador, nodo_inicial))
            contador += 1
            while heap:
                try:
                    peso_actual, _, nodo_actual = heappop(heap)
                except IndexError:
                    print("El nodo no tiene peso asignado")
                    break  #Si está vacío
                if nodo_actual in visitado:
                    continue
                #Se añaden los nodos visitados al total
                visitado.add(nodo_actual)
                #Se observan los vecinos y escogemos el de menor peso
                for vecino in G.neighbors(nodo_actual):
                    if vecino not in visitado:
                        try:
                            w = peso(G, nodo_actual, vecino)
                        except Exception as e:
                            print(f"Error al calcular el peso entre dos nodos")
                            continue
                        heappush(heap, (w, contador, vecino))
                        contador += 1
                        if vecino not in padre or (padre[vecino] is not None and w < peso(G, padre[vecino], vecino)):
                            padre[vecino] = nodo_actual
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    return padre

class UnionFind:
    """Clase Union-Find para el algoritmo de Kruskal."""
    def __init__(self, elementos):
        self.padre = {x: x for x in elementos}
        self.rango = {x: 0 for x in elementos}

    def find(self, x):
        """Encuentra el representante del conjunto al que pertenece x."""
        if self.padre[x] != x:
            self.padre[x] = self.find(self.padre[x])
        return self.padre[x]

    def union(self, x, y):
        """Une los conjuntos de x e y."""
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
    mst = []
    try:
        if not G.edges:
            #Devuelve una lista vacía si el grafo no tiene aristas
            return mst  
        #Se ordenan las aristas por peso
        aristas_ordenadas = sorted(G.edges, key=lambda edge: peso(G, edge[0], edge[1]))
        uf = UnionFind(G.nodes)
        #Se itera sobre las aristas ordenadas
        for u, v in aristas_ordenadas:
            try:
                if uf.find(u) != uf.find(v): 
                    uf.union(u, v) 
                    mst.append((u, v))  
            except KeyError as e:
                print(f"Error: nodo no encontrado en Union-Find.")
            except Exception as e:
                print(f"Error al procesar la arista ")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    return mst