
import numpy as np
from typing import List, Tuple, Set
from collections import deque

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    N = 15
    board = np.zeros((N, N), dtype=int)
    for r, c in me:
        board[r, c] = 1
    for r, c in opp:
        board[r, c] = 2

    valid_moves = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c]]

    # Precompute corner and edge cells
    corners = [(0,0), (0,7), (7,0), (7,14), (14,7), (14,14)]
    edges = set()
    for i in range(N):
        edges.add((0, i))        # top edge
        edges.add((14, i))       # bottom edge
        edges.add((i, 0))        # left edge
        edges.add((i, 14))       # right edge
        if i >= 7:
            edges.add((i, i-7))  # bottom-left to top-right diagonal
        if i <= 7:
            edges.add((7-i, 7+i)) # top-left to bottom-right diagonal
    edges -= set(corners)  # corners not part of edges

    # Direction vectors for hex grid: offsets for 6 neighbors
    directions = [(-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0)]

    def in_bounds(r, c):
        return 0 <= r < N and 0 <= c < N

    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def is_connected_component(stones, target_stones, goal_type):
        # Returns True if stones form the required goal
        if len(stones) < 3:
            return False
        visited = set()
        components = []
        stone_set = set(stones)

        for stone in stone_set:
            if stone not in visited:
                comp = set()
                queue = deque([stone])
                visited.add(stone)
                comp.add(stone)
                while queue:
                    r, c = queue.popleft()
                    for nr, nc in get_neighbors(r, c):
                        if (nr, nc) in stone_set and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                            comp.add((nr, nc))
                components.append(comp)

        for comp in components:
            if goal_type == "ring":
                # Check if component forms a ring (loop around empty space)
                comp_cells = np.zeros((N, N), dtype=bool)
                for r, c in comp:
                    comp_cells[r, c] = True
                # Find enclosed empty spaces via flood fill from outside
                exterior = np.zeros((N, N), dtype=bool)
                q = deque()
                q.append((0,0))
                exterior[0,0] = True
                while q:
                    r, c = q.popleft()
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if in_bounds(nr, nc) and not exterior[nr][nc] and not board[nr][nr]:
                            exterior[nr][nc] = True
                            q.append((nr, nc))
                # If any empty cell is not exterior and surrounded, it's enclosed
                for r in range(N):
                    for c in range(N):
                        if not board[r][c] and not exterior[r][c]:
                            return True  # encloses at least one cell
            elif goal_type == "bridge":
                comp_corners = [pos for pos in comp if pos in corners]
                if len(comp_corners) >= 2:
                    # Check if all in comp are connected and cover >=2 corners
                    return True
            elif goal_type == "fork":
                edge_count = len([pos for pos in comp if pos in edges])
                corner_count = len([pos for pos in comp if pos in corners])
                # Connects three edges (not via corners)
                comp_edges = set(pos for pos in comp if pos in edges)
                # Use BFS to check connectivity to at least three distinct edge types
                top = any(r == 0 and (r,c) in comp_edges for r,c in comp_edges)
                bottom = any(r == 14 and (r,c) in comp_edges for r,c in comp_edges)
                left = any(c == 0 and (r,c) in comp_edges for r,c in comp_edges)
                right = any(c == 14 and (r,c) in comp_edges for r,c in comp_edges)
                diag1 = any((r == c+7) and (r,c) in comp_edges for r,c in comp_edges)
                diag2 = any((c == r+7) and (r,c) in comp_edges for r,c in comp_edges)
                edge_types = sum([top, bottom, left, right, diag1, diag2])
                if edge_types >= 3:
                    return True
        return False

    def would_complete_structure(move, player_stones, goal_type):
        extended_stones = player_stones + [move]
        return is_connected_component(extended_stones, extended_stones, goal_type)

    def evaluate_move(move):
        score = 0.0
        r, c = move

        # Centrality: prefer center
        dr = abs(r - 7)
        dc = abs(c - 7)
        center_score = 14 - (dr + dc)
        score += center_score * 0.1

        # Edge proximity bonus
        if r == 0 or r == 14 or c == 0 or c == 14 or r == c+7 or c == r+7:
            score += 1.0
        if move in corners:
            score += 0.5

        # Connectivity to own stones
        own_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me:
                own_neighbors += 1
        score += own_neighbors * 2.0

        # Prevent over-concentration
        if own_neighbors >= 3:
            score += 2.0  # strong group building
        elif own_neighbors == 0:
            score -= 1.5  # isolated move penalty

        # Structure potential
        for goal in ["ring", "bridge", "fork"]:
            if would_complete_structure(move, me, goal):
                score += 1000.0  # winning move
            # Check if move helps toward structure
            extended = me + [move]
            if is_connected_component(extended, extended, goal):
                score += 20.0

        # Defensive: block opponent's win
        for goal in ["ring", "bridge", "fork"]:
            if would_complete_structure(move, opp, goal):
                score += 500.0  # block opponent win

        return score

    # First, check for immediate win
    for move in valid_moves:
        for goal in ["ring", "bridge", "fork"]:
            if would_complete_structure(move, me, goal):
                return move

    # Then, check for blocking opponent win
    blocking_moves = []
    for move in valid_moves:
        for goal in ["ring", "bridge", "fork"]:
            if would_complete_structure(move, opp, goal):
                blocking_moves.append(move)
    if blocking_moves:
        # Choose best among blocking moves
        best_block = max(blocking_moves, key=evaluate_move)
        return best_block

    # Otherwise, pick best scoring move
    best_move = max(valid_moves, key=evaluate_move)
    return best_move
