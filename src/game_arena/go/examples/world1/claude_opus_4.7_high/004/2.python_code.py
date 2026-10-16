
import random

def neighbors(r, c):
    result = []
    if r > 1: result.append((r-1, c))
    if r < 19: result.append((r+1, c))
    if c > 1: result.append((r, c-1))
    if c < 19: result.append((r, c+1))
    return result

def get_group(board, r, c):
    color = board[(r, c)]
    stones = set()
    liberties = set()
    stack = [(r, c)]
    while stack:
        pos = stack.pop()
        if pos in stones:
            continue
        stones.add(pos)
        for n in neighbors(*pos):
            if n not in board:
                liberties.add(n)
            elif board[n] == color and n not in stones:
                stack.append(n)
    return stones, liberties

def make_board(me, opponent):
    board = {}
    for s in me:
        board[tuple(s)] = 'M'
    for s in opponent:
        board[tuple(s)] = 'O'
    return board

def is_legal(board, r, c, color):
    if (r, c) in board:
        return False
    board[(r, c)] = color
    opp = 'O' if color == 'M' else 'M'
    captured = False
    for n in neighbors(r, c):
        if n in board and board[n] == opp:
            _, libs = get_group(board, *n)
            if not libs:
                captured = True
                break
    if captured:
        del board[(r, c)]
        return True
    _, libs = get_group(board, r, c)
    del board[(r, c)]
    return len(libs) > 0

def count_captures(board, r, c, color):
    board[(r, c)] = color
    opp = 'O' if color == 'M' else 'M'
    captured = set()
    seen_groups = []
    for n in neighbors(r, c):
        if n in board and board[n] == opp and n not in captured:
            stones, libs = get_group(board, *n)
            if not libs:
                captured |= stones
    del board[(r, c)]
    return len(captured)

def is_eye(board, r, c, color):
    for n in neighbors(r, c):
        if n not in board or board[n] != color:
            return False
    own_diag = 0
    total_diag = 0
    edge_diag = 0
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if not (1 <= nr <= 19 and 1 <= nc <= 19):
            edge_diag += 1
        else:
            total_diag += 1
            if (nr, nc) in board and board[(nr, nc)] == color:
                own_diag += 1
    if edge_diag > 0:
        return own_diag == total_diag
    return own_diag >= 3

def policy(me, opponent):
    board = make_board(me, opponent)
    total = len(me) + len(opponent)

    if total < 4:
        preferred = [(4, 4), (16, 16), (4, 16), (16, 4), (10, 10),
                     (4, 10), (16, 10), (10, 4), (10, 16)]
        for p in preferred:
            if p not in board:
                return p

    candidates = set()
    for pos in list(board.keys()):
        r, c = pos
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in board:
                    candidates.add((nr, nc))

    if not candidates:
        if (10, 10) not in board:
            return (10, 10)
        return (0, 0)

    # Precompute groups
    my_groups = []
    opp_groups = []
    seen = set()
    for pos in list(board.keys()):
        if pos in seen:
            continue
        stones, libs = get_group(board, *pos)
        seen |= stones
        if board[pos] == 'M':
            my_groups.append((stones, libs))
        else:
            opp_groups.append((stones, libs))

    best_score = -1e18
    best_move = None

    for move in candidates:
        r, c = move
        if not is_legal(board, r, c, 'M'):
            continue
        if is_eye(board, r, c, 'M'):
            continue

        score = 0.0

        caps = count_captures(board, r, c, 'M')
        score += caps * 120

        # Save own group in atari
        for stones, libs in my_groups:
            if move in libs and len(libs) == 1:
                board[move] = 'M'
                _, new_libs = get_group(board, r, c)
                del board[move]
                if len(new_libs) >= 2:
                    score += 80 + 15 * len(stones)
                elif len(new_libs) == 1:
                    # still in atari unless captures
                    if caps == 0:
                        score -= 10

        # Attack opponent groups
        for stones, libs in opp_groups:
            if move in libs:
                if len(libs) == 1:
                    score += 100 + 20 * len(stones)
                elif len(libs) == 2:
                    score += 25 + 8 * len(stones)
                elif len(libs) == 3:
                    score += 8 + 3 * len(stones)
                else:
                    score += 2

        # Connection/neighbor bonuses
        own_neighbors = 0
        opp_neighbors = 0
        for n in neighbors(r, c):
            if n in board:
                if board[n] == 'M':
                    own_neighbors += 1
                else:
                    opp_neighbors += 1

        # Check resulting own liberties
        board[(r, c)] = 'M'
        _, my_libs_after = get_group(board, r, c)
        del board[(r, c)]
        liberty_count = len(my_libs_after)
        if liberty_count == 1:
            score -= 40  # self-atari penalty
        elif liberty_count == 2:
            score += 2
        else:
            score += min(liberty_count, 6) * 2

        # Edge penalties
        edge_dist = min(r - 1, 19 - r, c - 1, 19 - c)
        if edge_dist == 0:
            score -= 25
        elif edge_dist == 1:
            score -= 6
        elif edge_dist == 2:
            score += 3
        elif edge_dist == 3:
            score += 4
        else:
            score += 2

        # Encourage approaches to opponent stones
        close_opp = 0
        for os in opponent:
            d = abs(os[0] - r) + abs(os[1] - c)
            if d <= 2:
                close_opp += 1
            elif d <= 4:
                close_opp += 0.3
        score += close_opp * 1.5

        # Moderate connection bonus
        if own_neighbors == 1:
            score += 1
        if opp_neighbors >= 1 and own_neighbors == 0:
            score += 2  # contact/attack

        score += random.random() * 0.5

        if score > best_score:
            best_score = score
            best_move = move

    if best_move is None:
        # Fallback: any legal non-eye move
        for r in range(1, 20):
            for c in range(1, 20):
                if (r, c) not in board and is_legal(board, r, c, 'M') and not is_eye(board, r, c, 'M'):
                    return (r, c)
        return (0, 0)

    return best_move
