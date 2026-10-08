"""Explicit Data Structures & Algorithms (DSA) Implementation.

Contains strictly from-scratch algorithmic routines and graph traversal engines
without relying on built-in Python DSA utilities (.sort(), sorted(), min(), max(),
sum(), any(), all(), collections.deque, queue.Queue).

Data Structures:
- Stack: Custom LIFO stack
- Queue: Custom FIFO queue with pointer tracking
- Graph: Custom adjacency list graph representation (directed & undirected)

Algorithms:
1. Sorting & Reduction:
   - custom_sort: In-place Selection Sort O(N^2)
   - custom_min / custom_max: Iterative linear scan O(N)
   - custom_sum: Iterative accumulation summation O(N)
   - custom_any / custom_all: Short-circuit linear verification O(N)
   - linear_search: Linear predicate scan O(N)

2. Breadth-First Search (BFS):
   - bfs_traversal: Standard level-by-level traversal using custom Queue
   - bfs_connected_components: Identifies connected clusters of touching cargo
   - bfs_accessibility_hops: Multi-source BFS computing distance layers from bin entrance
   - bfs_shortest_path: Shortest path in unweighted spatial graphs

3. Depth-First Search (DFS):
   - dfs_traversal: Iterative/recursive deep exploration using custom Stack
   - dfs_has_cycle: Three-color (White/Gray/Black) cycle detector for physical DAG validation
   - dfs_topological_sort: Post-order DFS topological sort for safe retrieval / unstacking order
   - dfs_cumulative_subtree_load: Post-order DFS subtree accumulation for compressive physical loads
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, TypeVar

T = TypeVar("T")


# ==============================================================================
# 1. CORE DATA STRUCTURES
# ==============================================================================

class Stack:
    """Explicit LIFO (Last-In-First-Out) Stack implementation written from scratch."""

    def __init__(self) -> None:
        self._items: List[Any] = []

    def push(self, item: Any) -> None:
        """Push an item onto the top of the stack."""
        self._items.append(item)

    def pop(self) -> Any:
        """Remove and return the top item. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("pop from empty Stack")
        return self._items.pop()

    def peek(self) -> Optional[Any]:
        """View the top item without removing it."""
        if self.is_empty():
            return None
        return self._items[-1]

    def is_empty(self) -> bool:
        """Check whether the stack contains zero elements."""
        return len(self._items) == 0

    def size(self) -> int:
        """Return the count of elements in the stack."""
        return len(self._items)


class Queue:
    """Explicit FIFO (First-In-First-Out) Queue implementation written from scratch.
    
    Uses an internal head-index pointer to achieve O(1) amortized dequeues without
    relying on collections.deque or external modules.
    """

    def __init__(self) -> None:
        self._items: List[Any] = []
        self._head: int = 0

    def enqueue(self, item: Any) -> None:
        """Add an item to the back of the queue."""
        self._items.append(item)

    def dequeue(self) -> Any:
        """Remove and return the front item. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("dequeue from empty Queue")
        item = self._items[self._head]
        self._head += 1
        # Periodic compaction to reclaim memory when head moves far
        if self._head > 100 and self._head * 2 >= len(self._items):
            self._items = self._items[self._head :]
            self._head = 0
        return item

    def peek(self) -> Optional[Any]:
        """View the front item without removing it."""
        if self.is_empty():
            return None
        return self._items[self._head]

    def is_empty(self) -> bool:
        """Check whether the queue is currently empty."""
        return self._head >= len(self._items)

    def size(self) -> int:
        """Return the number of remaining elements."""
        return len(self._items) - self._head


class Graph:
    """Explicit Adjacency List Graph representation written from scratch.
    
    Supports both directed (e.g. physical stacking support DAGs) and
    undirected (e.g. 3D spatial face-contact adjacency) topologies.
    """

    def __init__(self, directed: bool = False) -> None:
        self.directed = directed
        self.adj: Dict[int, List[int]] = {}
        self.nodes: List[int] = []

    def add_node(self, u: int) -> None:
        """Register a node in the graph if not already present."""
        if u not in self.adj:
            self.adj[u] = []
            self.nodes.append(u)

    def add_edge(self, u: int, v: int) -> None:
        """Add an edge from node u to node v."""
        self.add_node(u)
        self.add_node(v)
        if v not in self.adj[u]:
            self.adj[u].append(v)
        if not self.directed:
            if u not in self.adj[v]:
                self.adj[v].append(u)

    def neighbors(self, u: int) -> List[int]:
        """Return outgoing adjacent neighbors for node u."""
        return self.adj.get(u, [])


# ==============================================================================
# 2. BREADTH-FIRST SEARCH (BFS) ALGORITHMS
# ==============================================================================

def bfs_traversal(graph: Graph, start_node: int) -> List[int]:
    """Traverse graph level-by-level starting from start_node using custom Queue.
    
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    if start_node not in graph.adj:
        return []

    visited: Set[int] = {start_node}
    queue = Queue()
    queue.enqueue(start_node)
    traversal_order: List[int] = []

    while not queue.is_empty():
        curr = queue.dequeue()
        traversal_order.append(curr)

        for neighbor in graph.neighbors(curr):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.enqueue(neighbor)

    return traversal_order


