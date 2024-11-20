import callejero as c
import osmnx as ox
import networkx as nx
import pandas as pd
import re
from typing import Tuple
import os

if __name__=="__main__":
    street=c.carga_callejero()
    direction=c.busca_direccion("Calle de Alberto Aguilera, 1",street)
    graph=c.carga_grafo()
    directed_graph=c.procesa_grafo(graph)
    c.dibuja_grafo(graph)


