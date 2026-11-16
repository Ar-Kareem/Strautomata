
import numpy as np
from collections import defaultdict
from typing import List, Tuple, Dict

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # Initialize board representation (19x19)
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1  # My stones (1)
    for r, c in opponent:
        board[r-1, c-1] = 2  # Opponent stones (2)

    # If no memory exists, initialize it
    if not memory:
        memory = {
            'my_groups': defaultdict(list),  # (row, col) -> list of liberties
            'opponent_groups': defaultdict(list),
            'last_move': None,
            'phase': 'opening',  # 'opening', 'middle', 'end'
            'potential_expansions': set(),
            'influence_map': np.zeros((19, 19), dtype=int)  # Tracks influence strength
        }
        # Precompute influence map (simplified)
        for r in range(19):
            for c in range(19):
                distance = min(r, c, 18 - r, 18 - c)  # Distance to nearest edge
                memory['influence_map'][r, c] = distance * 2 + 1  # Center has highest influence

    # --- PHASE DETECTION ---
    # Simple phase detection: if > 50 stones, assume middle/endgame
    if len(me) + len(opponent) > 50:
        memory['phase'] = 'endgame' if len(me) + len(opponent) > 100 else 'middle'
    else:
        memory['phase'] = 'opening'

    # --- GROUP ANALYSIS ---
    # Find connected groups (simplified BFS)
    def find_groups(stones: List[Tuple[int, int]], color: int) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
        groups = defaultdict(list)
        visited = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for r, c in stones:
            if (r, c) in visited:
                continue
            queue = [(r, c)]
            visited.add((r, c))
            group = []
            while queue:
                x, y = queue.pop(0)
                group.append((x, y))
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 19 and 0 <= ny < 19 and board[nx, ny] == color and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
            groups[(r, c)] = group
        return groups

    my_groups = find_groups(me, 1)
    opponent_groups = find_groups(opponent, 2)

    # Update liberties for each group
    def compute_liberties(groups: Dict[Tuple[int, int], List[Tuple[int, int]]]) -> Dict[Tuple[int, int], int]:
        liberties = defaultdict(int)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for group in groups.values():
            for r, c in group:
                for dx, dy in directions:
                    nr, nc = r + dx, c + dy
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                        liberties[(r, c)] += 1
                        break
        return liberties

    my_liberties = compute_liberties(my_groups)
    opponent_liberties = compute_liberties(opponent_groups)

    # --- MOVE SELECTION ---
    # 1. Check for immediate captures (opponent groups with 0 liberties)
    for group, stones in opponent_groups.items():
        if opponent_liberties[group] == 0:
            # Find the first liberty of the opponent group
            for r, c in stones:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                        return ((nr + 1, nc + 1), memory)  # Capture move

    # 2. Check for my groups with 0 liberties (suicide prevention)
    for group, stones in my_groups.items():
        if my_liberties[group] == 0:
            # Find the first liberty of my group
            for r, c in stones:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                        return ((nr + 1, nc + 1), memory)  # Rescue move

    # 3. Influence-based move (highest influence_map value)
    empty_cells = [(r, c) for r in range(19) for c in range(19) if board[r, c] == 0]
    if empty_cells:
        # Sort by influence_map (descending) and distance to opponent stones (ascending)
        empty_cells.sort(key=lambda x: (-memory['influence_map'][x[0], x[1]],
                                    sum(1 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                                        for nr, nc in [(x[0] + dr, x[1] + dc)]
                                        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 2)))
        best_move = empty_cells[0]
        return ((best_move[0] + 1, best_move[1] + 1), memory)

    # 4. Pass if no moves left
    return ((0, 0), memory)
