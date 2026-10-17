
import collections
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    empty_cells = []
    for r in range(11):
        for c in range(11):
            cell = (r, c)
            if cell not in me_set and cell not in opp_set:
                empty_cells.append(cell)

    def get_neighbors(cell):
        r, c = cell
        neighbors = []
        if c > 0:
            neighbors.append((r, c - 1))
        if c < 10:
            neighbors.append((r, c + 1))
        if r > 0:
            neighbors.append((r - 1, c))
            if c < 10:
                neighbors.append((r - 1, c + 1))
        if r < 10:
            neighbors.append((r + 1, c))
            if c > 0:
                neighbors.append((r + 1, c - 1))
        return neighbors

    def is_connected(stones_set, color):
        if color == 'b':
            starts = [cell for cell in stones_set if cell[0] == 0]
            if not starts:
                return False
            visited = set()
            queue = deque(starts)
            visited.update(starts)
            while queue:
                current = queue.popleft()
                if current[0] == 10:
                    return True
                for neighbor in get_neighbors(current):
                    if neighbor in stones_set and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            return False
        else:
            starts = [cell for cell in stones_set if cell[1] == 0]
            if not starts:
                return False
            visited = set()
            queue = deque(starts)
            visited.update(starts)
            while queue:
                current = queue.popleft()
                if current[1] == 10:
                    return True
                for neighbor in get_neighbors(current):
                    if neighbor in stones_set and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            return False

    # Check for immediate win
    for move in empty_cells:
        new_me_set = me_set | {move}
        if is_connected(new_me_set, color):
            return move

    # Check for opponent's immediate win and block
    for move in empty_cells:
        new_opp_set = opp_set | {move}
        opponent_color = 'b' if color == 'w' else 'w'
        if is_connected(new_opp_set, opponent_color):
            return move

    # Select best move based on heuristic
    best_score = -float('inf')
    best_moves = []
    for move in empty_cells:
        my_neighbors = 0
        opp_neighbors = 0
        for neighbor in get_neighbors(move):
            if neighbor in me_set:
                my_neighbors += 1
            elif neighbor in opp_set:
                opp_neighbors += 1
        centrality = -(abs(move[0] - 5) + abs(move[1] - 5))
        score = my_neighbors - opp_neighbors + centrality
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    # Tie-break by centrality, then by row and column to ensure deterministic choice
    best_moves.sort(key=lambda x: (-(abs(x[0] - 5) + abs(x[1] - 5)), -x[0], -x[1]))
    return best_moves[0]
