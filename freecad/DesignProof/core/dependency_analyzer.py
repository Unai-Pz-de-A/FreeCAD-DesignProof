# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileNotice: Part of the DesignProof addon.
"""
Dependency Analyzer
===================
Construye el grafo de dependencias de un modelo FreeCAD
y calcula metricas de complejidad.

Metricas implementadas (basadas en Contero et al. 2023,
Johnson et al. 2018, Davis 2014):

Nivel 1 (basicas):
  - Feature count, Edge count, Average degree

Nivel 2 (estructura):
  - Max depth, Cyclomatic complexity, Graph density

Uso:
    from dependency_analyzer import analyze_dependencies
    metrics = analyze_dependencies(App.ActiveDocument)
"""

import FreeCAD as App
import math
from collections import deque, defaultdict


class DependencyGraph:
    """Grafo de dependencias entre features de un modelo FreeCAD."""

    def __init__(self):
        self.nodes = {}  # {name: {"type": str, "label": str}}
        self.edges = []  # [(from_name, to_name)]
        # Listas de adyacencia
        self._out = {}   # {name: [dependencias]}
        self._in = {}    # {name: [dependientes]}

    def add_node(self, name, type_id, label):
        self.nodes[name] = {"type": type_id, "label": label}
        if name not in self._out:
            self._out[name] = []
        if name not in self._in:
            self._in[name] = []

    def add_edge(self, from_name, to_name):
        """Anade arista: from_name depende de to_name."""
        self.edges.append((from_name, to_name))
        if from_name not in self._out:
            self._out[from_name] = []
        self._out[from_name].append(to_name)
        if to_name not in self._in:
            self._in[to_name] = []
        self._in[to_name].append(from_name)

    def dependencies_of(self, name):
        """Objetos de los que 'name' depende."""
        return self._out.get(name, [])

    def dependents_of(self, name):
        """Objetos que dependen de 'name'."""
        return self._in.get(name, [])

    @property
    def roots(self):
        """Nodos sin dependencias (raices del grafo)."""
        return [n for n in self.nodes if not self._out.get(n)]

    @property
    def leaves(self):
        """Nodos de los que nada depende (hojas)."""
        return [n for n in self.nodes if not self._in.get(n)]


def build_graph(doc=None):
    """
    Construye el grafo de dependencias desde un documento FreeCAD.
    Usa obj.OutList (dependencias) y obj.InList (dependientes).
    """
    if doc is None:
        doc = App.ActiveDocument
    if doc is None:
        raise RuntimeError("No hay documento activo")

    graph = DependencyGraph()

    for obj in doc.Objects:
        graph.add_node(obj.Name, obj.TypeId, obj.Label)

    for obj in doc.Objects:
        # OutList = objetos de los que este depende
        if hasattr(obj, 'OutList'):
            for dep in obj.OutList:
                if dep.Name in graph.nodes:
                    graph.add_edge(obj.Name, dep.Name)

    return graph


# ============================================================
# TRAVERSAL: Busqueda de objetos/parametros relacionados
# ============================================================

def find_related_objects(graph, start_name, depth):
    """
    BFS bidireccional desde start_name hasta depth hops.
    Recorre tanto upstream (dependencies_of) como downstream (dependents_of).

    Args:
        graph: DependencyGraph.
        start_name: Nombre del objeto de inicio.
        depth: Saltos maximos (0 = solo el propio objeto).

    Returns:
        dict {name: (distance, direction)} donde direction es
        "origin", "upstream", "downstream" o "both".
    """
    if start_name not in graph.nodes:
        return {}

    result = {start_name: (0, "origin")}
    queue = deque([(start_name, 0)])

    while queue:
        node, dist = queue.popleft()
        if dist >= depth:
            continue

        # Upstream: objetos de los que este depende
        for neighbor in graph.dependencies_of(node):
            new_dist = dist + 1
            if neighbor not in result:
                result[neighbor] = (new_dist, "upstream")
                queue.append((neighbor, new_dist))
            elif result[neighbor][0] > new_dist:
                old_dir = result[neighbor][1]
                new_dir = "both" if old_dir == "downstream" else old_dir
                result[neighbor] = (new_dist, new_dir)
                queue.append((neighbor, new_dist))

        # Downstream: objetos que dependen de este
        for neighbor in graph.dependents_of(node):
            new_dist = dist + 1
            if neighbor not in result:
                result[neighbor] = (new_dist, "downstream")
                queue.append((neighbor, new_dist))
            elif result[neighbor][0] > new_dist:
                old_dir = result[neighbor][1]
                new_dir = "both" if old_dir == "upstream" else old_dir
                result[neighbor] = (new_dist, new_dir)
                queue.append((neighbor, new_dist))

    return result


