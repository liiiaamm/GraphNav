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

import heapq #Librería para la creación de colas de prioridad

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
    
    try:
        hash(origen)
    except TypeError:
        raise TypeError("El origen no es hashable. Usa un tipo inmutable como int, str, tuple, etc.")

    padre = {v: None for v in G.nodes}
    d = {v: float('inf') for v in G.nodes}
    visitado = {v: False for v in G.nodes}

    d[origen] = 0
    Q = list(G.nodes)  #Inicializamos la cola como una lista de nodos

    while Q:
        #Encontrar el nodo con la menor distancia en Q
        v = min(Q, key=lambda node: d[node])

        Q.remove(v)  #Eliminarlo de la cola
        visitado[v] = True

        for vecino in G.neighbors(v):
            if not visitado[vecino]:
                w = peso(G, v, vecino)

                #Relajación de la arista
                if d[vecino] > d[v] + w:
                    d[vecino] = d[v] + w
                    padre[vecino] = v

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
    # Diccionarios de padre y coste mínimo para cada nodo
    padre = {v: None for v in G.nodes}  
    coste_minimo = {v: float('inf') for v in G.nodes}
    
    # Iniciamos el algoritmo desde un vértice arbitrario (usamos el primer nodo)
    raiz = list(G.nodes)[0]
    coste_minimo[raiz] = 0  # El costo del nodo raíz es 0
    
    # Lista de nodos visitados
    visitado = set()
    
    while len(visitado) < len(G.nodes):
        # Seleccionamos el nodo con el coste mínimo
        v = None
        for nodo in G.nodes:
            if nodo not in visitado:
                if v is None or coste_minimo[nodo] < coste_minimo[v]:
                    v = nodo
        
        # Marcar el nodo como visitado
        visitado.add(v)
        
        # Explorar los vecinos del nodo seleccionado
        for vecino in G.neighbors(v):
            if vecino not in visitado:
                w = peso(G, v, vecino)
                # Si encontramos un camino más barato hacia el vecino, actualizamos
                if w < coste_minimo[vecino]:
                    coste_minimo[vecino] = w
                    padre[vecino] = v
    
    return padre


     

def kruskal(G:nx.Graph, peso:Callable[[nx.Graph,object,object],float])-> List[Tuple[object,object]]:
    """ Calcula un Árbol Abarcador Mínimo para el grafo
    usando el algoritmo de Kruskal.
    
    Args:
        G (nx.Graph): grafo
        peso (función): función que recibe un grafo y dos vértices del grafo y devuelve el peso de la arista que los conecta
    Returns:
        List[Tuple[object,object]]: Devuelve una lista [(s1,t1),(s2,t2),...,(sn,tn)]
            de los pares de vértices del grafo que forman las aristas
            del arbol abarcador mínimo.
    Raises: None
    Example:
        En el ejemplo anterior en que prim(G,peso)={1:None, 2:1, 3:2, 4:1} podríamos tener, por ejemplo,
        kruskal(G,peso)=[(1,2),(1,4),(3,2)]
    """
    if not isinstance(G, nx.Graph):
        raise ValueError("El grafo debe ser no dirigido (nx.Graph).")
    
    # Lista de aristas ordenada por peso
    aristas = sorted(G.edges(data=True), key=lambda e: peso(G, e[0], e[1]))
    
    # Inicialización de componentes
    componentes = {nodo: {nodo} for nodo in G.nodes}
    aam = []  # Lista de aristas del Árbol Abarcador Mínimo
    
    for u, v, _ in aristas:
        # Si los nodos no pertenecen a la misma componente
        if componentes[u] != componentes[v]:
            aam.append((u, v))
            
            # Unificar componentes
            nueva_componente = componentes[u].union(componentes[v])
            for nodo in nueva_componente:
                componentes[nodo] = nueva_componente
    
    return aam