def bfs_connected_components(graph: Graph) -> List[List[int]]:
    """Identify all connected clusters of cargo items using BFS.
    
    In warehouse logistics, this clusters items that form touching, contiguous
    physical cargo blocks.
    
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    visited: Set[int] = set()
    components: List[List[int]] = []

    for node in graph.nodes:
        if node not in visited:
            component: List[int] = []
            queue = Queue()
            queue.enqueue(node)
            visited.add(node)

            while not queue.is_empty():
                curr = queue.dequeue()
                component.append(curr)

                for neighbor in graph.neighbors(curr):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.enqueue(neighbor)

            components.append(component)

    return components


def bfs_accessibility_hops(graph: Graph, entrance_nodes: List[int]) -> Dict[int, int]:
    """Multi-Source BFS computing minimum unblocking depth/hops from bin opening.
    
    Determines how many item-blocking layers must be bypassed to retrieve each item:
    - Distance 0: Directly accessible at the container opening.
    - Distance k: Requires moving k preceding items to access.
    
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    depths: Dict[int, int] = {}
    queue = Queue()

    for node in entrance_nodes:
        depths[node] = 0
        queue.enqueue((node, 0))

    while not queue.is_empty():
        curr, d = queue.dequeue()

        for neighbor in graph.neighbors(curr):
            if neighbor not in depths:
                depths[neighbor] = d + 1
                queue.enqueue((neighbor, d + 1))

    # Mark unreachable internal items with -1
    for node in graph.nodes:
        if node not in depths:
            depths[node] = -1

    return depths


def bfs_shortest_path(graph: Graph, start: int, goal: int) -> Optional[List[int]]:
    """Find the shortest unweighted path between two items using BFS.
    
    Returns the list of node IDs forming the shortest path, or None if disconnected.
    """
    if start not in graph.adj or goal not in graph.adj:
        return None
    if start == goal:
        return [start]

    visited: Set[int] = {start}
    parent: Dict[int, int] = {}
    queue = Queue()
    queue.enqueue(start)

    found = False
    while not queue.is_empty():
        curr = queue.dequeue()
        if curr == goal:
            found = True
            break

        for neighbor in graph.neighbors(curr):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = curr
                queue.enqueue(neighbor)

    if not found:
        return None

    # Reconstruct path using custom Stack
    path_stack = Stack()
    curr_node = goal
    while curr_node != start:
        path_stack.push(curr_node)
        curr_node = parent[curr_node]
    path_stack.push(start)

    path: List[int] = []
    while not path_stack.is_empty():
        path.append(path_stack.pop())
    return path


# ==============================================================================
# 3. DEPTH-FIRST SEARCH (DFS) ALGORITHMS
# ==============================================================================

def dfs_traversal(graph: Graph, start_node: int) -> List[int]:
    """Iterative Depth-First Search traversal using our custom Stack.
    
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    if start_node not in graph.adj:
        return []

    visited: Set[int] = set()
    stack = Stack()
    stack.push(start_node)
    traversal_order: List[int] = []

    while not stack.is_empty():
        curr = stack.pop()
        if curr not in visited:
            visited.add(curr)
            traversal_order.append(curr)
            # Push neighbors in reverse to maintain order
            for neighbor in graph.neighbors(curr):
                if neighbor not in visited:
                    stack.push(neighbor)

    return traversal_order


def dfs_has_cycle(graph: Graph) -> bool:
    """Three-Color DFS cycle detection for Directed Physical Stacking Graphs.
    
    Colors:
    0 = WHITE (unvisited)
    1 = GRAY (currently in recursion call stack / ancestor)
    2 = BLACK (visited and completely processed)
    
    Returns True if a circular physical dependency exists (impossible physics loop),
    or False if the structure is a strictly valid Directed Acyclic Graph (DAG).
    
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    color: Dict[int, int] = {node: 0 for node in graph.nodes}

    def _dfs_visit(u: int) -> bool:
        color[u] = 1  # Mark GRAY
        for v in graph.neighbors(u):
            if color.get(v, 0) == 1:
                return True  # Back-edge detected -> Cycle found!
            if color.get(v, 0) == 0:
                if _dfs_visit(v):
                    return True
        color[u] = 2  # Mark BLACK
        return False

    for node in graph.nodes:
        if color[node] == 0:
            if _dfs_visit(node):
                return True

    return False


