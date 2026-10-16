
import numpy as np
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    """
    Havannah policy for 15x15 board.
    
    Args:
        me: List of (row, col) tuples for player-0 stones
        opp: List of (row, col) tuples for player-1 stones  
        valid_mask: 2D array where True marks playable cells
    
    Returns:
        A single move as (row, col)
    """
    # Create board representation
    board_size = valid_mask.shape[0]
    board = np.zeros((board_size, board_size), dtype=int)
    
    for r, c in me:
        board[r, c] = 1  # Player 0
    for r, c in opp:
        board[r, c] = 2  # Player 1
    
    # Get all valid moves
    valid_moves = [(r, c) for r in range(board_size) 
                   for c in range(board_size) 
                   if valid_mask[r, c] and board[r, c] == 0]
    
    if not valid_moves:
        # Should never happen given constraints, but just in case
        return (7, 7)
    
    # Check for immediate winning moves first
    for move in valid_moves:
        if would_win(board, move, 1):
            return move
    
    # Check for moves that block opponent wins
    for move in valid_moves:
        if would_win(board, move, 2):
            return move
    
    # Evaluate remaining moves using strategic scoring
    best_move = None
    best_score = float('-inf')
    
    for move in valid_moves:
        score = evaluate_move(board, move, valid_mask, me, opp)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else valid_moves[0]


def get_hex_neighbors(r: int, c: int, board_size: int) -> List[Tuple[int, int]]:
    """
    Get neighboring coordinates on hex grid.
    In this representation, neighbors depend on row parity.
    """
    neighbors = []
    
    # Even rows: neighbors are (r-1, c-1), (r-1, c), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)
    # Odd rows: neighbors are (r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c), (r+1, c+1)
    
    if r % 2 == 0:  # Even row
        potential = [
            (r-1, c-1), (r-1, c), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)
        ]
    else:  # Odd row
        potential = [
            (r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c), (r+1, c+1)
        ]
    
    for nr, nc in potential:
        if 0 <= nr < board_size and 0 <= nc < board_size:
            neighbors.append((nr, nc))
    
    return neighbors


def get_all_neighbors(r: int, c: int, board_size: int) -> List[Tuple[int, int]]:
    """
    Get all neighboring coordinates (simplified hex connectivity).
    """
    neighbors = []
    
    # Standard hex grid offsets
    offsets = [
        (-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)
    ]
    
    # Adjust for row parity
    if r % 2 == 0:
        # Even row
        offsets = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    else:
        # Odd row  
        offsets = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
    
    for dr, dc in offsets:
        nr, nc = r + dr, c + dc
        if 0 <= nr < board_size and 0 <= nc < board_size:
            neighbors.append((nr, nc))
    
    return neighbors


def bfs_connected(board: np.ndarray, start: Tuple[int, int], player: int, 
                  max_depth: int = 50) -> set:
    """
    Find all stones connected to start via player's stones.
    """
    board_size = board.shape[0]
    visited = set()
    queue = [start]
    
    while queue and len(visited) < max_depth:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        neighbors = get_all_neighbors(current[0], current[1], board_size)
        for neighbor in neighbors:
            if neighbor not in visited and board[neighbor] == player:
                queue.append(neighbor)
    
    return visited


