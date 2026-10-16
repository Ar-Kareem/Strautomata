
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)

    def get_neighbors(i, j):
        neighbors = []
        for di, dj in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
            ni = i + di
            nj = j + dj
            if 0 <= ni < 11 and 0 <= nj < 11:
                neighbors.append((ni, nj))
        return neighbors

    def is_connected(c, stones):
        if c == 'b':
            start_cells = [(i, j) for (i, j) in stones if i == 0]
            visited = set()
            queue = deque(start_cells)
            if not queue:
                return False
            while queue:
                cell = queue.popleft()
                if cell in visited:
                    continue
                i, j = cell
                if i == 10:
                    return True
                visited.add(cell)
                for neighbor in get_neighbors(i, j):
                    if neighbor in stones:
                        queue.append(neighbor)
            return False
        else:
            start_cells = [(i, j) for (i, j) in stones if j == 0]
            visited = set()
            queue = deque(start_cells)
            if not queue:
                return False
            while queue:
                cell = queue.popleft()
                if cell in visited:
                    continue
                i, j = cell
                if j == 10:
                    return True
                visited.add(cell)
                for neighbor in get_neighbors(i, j):
                    if neighbor in stones:
                        queue.append(neighbor)
            return False

    all_cells = [(i, j) for i in range(11) for j in range(11)]
    empty = [cell for cell in all_cells if cell not in me_set and cell not in opp_set]

    # Step 1: Immediate win
    for move in empty:
        if is_connected(color, me_set | {move}):
            return move

    # Step 2: Block opponent's immediate win
    opponent_color = 'w' if color == 'b' else 'b'
    for move in empty:
        if is_connected(opponent_color, opp_set | {move}):
            return move

    # Step 3: Heuristic - adjacency + position
    def calculate_score(move):
        i, j = move
        neighbors = get_neighbors(i, j)
        adjacency_score = sum(1 for n in neighbors if n in me_set)
        if color == 'b':
            position_score = i
        else:
            position_score = j
        return adjacency_score + position_score

    best_score = -1
    best_moves = []
    for move in empty:
        score = calculate_score(move)
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    return best_moves[0]
