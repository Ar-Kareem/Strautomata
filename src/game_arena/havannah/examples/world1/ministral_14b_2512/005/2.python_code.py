
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Convert to numpy arrays for easier manipulation
    board_size = len(valid_mask)
    my_stones = np.array(me)
    opp_stones = np.array(opp)

    # First check for immediate winning moves
    winning_move = find_winning_move(my_stones, opp_stones, valid_mask)
    if winning_move is not None:
        return winning_move

    # Then check if opponent has a winning move we need to block
    blocking_move = find_blocking_move(my_stones, opp_stones, valid_mask)
    if blocking_move is not None:
        return blocking_move

    # If no immediate threats, evaluate all valid moves
    valid_moves = np.argwhere(valid_mask)
    if len(valid_moves) == 0:
        # Shouldn't happen per problem statement, but handle gracefully
        return (0, 0)

    # Evaluate each move using our scoring system
    scores = []
    for move in valid_moves:
        scores.append(evaluate_move(my_stones, opp_stones, move[0], move[1], valid_mask))

    # Select the move with highest score
    best_move_idx = np.argmax(scores)
    return tuple(valid_moves[best_move_idx])

def find_winning_move(my_stones, opp_stones, valid_mask):
    """Check if placing a stone would create a winning pattern"""
    for move in np.argwhere(valid_mask):
        if is_winning_position(my_stones, opp_stones, move[0], move[1]):
            return (move[0], move[1])
    return None

def find_blocking_move(my_stones, opp_stones, valid_mask):
    """Check if opponent has a winning move we need to block"""
    for move in np.argwhere(valid_mask):
        if is_winning_position(opp_stones, my_stones, move[0], move[1]):
            return (move[0], move[1])
    return None

def is_winning_position(stones, opponent_stones, row, col, valid_mask=None):
    """Check if placing a stone at (row,col) creates a winning pattern"""
    # Create a temporary board with the new stone
    temp_stones = stones.tolist() + [(row, col)]
    temp_stones = np.array(temp_stones)

    # Check for ring
    if has_ring(temp_stones):
        return True

    # Check for bridge
    if has_bridge(temp_stones):
        return True

    # Check for fork
    if has_fork(temp_stones):
        return True

    return False

def has_ring(stones):
    """Check if stones form a ring (loop)"""
    if len(stones) < 3:
        return False

    # Build adjacency graph
    graph = build_hex_graph(stones)

    # Check for cycles (rings)
    visited = set()
    recursion_stack = set()

    def has_cycle(node):
        visited.add(node)
        recursion_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in recursion_stack:
                return True
        recursion_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if has_cycle(node):
                return True
    return False

def has_bridge(stones):
    """Check if stones connect any two corners"""
    corners = [(0,0), (0,14), (14,0), (14,14), (0,7), (14,7)]
    corner_set = set(corners)

    # Find which corners are connected
    connected_corners = set()
    graph = build_hex_graph(stones)

    for corner in corners:
        if corner in graph:
            # BFS to find all connected corners
            queue = deque([corner])
            visited = set()
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                if node in corner_set:
                    connected_corners.add(node)
                for neighbor in graph.get(node, []):
                    if neighbor not in visited:
                        queue.append(neighbor)

    # Check if we have at least two connected corners
    return len(connected_corners) >= 2

def has_fork(stones):
    """Check if stones connect three edges (not corners)"""
    edges = set()
    # Top edge (row 0, cols 1-13)
    edges.update([(0, col) for col in range(1, 14)])
    # Bottom edge (row 14, cols 1-13)
    edges.update([(14, col) for col in range(1, 14)])
    # Left edge (cols 0, rows 1-13)
    edges.update([(row, 0) for row in range(1, 14)])
    # Right edge (cols 14, rows 1-13)
    edges.update([(row, 14) for row in range(1, 14)])

    # Find which edges are connected
    connected_edges = set()
    graph = build_hex_graph(stones)

    for edge in edges:
        if edge in graph:
            # BFS to find all connected edges
            queue = deque([edge])
            visited = set()
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                if node in edges:
                    connected_edges.add(node)
                for neighbor in graph.get(node, []):
                    if neighbor not in visited:
                        queue.append(neighbor)

    # Check if we have at least three connected edges
    return len(connected_edges) >= 3