def check_bridge_win(board: np.ndarray, player: int) -> bool:
    """
    Check if player has connected any two corners.
    Corners: (0,0), (0,14), (14,0), (14,14), (0,7), (14,7)
    Actually for Havannah, the 6 corner cells are the board corners.
    """
    board_size = board.shape[0]
    
    # The 6 "corners" in Havannah are actually the 6 vertices of the hexagonal board
    # For a 15x15 board represented as hex, these are approximately:
    corners = [(0, 0), (0, board_size-1), 
               (board_size//2, 0), (board_size//2, board_size-1),
               (board_size-1, 0), (board_size-1, board_size-1)]
    
    # Get all player's connected components
    player_positions = [(r, c) for r in range(board_size) 
                        for c in range(board_size) if board[r, c] == player]
    
    if len(player_positions) < 2:
        return False
    
    # Check each pair of corners
    for i, corner1 in enumerate(corners):
        for corner2 in corners[i+1:]:
            # Check if both corners are owned by player and connected
            if board[corner1] == player and board[corner2] == player:
                # Check if they're in the same connected component
                component = bfs_connected(board, corner1, player)
                if corner2 in component:
                    return True
    
    return False


def check_fork_win(board: np.ndarray, player: int) -> bool:
    """
    Check if player has connected any three edges.
    """
    board_size = board.shape[0]
    
    # Define edges (excluding corners)
    top_edge = [(0, c) for c in range(1, board_size-1)]
    bottom_edge = [(board_size-1, c) for c in range(1, board_size-1)]
    left_edge = [(r, 0) for r in range(1, board_size-1)]
    right_edge = [(r, board_size-1) for r in range(1, board_size-1)]
    
    edges = [top_edge, bottom_edge, left_edge, right_edge]
    edge_names = ['top', 'bottom', 'left', 'right']
    
    # Find which edges player controls (has at least one stone on)
    controlled_edges = []
    for edge_name, edge in zip(edge_names, edges):
        for pos in edge:
            if board[pos] == player:
                controlled_edges.append(edge_name)
                break
    
    # Need 3 different edges
    if len(set(controlled_edges)) >= 3:
        return True
    
    return False


def check_ring_win(board: np.ndarray, player: int) -> bool:
    """
    Check if player has formed a ring (loop).
    This is complex - we check for cycles in the graph of player's stones.
    """
    board_size = board.shape[0]
    
    # Get all player positions
    player_positions = [(r, c) for r in range(board_size) 
                        for c in range(board_size) if board[r, c] == player]
    
    if len(player_positions) < 6:
        return False
    
    # Simple ring detection: look for cycles of length >= 6
    # For efficiency, we use a simplified check
    for pos in player_positions:
        neighbors = get_all_neighbors(pos[0], pos[1], board_size)
        player_neighbors = [n for n in neighbors if board[n] == player]
        
        if len(player_neighbors) >= 2:
            # Found a potential ring point
            # Check if this is part of a cycle
            if is_in_cycle(board, pos, player, visited=set(), max_depth=20):
                return True
    
    return False


def is_in_cycle(board: np.ndarray, start: Tuple[int, int], player: int,
                visited: set, max_depth: int) -> bool:
    """
    Check if a position is part of a cycle using DFS.
    """
    board_size = board.shape[0]
    
    if max_depth <= 0:
        return False
    
    neighbors = get_all_neighbors(start[0], start[1], board_size)
    player_neighbors = [n for n in neighbors if board[n] == player and n not in visited]
    
    if len(player_neighbors) < 2:
        return False
    
    # Try to find a cycle starting from this node
    for neighbor in player_neighbors:
        new_visited = visited | {start, neighbor}
        path = find_path_to_node(board, start, neighbor, player, new_visited, max_depth-1)
        if path and len(path) >= 3:  # Minimum cycle length
            return True
    
    return False


def find_path_to_node(board: np.ndarray, start: Tuple[int, int], target: Tuple[int, int],
                      player: int, visited: set, max_depth: int) -> List[Tuple[int, int]]:
    """
    Find path from start to target avoiding visited nodes.
    """
    if start == target:
        return [start]
    
    if max_depth <= 0:
        return []
    
    neighbors = get_all_neighbors(start[0], start[1], board.shape[0])
    player_neighbors = [n for n in neighbors if board[n] == player and n not in visited]
    
    for neighbor in player_neighbors:
        path = find_path_to_node(board, neighbor, target, player, visited | {neighbor}, max_depth-1)
        if path:
            return [start] + path
    
    return []


def would_win(board: np.ndarray, move: Tuple[int, int], player: int) -> bool:
    """
    Check if placing a stone at move would win the game.
    """
    board_size = board.shape[0]
    r, c = move
    
    # Temporarily place the stone
    board[r, c] = player
    
    win = (check_bridge_win(board, player) or 
           check_fork_win(board, player) or 
           check_ring_win(board, player))
    
    # Remove the stone
    board[r, c] = 0
    
    return win


def evaluate_move(board: np.ndarray, move: Tuple[int, int], valid_mask: np.ndarray,
                  me: List[Tuple[int, int]], opp: List[Tuple[int, int]]) -> float:
    """
    Evaluate the strategic value of a move.
    """
    board_size = board.shape[0]
    r, c = move
    score = 0
    
    # 1. Distance to corners (important for bridge)
    corners = [(0, 0), (0, board_size-1), (board_size-1, 0), (board_size-1, board_size-1)]
    min_corner_dist = min(abs(r - corner[0]) + abs(c - corner[1]) for corner in corners)
    score += (board_size - min_corner_dist) * 2
    
    # 2. Distance to edges (important for fork)
    dist_to_top = r
    dist_to_bottom = board_size - 1 - r
    dist_to_left = c
    dist_to_right = board_size - 1 - c
    min_edge_dist = min(dist_to_top, dist_to_bottom, dist_to_left, dist_to_right)
    score += (board_size - min_edge_dist) * 1.5
    
    # 3. Central control
    center_dist = abs(r - board_size//2) + abs(c - board_size//2)
    score += (board_size - center_dist) * 0.5
    
    # 4. Connectivity to own stones
    neighbors = get_all_neighbors(r, c, board_size)
    own_neighbors = sum(1 for n in neighbors if board[n] == 1)
    opp_neighbors = sum(1 for n in neighbors if board[n] == 2)
    
    score += own_neighbors * 3  # Good to connect to own stones
    score -= opp_neighbors * 2  # Bad to be next to opponent
    
    # 5. Strategic positions
    # Check if move creates potential for ring
    if own_neighbors >= 3:
        score += 5  # Good ring potential
    
    # 6. Blocking value
    if opp_neighbors >= 2:
        score += 3  # Good defensive move
    
    # 7. Avoid creating opponent opportunities
    if opp_neighbors >= 3:
        score -= 10  # Dangerous - might help opponent
    
    # 8. Early game: prefer center, later game: prefer edges/corners
    total_stones = len(me) + len(opp)
    if total_stones < 20:  # Early game
        score += center_dist * -0.5  # Prefer center more
    else:  # Late game
        score += min_corner_dist * -0.3  # Prioritize corners slightly
    
    return score
