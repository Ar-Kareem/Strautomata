
from collections import deque
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    def is_connected(stones, player_color):
        stone_set = set(stones)
        visited = set()
        queue = deque()
        for (r, c) in stone_set:
            if (player_color == 'b' and r == 0) or (player_color == 'w' and c == 0):
                if (r, c) not in visited:
                    queue.append((r, c))
                    visited.add((r, c))
        while queue:
            r, c = queue.popleft()
            if player_color == 'b' and r == 10:
                return True
            if player_color == 'w' and c == 10:
                return True
            for dr, dc in [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in stone_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False

    me_set = set(me)
    opp_set = set(opp)
    empty_cells = [(r, c) for r in range(11) for c in range(11) if (r, c) not in me_set and (r, c) not in opp_set]

    for move in empty_cells:
        if is_connected(me + [move], color):
            return move

    opp_color = 'w' if color == 'b' else 'b'
    block_moves = []
    for move in empty_cells:
        if is_connected(opp + [move], opp_color):
            block_moves.append(move)
    if block_moves:
        return block_moves[0]

    best_score = -1
    best_moves = []
    for move in empty_cells:
        r, c = move
        adj_count = 0
        for dr, dc in [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]:
            if (r + dr, c + dc) in me_set:
                adj_count += 1
        if color == 'b':
            if adj_count > 0:
                pos_score = r
            else:
                proximity = abs(r - 5) + abs(c - 5)
                pos_score = 11 - proximity
        else:
            if adj_count > 0:
                pos_score = c
            else:
                proximity = abs(r - 5) + abs(c - 5)
                pos_score = 11 - proximity
        score = adj_count * 10 + pos_score
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    return best_moves[0]
