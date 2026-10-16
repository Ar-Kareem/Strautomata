
import numpy as np
import random
import time
from collections import defaultdict

# Precompute neighbors for all cells once
NEIGHBORS = {}
for i in range(11):
    for j in range(11):
        # All 8 neighbors except (i-1, j-1) and (i+1, j+1)
        n = []
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                if (di == -1 and dj == -1) or (di == 1 and dj == 1):
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < 11 and 0 <= nj < 11:
                    n.append((ni, nj))
        NEIGHBORS[(i, j)] = n

def get_empty_cells(me, opp):
    occupied = set(me) | set(opp)
    return [(i, j) for i in range(11) for j in range(11) if (i, j) not in occupied]

def get_adjacent_empty(me, opp, empty_set):
    """Get empty cells adjacent to any stone, plus some random empty cells for exploration."""
    occupied = set(me) | set(opp)
    adjacent = set()
    for stone in occupied:
        for n in NEIGHBORS[stone]:
            if n in empty_set:
                adjacent.add(n)
    return list(adjacent) if adjacent else list(empty_set)

def check_win(board, player_stones, color):
    """Check if player has won using union-find."""
    if not player_stones:
        return False
    
    parent = {stone: stone for stone in player_stones}
    
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # Union all adjacent stones
    stone_set = set(player_stones)
    for stone in player_stones:
        for n in NEIGHBORS[stone]:
            if n in stone_set:
                union(stone, n)
    
    # Check connectivity based on color
    groups = defaultdict(set)
    for stone in player_stones:
        groups[find(stone)].add(stone)
    
    if color == 'b':
        # Connect top (row 0) to bottom (row 10)
        for group in groups.values():
            has_top = any(r == 0 for r, c in group)
            has_bottom = any(r == 10 for r, c in group)
            if has_top and has_bottom:
                return True
    else:
        # Connect left (col 0) to right (col 10)
        for group in groups.values():
            has_left = any(c == 0 for r, c in group)
            has_right = any(c == 10 for r, c in group)
            if has_left and has_right:
                return True
    return False

def simulate_random_game(me, opp, color, empty_cells, move_to_try=None):
    """Simulate a random game from current position, optionally with a first move."""
    my_stones = set(me)
    opp_stones = set(opp)
    empty = set(empty_cells)
    current_color = color
    
    if move_to_try is not None:
        if current_color == color:
            my_stones.add(move_to_try)
        else:
            opp_stones.add(move_to_try)
        empty.discard(move_to_try)
        current_color = 'w' if current_color == 'b' else 'b'
    
    # Quick win check after initial move
    if move_to_try is not None:
        if check_win(None, my_stones if current_color != color else my_stones, color):
            return 1.0  # I win
        if check_win(None, opp_stones if current_color != color else opp_stones, 'w' if color == 'b' else 'b'):
            return 0.0  # Opponent wins
    
    # Play random moves until board is full
    empty_list = list(empty)
    random.shuffle(empty_list)
    
    # Interleave adjacency-biased moves for more realistic playouts
    for _ in range(min(len(empty_list), 60)):  # Cap simulation depth for speed
        if not empty_list:
            break
        
        # Pick move with 70% chance from adjacency-biased, 30% fully random
        if random.random() < 0.7:
            adj_empty = get_adjacent_empty(my_stones | opp_stones, empty, set(empty_list))
            if adj_empty:
                move = random.choice(adj_empty)
                empty_list.remove(move)
            else:
                move = empty_list.pop()
        else:
            move = empty_list.pop()
        
        if current_color == color:
            my_stones.add(move)
        else:
            opp_stones.add(move)
        
        # Check win after each move
        if current_color == color and check_win(None, my_stones, color):
            return 1.0
        if current_color != color and check_win(None, opp_stones, 'w' if color == 'b' else 'b'):
            return 0.0
        
        current_color = 'w' if current_color == 'b' else 'b'
    
    # If game not finished, estimate based on territory
    return 0.5

def find_bridge_moves(me, empty_set):
    """Find bridge patterns: two empty cells that mutually support each other."""
    bridges = []
    for (i, j) in empty_set:
        # Check for bridge pattern: (i,j+1) and (i+1,j) both empty, with (i,j) forming the bridge
        # Or similar patterns
        for di, dj in [(0, 1), (1, 0), (-1, 1), (1, -1), (0, -1), (-1, 0)]:
            n1 = (i + di, j + dj)
            if n1 in empty_set:
                bridges.append((i, j))
                break
    return bridges

def mcts_policy(me, opp, color, time_limit=0.95):
    """Monte Carlo Tree Search for Hex."""
    start_time = time.time()
    
    empty_cells = get_empty_cells(me, opp)
    if not empty_cells:
        return (0, 0)  # Shouldn't happen
    
    # If only one move available, return it
    if len(empty_cells) == 1:
        return empty_cells[0]
    
    empty_set = set(empty_cells)
    
    # Get candidate moves: prioritize adjacent cells and bridges
    candidates = get_adjacent_empty(me, opp, empty_set)
    if len(candidates) > 30:
        candidates = random.sample(candidates, 30)
    
    bridges = find_bridge_moves(me, empty_set)
    bridge_set = set(bridges)
    
    # Add some bridges
    for b in bridges:
        if b not in candidates and b in empty_set:
            candidates.append(b)
    
    # Add some random moves for exploration
    other_empty = [c for c in empty_cells if c not in candidates]
    if other_empty:
        candidates.extend(random.sample(other_empty, min(10, len(other_empty))))
    
    # Ensure candidates are unique and valid
    candidates = list(set(candidates) & empty_set)
    if not candidates:
        candidates = empty_cells[:30]
    
    # MCTS statistics
    visits = defaultdict(int)
    wins = defaultdict(float)
    
    num_simulations = 0
    
    # Run simulations
    while time.time() - start_time < time_limit:
        num_simulations += 1
        
        # For efficiency, interleave different candidate moves
        if num_simulations % 3 == 0:
            # Simulate without any initial move for baseline
            result = simulate_random_game(me, opp, color, empty_cells, None)
            continue
        
        # Pick a candidate using UCB1-like heuristic
        total_visits = sum(visits.values()) + 1
        best_score = -1
        best_candidate = random.choice(candidates)
        
        for c in candidates:
            if visits[c] == 0:
                score = float('inf')  # Explore unvisited nodes
            else:
                exploitation = wins[c] / visits[c]
                exploration = np.sqrt(2 * np.log(total_visits) / visits[c])
                score = exploitation + exploration
            
            if score > best_score:
                best_score = score
                best_candidate = c
        
        # Simulate game with this move
        result = simulate_random_game(me, opp, color, empty_cells, best_candidate)
        visits[best_candidate] += 1
        wins[best_candidate] += result
    
    # Choose move with highest win rate among visited candidates
    if visits:
        best_move = max(candidates, key=lambda c: wins.get(c, 0) / max(visits.get(c, 1), 1))
        if visits.get(best_move, 0) > 0:
            return best_move
    
    # Fallback: pick any adjacent move, or center if no adjacent moves
    adj = get_adjacent_empty(me, opp, empty_set)
    if adj:
        return random.choice(adj)
    
    # Center-biased fallback
    center_moves = sorted(empty_cells, key=lambda c: abs(c[0] - 5) + abs(c[1] - 5))
    return center_moves[0]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """Main policy function called by the arena."""
    return mcts_policy(me, opp, color)