def build_hex_graph(stones):
    """Build adjacency graph for hexagonal grid"""
    graph = {}
    for stone in stones:
        row, col = stone
        neighbors = get_hex_neighbors(row, col)
        graph[(row, col)] = []
        for neighbor in neighbors:
            if neighbor in stones:
                graph[(row, col)].append(neighbor)
    return graph

def get_hex_neighbors(row, col):
    """Get all six hexagonal neighbors of a cell"""
    neighbors = []
    # Same column neighbors
    if row > 0:
        neighbors.append((row-1, col))
    if row < 14:
        neighbors.append((row+1, col))

    # Left column neighbors
    if col > 0:
        if row > 0:
            neighbors.append((row-1, col-1))
        if row < 14:
            neighbors.append((row+1, col-1))

    # Right column neighbors
    if col < 14:
        if row > 0:
            neighbors.append((row-1, col+1))
        if row < 14:
            neighbors.append((row+1, col+1))

    return neighbors

def evaluate_move(my_stones, opp_stones, row, col, valid_mask):
    """Evaluate how good a move is using multiple factors"""
    score = 0

    # 1. Positional value (center control)
    center_distance = np.sqrt((row - 7)**2 + (col - 7)**2)
    score += 100 - center_distance * 5

    # 2. Potential to create a ring
    score += evaluate_ring_potential(my_stones, row, col) * 50

    # 3. Potential to create a bridge
    score += evaluate_bridge_potential(my_stones, row, col) * 40

    # 4. Potential to create a fork
    score += evaluate_fork_potential(my_stones, row, col) * 30

    # 5. Blocking opponent's potential threats
    score -= evaluate_opponent_threats(opp_stones, row, col) * 20

    # 6. Hexagonal connectivity
    score += evaluate_connectivity(my_stones, row, col) * 10

    return score

def evaluate_ring_potential(stones, row, col):
    """Evaluate potential to create a ring with this move"""
    # Check if this move connects two existing stones that are part of a potential ring
    neighbors = get_hex_neighbors(row, col)
    connected = 0
    for neighbor in neighbors:
        if neighbor in stones:
            connected += 1

    # If we connect 2 existing stones, we might complete a ring
    if connected >= 2:
        # Check if these two stones are already connected through other paths
        # If not, this move could complete a ring
        graph = build_hex_graph(stones)
        if len(graph) >= 2:  # At least two stones exist
            # Find the two connected neighbors
            connected_neighbors = [n for n in neighbors if n in stones]
            if len(connected_neighbors) >= 2:
                # Check if they're already connected
                visited = set()
                queue = deque([connected_neighbors[0]])
                while queue:
                    node = queue.popleft()
                    if node == connected_neighbors[1]:
                        return 0  # Already connected
                    if node in visited:
                        continue
                    visited.add(node)
                    for neighbor in graph.get(node, []):
                        if neighbor not in visited:
                            queue.append(neighbor)
                return 1  # Not connected, could complete ring
    return 0

def evaluate_bridge_potential(stones, row, col):
    """Evaluate potential to create a bridge with this move"""
    corners = [(0,0), (0,14), (14,0), (14,14), (0,7), (14,7)]
    corner_set = set(corners)

    # Check if this move connects to any corners
    connected_corners = 0
    for neighbor in get_hex_neighbors(row, col):
        if neighbor in corner_set and neighbor in stones:
            connected_corners += 1

    # If we connect to 1 corner, check if we can connect to another
    if connected_corners == 1:
        # Find the connected corner
        connected_corner = [n for n in get_hex_neighbors(row, col) if n in corner_set and n in stones][0]

        # Check if we can connect to another corner
        graph = build_hex_graph(stones)
        graph[(row, col)] = [n for n in get_hex_neighbors(row, col) if n in stones]

        # BFS from the connected corner
        visited = set()
        queue = deque([connected_corner])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            if node in corner_set and node != connected_corner:
                return 2  # Can connect to another corner
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)

    return 0