def dfs_topological_sort(graph: Graph) -> List[int]:
    """Post-Order DFS Topological Sort producing valid unstacking order.
    
    In warehouse operations, an item cannot be removed until all items resting on top
    of it are cleared. This DFS generates the strict LIFO retrieval sequence.
    
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    visited: Set[int] = set()
    result_stack = Stack()

    def _dfs(u: int) -> None:
        visited.add(u)
        for v in graph.neighbors(u):
            if v not in visited:
                _dfs(v)
        result_stack.push(u)

    for node in graph.nodes:
        if node not in visited:
            _dfs(node)

    # Pop from stack for topological ordering
    sorted_order: List[int] = []
    while not result_stack.is_empty():
        sorted_order.append(result_stack.pop())

    return sorted_order


def dfs_cumulative_subtree_load(
    support_graph: Graph,
    root_nodes: List[int],
    item_weights: Dict[int, float],
) -> Dict[int, float]:
    """Post-order DFS traversal computing cumulative downward compressive weight.
    
    For any base item `u`, the total downward load equals:
        Load(u) = Weight(u) + Sum_{v in Children(u)} Load(v)
        
    Allows verifying whether base objects are crushed under the weight of higher items.
    
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """
    memo: Dict[int, float] = {}
    visited: Set[int] = set()

    def _dfs_load(u: int) -> float:
        if u in memo:
            return memo[u]

        visited.add(u)
        total_load = item_weights.get(u, 0.0)

        for child in support_graph.neighbors(u):
            total_load += _dfs_load(child)

        memo[u] = total_load
        return total_load

    for root in root_nodes:
        if root not in visited:
            _dfs_load(root)

    # Ensure all nodes exist in returned dictionary
    for node in support_graph.nodes:
        if node not in memo:
            memo[node] = item_weights.get(node, 0.0)

    return memo


# ==============================================================================
# 4. BASIC DSA PRIMITIVES (PURE LOOPS & COMPARISONS)
# ==============================================================================

def custom_sort(
    arr: List[T],
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> List[T]:
    """In-place Selection Sort algorithm written explicitly from scratch."""
    n = len(arr)
    for i in range(n - 1):
        target_idx = i
        for j in range(i + 1, n):
            val_j = key(arr[j]) if key is not None else arr[j]
            val_target = key(arr[target_idx]) if key is not None else arr[target_idx]

            if reverse:
                if val_j > val_target:
                    target_idx = j
            else:
                if val_j < val_target:
                    target_idx = j

        if target_idx != i:
            arr[i], arr[target_idx] = arr[target_idx], arr[i]

    return arr


def custom_min(*args: Any) -> Any:
    """Iterative linear scan minimum."""
    if len(args) == 0:
        raise ValueError("custom_min expected at least 1 argument, got 0")
    if len(args) == 1 and hasattr(args[0], "__iter__") and not isinstance(args[0], (str, bytes)):
        elements = args[0]
    else:
        elements = args

    smallest = None
    is_first = True
    for val in elements:
        if is_first or val < smallest:
            smallest = val
            is_first = False

    if is_first:
        raise ValueError("custom_min arg is an empty sequence")
    return smallest


def custom_max(*args: Any) -> Any:
    """Iterative linear scan maximum."""
    if len(args) == 0:
        raise ValueError("custom_max expected at least 1 argument, got 0")
    if len(args) == 1 and hasattr(args[0], "__iter__") and not isinstance(args[0], (str, bytes)):
        elements = args[0]
    else:
        elements = args

    largest = None
    is_first = True
    for val in elements:
        if is_first or val > largest:
            largest = val
            is_first = False

    if is_first:
        raise ValueError("custom_max arg is an empty sequence")
    return largest


def custom_sum(iterable: Iterable[Any], start: float = 0.0) -> float:
    """Explicit accumulator summation loop."""
    accumulator = start
    for item in iterable:
        accumulator += item
    return accumulator


def custom_any(iterable: Iterable[Any]) -> bool:
    """Short-circuit existential linear scan."""
    for item in iterable:
        if item:
            return True
    return False


def custom_all(iterable: Iterable[Any]) -> bool:
    """Short-circuit universal linear scan."""
    for item in iterable:
        if not item:
            return False
    return True


def linear_search(items: Iterable[T], predicate: Callable[[T], bool]) -> Optional[T]:
    """Linear predicate scan search."""
    for elem in items:
        if predicate(elem):
            return elem
    return None
