
import numpy as np
from collections import deque
from typing import List, Tuple, Set

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    # Create board representation
    board = np.zeros((11, 11), dtype=int)
    # Mark my stones as 1, opponent stones as -1, empty as 0
    for r, c in me:
        board[r, c] = 1
    for r, c in opp:
        board[r, c] = -1

    # Define the two sides the player needs to connect
    if color == 'b':  # Black connects top (row 0) to bottom (row 10)
        start_side = [(0, j) for j in range(11)]
        end_side = [(10, j) for j in range(11)]
        is_start = lambda cell: cell[0] == 0
        is_end = lambda cell: cell[0] == 10
    else:  # White connects left (col 0) to right (col 10)
        start_side = [(i, 0) for i in range(11)]
        end_side = [(i, 10) for i in range(11)]
        is_start = lambda cell: cell[1] == 0
        is_end = lambda cell: cell[1] == 10

    # Get all empty cells
    empty_cells = []
    for i in range(11):
        for j in range(11):
            if board[i, j] == 0:
                empty_cells.append((i, j))

    # Neighbor function for hex grid
    def get_neighbors(r, c):
        # Directions: 6 hexagonal neighbors
        # Top row: (r-1, c), (r-1, c+1)
        # Same row: (r, c-1), (r, c+1)
        # Bottom row: (r+1, c-1), (r+1, c)
        directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 11 and 0 <= nc < 11:
                neighbors.append((nr, nc))
        return neighbors

    # Compute shortest path length from a set of start cells to a set of end cells
    # considering only empty and friendly cells (enemy blocks)
    def shortest_path_length(start_cells: List[Tuple[int,int]], 
                           end_condition) -> float:
        visited = set()
        queue = deque()
        for cell in start_cells:
            if board[cell[0], cell[1]] == 0:  # Only passable if empty
                queue.append((cell[0], cell[1], 0))
                visited.add(cell)
            elif board[cell[0], cell[1]] == 1:  # Our stone: start from distance 0
                queue.append((cell[0], cell[1], 0))
                visited.add(cell)
        while queue:
            r, c, dist = queue.popleft()
            if end_condition((r, c)):
                return dist
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in visited and board[nr, nc] != -1:  # Can't go through opponent
                    visited.add((nr, nc))
                    # If empty, cost 1; if our stone, cost 0 (already occupied)
                    new_dist = dist + (1 if board[nr, nc] == 0 else 0)
                    queue.append((nr, nc, new_dist))
        return float('inf')  # Unreachable

    # Compute current shortest path for me and opponent (on hypothetical board state)
    def evaluate_move(cell: Tuple[int, int]):
        r, c = cell
        # Place move temporarily (we know it's empty)
        # Evaluate: 1. How much we improve our shortest path, 2. How much we block opponent
        # Our path after placing
        board[r, c] = 1
        my_shortest = shortest_path_length(start_side, is_end)
        board[r, c] = 0  # remove

        # Opponent's path remains unchanged by our move
        # But compute what opponent's shortest path is now (without blocking our own possible future moves)
        opp_start_side = end_side if color == 'b' else [(i, 0) for i in range(11)]  # reuse logic
        opp_end_condition = is_start if color == 'b' else (lambda cell: cell[1] == 10)
        opp_shortest_now = shortest_path_length([s for s in opp_start_side if board[s[0], s[1]] in [0, -1]], 
                                               opp_end_condition)

        # Simulate opponent playing this cell — would it help them?
        # But only if cell is reachable for them (i.e., adjacent to their path)
        # We care if this move blocks an imminent win
        block_value = 0
        board[r, c] = -1  # simulate opponent taking it
        opp_shortest_after = shortest_path_length([s for s in opp_start_side if board[s[0], s[1]] in [0, -1]], 
                                               opp_end_condition)
        board[r, c] = 0  # reset
        if opp_shortest_after == 0:  # They would have won
            block_value = float('inf')  # Must block immediate win
        elif opp_shortest_now <= 2 and opp_shortest_after > opp_shortest_now:
            block_value = 100 / opp_shortest_now  # High priority to block near-win

        # Offense: the lower the shortest path, the better
        # We normalize by max possible distance (about 11)
        offense_score = -my_shortest if my_shortest != float('inf') else -100
        
        # Total score: we combine offense and defense
        if block_value == float('inf'):
            score = 1000  # Block immediate win
        else:
            score = offense_score + block_value
        
        # Slight preference toward center to break symmetry
        center_score = 5 - (abs(r - 5) + abs(c - 5)) / 2
        score += center_score

        return score

    # Check if opponent has an immediate winning move — if so, block it
    for cell in empty_cells:
        r, c = cell
        board[r, c] = -1  # simulate opponent move
        opp_start_side = [(10, j) for j in range(11)] if color == 'b' else [(i, 0) for i in range(11)]
        opp_end_cond = (lambda x: x[0]==0) if color == 'b' else (lambda x: x[1]==10)
        if shortest_path_length([s for s in opp_start_side if board[s[0],s[1]] in [0,-1]], opp_end_cond) == 0:
            board[r, c] = 0  # reset
            return cell  # Block the win
        board[r, c] = 0  # reset

    # Evaluate all empty cells
    best_move = empty_cells[0]
    best_score = -float('inf')
    
    for cell in empty_cells:
        score = evaluate_move(cell)
        if score > best_score:
            best_score = score
            best_move = cell

    return best_move