def depth_from_node(graph, start_name):
    """
    Calcula la maxima profundidad alcanzable desde un nodo
    (en ambas direcciones). Determina el max del slider de profundidad.

    Args:
        graph: DependencyGraph.
        start_name: Nombre del objeto de inicio.

    Returns:
        int: Maxima distancia a cualquier nodo alcanzable.
    """
    if start_name not in graph.nodes:
        return 0

    max_dist = 0
    visited = {start_name}
    queue = deque([(start_name, 0)])

    while queue:
        node, dist = queue.popleft()
        max_dist = max(max_dist, dist)
        for neighbor in graph.dependencies_of(node) + graph.dependents_of(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))

    return max_dist


def find_related_parameters(graph, params, selected_param_ids, depth):
    """
    Dado parametro(s) seleccionado(s), encuentra parametros relacionados
    recorriendo el grafo de dependencias hasta depth saltos.

    Args:
        graph: DependencyGraph.
        params: Lista de Parameter detectados.
        selected_param_ids: Lista de IDs de parametros seleccionados.
        depth: Numero de saltos en el grafo.

    Returns:
        list de tuplas (Parameter, distance, direction), ordenada por
        distancia y luego por label. No incluye los parametros seleccionados.
    """
    # Mapeo: source_name -> [Parameter, ...]
    source_to_params = defaultdict(list)
    for p in params:
        source_to_params[p.source_name].append(p)

    # Encontrar source_names de los parametros seleccionados
    selected_sources = set()
    for p in params:
        if p.id in selected_param_ids:
            selected_sources.add(p.source_name)

    # BFS desde cada source de los parametros seleccionados
    merged = {}  # {obj_name: (min_distance, direction)}
    for source in selected_sources:
        related = find_related_objects(graph, source, depth)
        for name, (dist, direction) in related.items():
            if name not in merged or merged[name][0] > dist:
                merged[name] = (dist, direction)

    # Recoger parametros de los objetos encontrados, excluyendo los seleccionados
    selected_set = set(selected_param_ids)
    result = []
    for obj_name, (dist, direction) in merged.items():
        for p in source_to_params.get(obj_name, []):
            if p.id not in selected_set:
                result.append((p, dist, direction))

    result.sort(key=lambda x: (x[1], x[0].label))
    return result


# ============================================================
# METRICAS NIVEL 1: Basicas
# ============================================================

def feature_count(graph):
    """Numero total de features (nodos)."""
    return len(graph.nodes)


def edge_count(graph):
    """Numero total de dependencias (aristas)."""
    return len(graph.edges)


def average_degree(graph):
    """Grado medio del grafo: 2*E/N."""
    n = len(graph.nodes)
    if n == 0:
        return 0.0
    return 2 * len(graph.edges) / n


# ============================================================
# METRICAS NIVEL 2: Estructura
# ============================================================

def max_depth(graph):
    """
    Profundidad maxima: camino mas largo desde cualquier raiz
    hasta cualquier hoja, siguiendo las dependencias.
    """
    if not graph.nodes:
        return 0

    max_d = 0
    # BFS desde cada raiz
    for root in graph.roots:
        visited = set()
        queue = [(root, 0)]
        while queue:
            node, depth = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            max_d = max(max_d, depth)
            for child in graph.dependents_of(node):
                if child not in visited:
                    queue.append((child, depth + 1))

    return max_d


