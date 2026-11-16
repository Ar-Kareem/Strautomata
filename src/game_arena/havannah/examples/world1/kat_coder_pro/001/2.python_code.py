
import numpy as np
from typing import List, Tuple, Set
import random

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    """
    Main policy function for Havannah game
    Returns the best move based on evaluation of the board state
    """
    # Convert lists to sets for faster lookups
    me_set = set(me)
    opp_set = set(opp)
    board_size = 15
    
    # Get all valid moves
    valid_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
    
    if not valid_moves:
        # Fallback - should not happen in normal play
        return (0, 0)
    
    # Immediate win check
    winning_move = find_winning_move(me_set, opp_set, valid_moves)
    if winning_move:
        return winning_move
    
    # Block opponent's winning move
    blocking_move = find_winning_move(opp_set, me_set, valid_moves)
    if blocking_move:
        return blocking_move
    
    # Evaluate all moves
    best_score = -float('inf')
    best_move = valid_moves[0]
    
    for move in valid_moves:
        score = evaluate_move(move, me_set, opp_set, valid_mask)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def find_winning_move(player_stones: Set[Tuple[int, int]], opponent_stones: Set[Tuple[int, int]], valid_moves: List[Tuple[int, int]]) -> None:
    """Check if any valid move creates a winning position for the player"""
    for move in valid_moves:
        # Temporarily add the move to player's stones
        test_stones = player_stones.copy()
        test_stones.add(move)
        
        if is_winning_position(test_stones, opponent_stones):
            return move
    
    return None

def is_winning_position(player_stones: Set[Tuple[int, int]], opponent_stones: Set[Tuple[int, int]]) -> bool:
    """Check if the player has won with their current stones"""
    if has_ring(player_stones):
        return True
    if has_bridge(player_stones):
        return True
    if has_fork(player_stones):
        return True
    return False

def has_ring(player_stones: Set[Tuple[int, int]]) -> bool:
    """
    Check if player has formed a ring
    A ring is a loop around one or more cells
    """
    if len(player_stones) < 6:
        return False
    
    # Find connected components and check if any forms a loop
    visited = set()
    
    for stone in player_stones:
        if stone not in visited:
            component = get_connected_component(player_stones, stone)
            if component and has_loop(component):
                return True
            visited.update(component)
    
    return False

def has_bridge(player_stones: Set[Tuple[int, int]]) -> bool:
    """
    Check if player has formed a bridge
    A bridge connects any two of the six corner cells
    """
    corners = [(0, 0), (0, 14), (7, 0), (7, 14), (14, 0), (14, 14)]
    
    # Check if player controls at least 2 corners
    controlled_corners = [corner for corner in corners if corner in player_stones]
    if len(controlled_corners) < 2:
        return False
    
    # Check connectivity between pairs of controlled corners
    for i in range(len(controlled_corners)):
        for j in range(i + 1, len(controlled_corners)):
            if are_connected(player_stones, controlled_corners[i], controlled_corners[j]):
                return True
    
    return False

def has_fork(player_stones: Set[Tuple[int, int]]) -> bool:
    """
    Check if player has formed a fork
    A fork connects any three edges of the board
    """
    # Define the three pairs of edges (opposite edges)
    edges = [
        [(0, c) for c in range(15)],  # Top edge
        [(14, c) for c in range(15)], # Bottom edge
        [(r, 0) for r in range(15)],  # Left edge
        [(r, 14) for r in range(15)], # Right edge
        [(r, c) for r in range(8) for c in range(15-r)], # Top-left edge
        [(r, c) for r in range(8, 15) for c in range(r-7, 15)] # Bottom-right edge
    ]
    
    # Check which edges the player touches
    touched_edges = []
    for i, edge in enumerate(edges):
        for pos in edge:
            if pos in player_stones:
                touched_edges.append(i)
                break
    
    if len(touched_edges) < 3:
        return False
    
    # Check if the player connects three different edges
    # This is a simplified check - full implementation would be more complex
    return True

def are_connected(stones: Set[Tuple[int, int]], start: Tuple[int, int], end: Tuple[int, int]) -> bool:
    """Check if two positions are connected through the player's stones"""
    if start not in stones or end not in stones:
        return False
    
    visited = set()
    stack = [start]
    
    while stack:
        current = stack.pop()
        if current == end:
            return True
        
        if current in visited:
            continue
        
        visited.add(current)
        
        # Add neighbors to stack
        for neighbor in get_neighbors(current):
            if neighbor in stones and neighbor not in visited:
                stack.append(neighbor)
    
    return False