def evaluate_fork_potential(stones, row, col):
    """Evaluate potential to create a fork with this move"""
    edges = set()
    # Top edge (row 0, cols 1-13)
    edges.update([(0, col) for col in range(1, 14)])
    # Bottom edge (row 14, cols 1-13)
    edges.update([(14, col) for col in range(1, 14)])
    # Left edge (cols 0, rows 1-13)
    edges.update([(row, 0) for row in range(1, 14)])
    # Right edge (cols 14, rows 1-13)
    edges.update([(row, 14) for row in range(1, 14)])

    # Check how many edges this move connects to
    connected_edges = 0
    for neighbor in get_hex_neighbors(row, col):
        if neighbor in edges and neighbor in stones:
            connected_edges += 1

    # If we connect to 2 edges, check if we can connect to a third
    if connected_edges >= 2:
        # Build graph including this move
        temp_stones = stones.tolist() + [(row, col)]
        temp_stones = np.array(temp_stones)
        graph = build_hex_graph(temp_stones)

        # Find all connected edges
        connected_edge_set = set()
        for edge in edges:
            if edge in graph:
                # BFS to find all connected edges
                visited = set()
                queue = deque([edge])
                while queue:
                    node = queue.popleft()
                    if node in visited:
                        continue
                    visited.add(node)
                    if node in edges:
                        connected_edge_set.add(node)
                    for neighbor in graph.get(node, []):
                        if neighbor not in visited:
                            queue.append(neighbor)

        return len(connected_edge_set)
    return 0

def evaluate_opponent_threats(opp_stones, row, col):
    """Evaluate how much this move blocks opponent's threats"""
    # Check if opponent has potential winning moves that this move blocks
    threats = 0

    # Check if opponent would win with this move (which we're blocking)
    if is_winning_position(opp_stones, opp_stones, row, col):
        threats += 10

    # Check if opponent has potential ring, bridge, or fork that this move blocks
    # (This is simplified - in practice would need more sophisticated analysis)
    neighbors = get_hex_neighbors(row, col)
    for neighbor in neighbors:
        if neighbor in opp_stones:
            # Check if this neighbor is part of opponent's potential threat
            if evaluate_ring_potential(opp_stones, neighbor[0], neighbor[1]) > 0:
                threats += 2
            if evaluate_bridge_potential(opp_stones, neighbor[0], neighbor[1]) > 0:
                threats += 3
            if evaluate_fork_potential(opp_stones, neighbor[0], neighbor[1]) > 0:
                threats += 4

    return threats

def evaluate_connectivity(stones, row, col):
    """Evaluate how much this move improves our connectivity"""
    # Check how many existing stones this move connects to
    neighbors = get_hex_neighbors(row, col)
    connected = 0
    for neighbor in neighbors:
        if neighbor in stones:
            connected += 1

    # Check if this move connects previously disconnected components
    if connected >= 2:
        # Build graph without this move
        graph = build_hex_graph(stones)

        # Find the two connected neighbors
        connected_neighbors = [n for n in neighbors if n in stones]
        if len(connected_neighbors) >= 2:
            # Check if they're already connected
            visited = set()
            queue = deque([connected_neighbors[0]])
            while queue:
                node = queue.popleft()
                if node == connected_neighbors[1]:
                    return 0  # Already connected
                if node in visited:
                    continue
                visited.add(node)
                for neighbor in graph.get(node, []):
                    if neighbor not in visited:
                        queue.append(neighbor)
            return 5  # Connects previously disconnected components

    return connected