def cyclomatic_complexity(graph):
    """
    Complejidad ciclomatica de McCabe: M = E - N + 2P.
    E = aristas, N = nodos, P = componentes conexos.
    En un arbol puro M = 1; cada referencia cruzada anade 1.
    """
    n = len(graph.nodes)
    e = len(graph.edges)
    if n == 0:
        return 0

    # Calcular componentes conexos (grafo no dirigido)
    visited = set()
    components = 0
    for node in graph.nodes:
        if node in visited:
            continue
        components += 1
        # BFS en ambas direcciones
        queue = [node]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for neighbor in graph.dependencies_of(current):
                if neighbor not in visited:
                    queue.append(neighbor)
            for neighbor in graph.dependents_of(current):
                if neighbor not in visited:
                    queue.append(neighbor)

    return e - n + 2 * components


def graph_density(graph):
    """
    Densidad del grafo: 2E / (N*(N-1)).
    0 = sin aristas, 1 = completamente conectado.
    """
    n = len(graph.nodes)
    if n <= 1:
        return 0.0
    max_edges = n * (n - 1)  # Grafo dirigido
    return len(graph.edges) / max_edges


def li_entropy(graph):
    """
    Entropia de Li (basada en grados): mide la heterogeneidad
    de la estructura de dependencias.

    H = -sum( (d_i / 2m) * log2(d_i / 2m) )

    donde d_i es el grado del nodo i, m = total de aristas.
    """
    if not graph.edges:
        return 0.0

    m = len(graph.edges)
    two_m = 2 * m

    # Calcular grado de cada nodo (in + out)
    degrees = {}
    for name in graph.nodes:
        d = len(graph.dependencies_of(name)) + len(graph.dependents_of(name))
        degrees[name] = d

    entropy = 0.0
    for name, d in degrees.items():
        if d > 0:
            p = d / two_m
            entropy -= p * math.log2(p)

    return entropy


# ============================================================
# ANALISIS COMPLETO
# ============================================================

def analyze_dependencies(doc=None):
    """
    Realiza el analisis completo de dependencias y devuelve
    todas las metricas.

    Returns:
        dict con metricas y el grafo.
    """
    graph = build_graph(doc)

    metrics = {
        # Nivel 1
        "feature_count": feature_count(graph),
        "edge_count": edge_count(graph),
        "average_degree": round(average_degree(graph), 2),
        # Nivel 2
        "max_depth": max_depth(graph),
        "cyclomatic_complexity": cyclomatic_complexity(graph),
        "graph_density": round(graph_density(graph), 4),
        "li_entropy": round(li_entropy(graph), 2),
    }

    return {"metrics": metrics, "graph": graph}


def print_metrics(metrics):
    """Imprime las metricas en formato legible."""
    print("\n=== Metricas de Complejidad del Modelo ===")
    print(f"  Features (nodos):          {metrics['feature_count']}")
    print(f"  Dependencias (aristas):    {metrics['edge_count']}")
    print(f"  Grado medio:               {metrics['average_degree']}")
    print(f"  Profundidad maxima:         {metrics['max_depth']}")
    print(f"  Complejidad ciclomatica:    {metrics['cyclomatic_complexity']}")
    print(f"  Densidad del grafo:         {metrics['graph_density']}")
    print(f"  Entropia de Li:             {metrics['li_entropy']}")


def print_dependency_tree(graph):
    """Imprime las dependencias de cada objeto."""
    print("\n=== Dependencias por objeto ===")
    for name in graph.nodes:
        deps = graph.dependencies_of(name)
        deps_str = ", ".join(deps) if deps else "(ninguna)"
        node_type = graph.nodes[name]["type"].split("::")[-1]
        print(f"  {name:25s} [{node_type:15s}] -> {deps_str}")