def has_loop(component: Set[Tuple[int, int]]) -> bool:
    """
    Check if a connected component contains a loop
    Uses a simplified approach based on Euler's formula for planar graphs
    """
    if len(component) < 6:
        return False
    
    # Count edges in the component
    edges = 0
    for stone in component:
        for neighbor in get_neighbors(stone):
            if neighbor in component:
                edges += 1
    
    edges //= 2  # Each edge counted twice
    
    # A connected planar graph has a cycle if edges >= vertices
    return edges >= len(component)

def get_connected_component(stones: Set[Tuple[int, int]], start: Tuple[int, int]) -> Set[Tuple[int, int]]:
    """Get all stones connected to the starting stone"""
    if start not in stones:
        return set()
    
    component = set()
    stack = [start]
    
    while stack:
        current = stack.pop()
        if current in component:
            continue
        
        component.add(current)
        
        for neighbor in get_neighbors(current):
            if neighbor in stones and neighbor not in component:
                stack.append(neighbor)
    
    return component

def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Get all valid neighbors of a position on the hexagonal grid"""
    r, c = pos
    neighbors = []
    
    # Same column
    if r > 0:
        neighbors.append((r-1, c))
    if r < 14:
        neighbors.append((r+1, c))
    
    # Left column
    if c > 0:
        if r > 0:
            neighbors.append((r-1, c-1))
        neighbors.append((r, c-1))
    
    # Right column
    if c < 14:
        if r > 0:
            neighbors.append((r-1, c+1))
        neighbors.append((r, c+1))
    
    return neighbors

def evaluate_move(move: Tuple[int, int], me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]], valid_mask) -> float:
    """Evaluate a move based on multiple factors"""
    score = 0.0
    
    # Basic positional value
    score += evaluate_position(move)
    
    # Connectivity to own stones
    score += evaluate_connectivity(move, me_set)
    
    # Threats to opponent
    score += evaluate_threats(move, opp_set)
    
    # Pattern completion
    score += evaluate_patterns(move, me_set, opp_set)
    
    # Mobility (keeping options open)
    score += evaluate_mobility(move, me_set, opp_set, valid_mask)
    
    return score

def evaluate_position(move: Tuple[int, int]) -> float:
    """Evaluate the inherent value of a position"""
    r, c = move
    score = 0.0
    
    # Prefer edges and corners
    if r == 0 or r == 14 or c == 0 or c == 14:
        score += 0.5
    elif r == 1 or r == 13 or c == 1 or c == 13:
        score += 0.2
    
    # Prefer corners
    if (r, c) in [(0, 0), (0, 14), (14, 0), (14, 14), (7, 0), (7, 14)]:
        score += 1.0
    
    return score

def evaluate_connectivity(move: Tuple[int, int], me_set: Set[Tuple[int, int]]) -> float:
    """Evaluate how well the move connects to existing stones"""
    score = 0.0
    neighbors = get_neighbors(move)
    
    connected_neighbors = sum(1 for n in neighbors if n in me_set)
    
    if connected_neighbors > 0:
        score += connected_neighbors * 0.8
    
    # Bonus for creating chains
    if connected_neighbors >= 2:
        score += 0.5
    
    return score

def evaluate_threats(move: Tuple[int, int], opp_set: Set[Tuple[int, int]]) -> float:
    """Evaluate how the move threatens the opponent"""
    score = 0.0
    neighbors = get_neighbors(move)
    
    # Block opponent's potential connections
    blocked_neighbors = sum(1 for n in neighbors if n in opp_set)
    score += blocked_neighbors * 0.3
    
    # Create potential for cutting off opponent groups
    # This is a simplified check
    if blocked_neighbors >= 2:
        score += 0.4
    
    return score

def evaluate_patterns(move: Tuple[int, int], me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]) -> float:
    """Evaluate how the move contributes to building patterns"""
    score = 0.0
    
    # Check for potential bridges, forks, or rings
    # This is a simplified pattern evaluation
    
    # Look for potential connections to edges
    r, c = move
    if r == 1 or c == 1 or r == 13 or c == 13:
        score += 0.3
    
    # Look for positions that could form forks
    if (r < 3 or r > 11) and (c < 3 or c > 11):
        score += 0.2
    
    return score

def evaluate_mobility(move: Tuple[int, int], me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]], valid_mask) -> float:
    """Evaluate how the move maintains future mobility"""
    score = 0.0
    
    # Count available future moves around this position
    neighbors = get_neighbors(move)
    valid_neighbors = sum(1 for n in neighbors if valid_mask[n[0]][n[1]] and n not in me_set and n not in opp_set)
    
    score += valid_neighbors * 0.1
    
    # Prefer moves that don't hem in future options
    if valid_neighbors >= 4:
        score += 0.2
    
    return score
