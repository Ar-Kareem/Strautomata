
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board = np.zeros((11, 11), dtype=int)
    # 1 for me, -1 for opponent, 0 for empty
    for r, c in me:
        board[r, c] = 1
    for r, c in opp:
        board[r, c] = -1

    def neighbors(r, c):
        # Returns the six adjacent hex cells
        candidates = [
            (r, c-1), (r, c+1),  # same row
            (r-1, c), (r-1, c+1),  # top row
            (r+1, c-1), (r+1, c)   # bottom row
        ]
        return [(nr, nc) for nr, nc in candidates if 0 <= nr < 11 and 0 <= nc < 11]

    def connected_to_side(stones, color):
        # Check if any stone in list touches own sides
        if color == 'b':
            return any(r == 0 for r, c in stones) and any(r == 10 for r, c in stones)
        else:
            return any(c == 0 for r, c in stones) and any(c == 10 for r, c in stones)

    def can_connect_path(stones, color, board):
        # BFS to check if current stones connect both sides
        visited = np.zeros((11, 11), dtype=bool)
        queue = deque()
        start_edges = set()

        if color == 'b':
            for r, c in stones:
                if r == 0:
                    queue.append((r, c))
                    visited[r, c] = True
            target_side = 10
            check_node = lambda r, c: r == target_side
        else:
            for r, c in stones:
                if c == 0:
                    queue.append((r, c))
                    visited[r, c] = True
            target_side = 10
            check_node = lambda r, c: c == target_side

        while queue:
            r, c = queue.popleft()
            if check_node(r, c):
                return True
            for nr, nc in neighbors(r, c):
                if board[nr, nc] == 1 and not visited[nr, nc]:
                    visited[nr, nc] = True
                    queue.append((nr, nc))
        return False

    # First, check for immediate winning move
    empty_cells = [(r, c) for r in range(11) for c in range(11) if board[r, c] == 0]
    my_stones = me[:]
    for r, c in empty_cells:
        # Simulate placing stone
        if can_connect_path(my_stones + [(r, c)], color, board):
            return (r, c)

    # Check if opponent has a winning threat and block it
    opp_board = np.copy(board)
    opp_board[opp_board == 1] = -1
    opp_board[opp_board == -1] = 1
    opp_stones_reversed = [(r, c) for r, c in opp]
    for r, c in empty_cells:
        if can_connect_path(opp_stones_reversed + [(r, c)], 'b' if color == 'w' else 'w', opp_board):
            return (r, c)

    # Score each empty cell based on strategic value
    best_score = -1
    best_move = empty_cells[0]

    # Precompute distances for influence map
    def distance_to_target(r, c, color):
        if color == 'b':
            return min(r, 10 - r)  # distance to top or bottom
        else:
            return min(c, 10 - c)  # distance to left or right

    for r, c in empty_cells:
        score = 0.0

        # Distance to target sides (lower is better, so use inverse-like)
        d = distance_to_target(r, c, color)
        score += 10.0 / (1 + d)  # closer to edge is better

        # Proximity to own stones
        near_me = 0
        near_opp = 0
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == 1:
                near_me += 1
            elif board[nr, nc] == -1:
                near_opp += 1

        score += 3.0 * near_me
        score -= 2.0 * near_opp

        # Prefer central moves if not near edges
        if color == 'b':
            centrality = 11 - abs(r - 5)
        else:
            centrality = 11 - abs(c - 5)
        score += 0.5 * centrality

        # Bonus for forming potential bridges
        for dr, dc in [(1,1), (-1,-1), (2, -1), (-2, 1)]:
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < 11 and 0 <= c2 < 11:
                if (r2, c2) in me:
                    score += 2.0  # potential bridge
                elif (r2, c2) in opp:
                    score -= 1.0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
