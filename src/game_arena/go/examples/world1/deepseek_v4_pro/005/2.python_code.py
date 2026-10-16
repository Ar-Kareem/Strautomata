
import numpy as np

# Precompute positional value map (0-indexed)
pos_map = np.zeros((19, 19), dtype=np.int8)
for r in range(19):
    for c in range(19):
        d = min(r, 18 - r, c, 18 - c)
        if d == 0:
            pos_map[r, c] = 1
        elif d == 1:
            pos_map[r, c] = 3
        elif d == 2:
            pos_map[r, c] = 5
        elif d == 3:
            pos_map[r, c] = 4
        else:
            pos_map[r, c] = 2


def get_groups(board):
    """Return a list of (color, stones, liberties) for each group."""
    visited = np.zeros((19, 19), dtype=bool)
    groups = []
    for r in range(19):
        for c in range(19):
            if board[r, c] != 0 and not visited[r, c]:
                color = board[r, c]
                stones = []
                liberties = set()
                queue = [(r, c)]
                visited[r, c] = True
                while queue:
                    cr, cc = queue.pop(0)
                    stones.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 19 and 0 <= nc < 19:
                            if board[nr, nc] == 0:
                                liberties.add((nr, nc))
                            elif board[nr, nc] == color and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))
                groups.append((color, stones, liberties))
    return groups


def simulate_and_evaluate(board, move):
    """Simulate placing a stone at move, return score or None if illegal."""
    new_board = board.copy()
    new_board[move] = 1
    groups = get_groups(new_board)

    # Remove captured opponent groups
    captured = 0
    for color, stones, liberties in groups:
        if color == 2 and len(liberties) == 0:
            for s in stones:
                new_board[s] = 0
            captured += len(stones)

    if captured > 0:
        groups = get_groups(new_board)

    # Check suicide
    for color, stones, liberties in groups:
        if color == 1 and len(liberties) == 0:
            return None  # illegal move

    # Evaluate the resulting board
    score = 0
    for color, stones, liberties in groups:
        size = len(stones)
        libs = len(liberties)
        if color == 1:  # our stones
            if libs == 1:
                score -= 20 * size
            elif libs == 2:
                score -= 5 * size
            else:
                score += size * 1
        else:  # opponent stones
            if libs == 1:
                score += 15 * size
            elif libs == 2:
                score += 3 * size
            else:
                score -= size * 1

    # Bonus for captures
    score += captured * 20

    # Positional value
    score += pos_map[move] * 2

    # Ko penalty: avoid playing a move that captures exactly 1 stone
    # and leaves our new stone with 1 liberty (ko shape)
    for color, stones, liberties in groups:
        if color == 1 and len(liberties) == 1 and move in stones:
            if captured == 1:
                score -= 10
            break

    return score


def get_candidates(board):
    """Return all empty cells adjacent to any stone."""
    candidates = set()
    for r in range(19):
        for c in range(19):
            if board[r, c] != 0:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                        candidates.add((nr, nc))
    return list(candidates)


def policy(me, opponent):
    """Return the next move as (row, col) or (0, 0) to pass."""
    board = np.zeros((19, 19), dtype=np.int8)
    for r, c in me:
        board[r - 1, c - 1] = 1
    for r, c in opponent:
        board[r - 1, c - 1] = 2

    total_stones = len(me) + len(opponent)

    # Opening: empty board
    if total_stones == 0:
        return (4, 4)

    # Early opening: prefer corners, then center
    if total_stones < 6:
        corners = [(3, 3), (3, 15), (15, 3), (15, 15)]  # 0-indexed
        for cr, cc in corners:
            if board[cr, cc] == 0:
                return (cr + 1, cc + 1)
        if board[9, 9] == 0:
            return (10, 10)

    candidates = get_candidates(board)
    # Fallback: if no adjacent empty cells (shouldn't happen), consider all empty cells
    if not candidates:
        candidates = [(r, c) for r in range(19) for c in range(19) if board[r, c] == 0]

    best_score = -float('inf')
    best_move = (0, 0)

    for move in candidates:
        score = simulate_and_evaluate(board, move)
        if score is None:
            continue
        if score > best_score:
            best_score = score
            best_move = (move[0] + 1, move[1] + 1)

    return best_move
