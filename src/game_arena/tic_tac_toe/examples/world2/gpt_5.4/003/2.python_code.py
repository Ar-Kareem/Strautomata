
from typing import List, Tuple

N = 4

def _lines():
    lines = []
    for r in range(N):
        lines.append([(r, c) for c in range(N)])
    for c in range(N):
        lines.append([(r, c) for r in range(N)])
    lines.append([(i, i) for i in range(N)])
    lines.append([(i, N - 1 - i) for i in range(N)])
    return lines

LINES = _lines()
CELL_TO_LINES = {(r, c): [] for r in range(N) for c in range(N)}
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(idx)

POSITION_WEIGHTS = [
    [3, 4, 4, 3],
    [4, 6, 6, 4],
    [4, 6, 6, 4],
    [3, 4, 4, 3],
]

def _empty_cells(board: List[List[int]]):
    out = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                out.append((r, c))
    return out

def _is_win(board: List[List[int]], player: int) -> bool:
    target = player * N
    for line in LINES:
        s = 0
        for r, c in line:
            s += board[r][c]
        if s == target:
            return True
    return False

def _winning_moves(board: List[List[int]], player: int):
    wins = []
    for r, c in _empty_cells(board):
        board[r][c] = player
        if _is_win(board, player):
            wins.append((r, c))
        board[r][c] = 0
    return wins

def _line_score(my_count: int, opp_count: int, empty_count: int) -> int:
    if my_count > 0 and opp_count > 0:
        return 0
    if my_count == 4:
        return 100000
    if opp_count == 4:
        return -100000
    if opp_count == 0:
        if my_count == 3 and empty_count == 1:
            return 500
        if my_count == 2 and empty_count == 2:
            return 60
        if my_count == 1 and empty_count == 3:
            return 8
        return 1 if empty_count == 4 else 0
    if my_count == 0:
        if opp_count == 3 and empty_count == 1:
            return -700
        if opp_count == 2 and empty_count == 2:
            return -80
        if opp_count == 1 and empty_count == 3:
            return -10
    return 0

def _evaluate(board: List[List[int]]) -> int:
    if _is_win(board, 1):
        return 1000000
    if _is_win(board, -1):
        return -1000000

    score = 0

    for line in LINES:
        vals = [board[r][c] for r, c in line]
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        empty_count = vals.count(0)
        score += _line_score(my_count, opp_count, empty_count)

    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                score += POSITION_WEIGHTS[r][c]
            elif board[r][c] == -1:
                score -= POSITION_WEIGHTS[r][c]

    return score

def _move_heuristic(board: List[List[int]], move: Tuple[int, int]) -> int:
    r, c = move
    score = POSITION_WEIGHTS[r][c] * 3

    for idx in CELL_TO_LINES[(r, c)]:
        line = LINES[idx]
        vals = [board[rr][cc] for rr, cc in line]
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        empty_count = vals.count(0)

        if opp_count == 0:
            if my_count == 3 and empty_count == 1:
                score += 5000
            elif my_count == 2 and empty_count == 2:
                score += 150
            elif my_count == 1 and empty_count == 3:
                score += 20
            elif my_count == 0 and empty_count == 4:
                score += 4

        if my_count == 0:
            if opp_count == 3 and empty_count == 1:
                score += 4000
            elif opp_count == 2 and empty_count == 2:
                score += 120
            elif opp_count == 1 and empty_count == 3:
                score += 12

    return score

def policy(board: List[List[int]]) -> Tuple[int, int]:
    empties = _empty_cells(board)
    if not empties:
        return (0, 0)

    # 1. Immediate win
    my_wins = _winning_moves(board, 1)
    if my_wins:
        return my_wins[0]

    # 2. Immediate block
    opp_wins = _winning_moves(board, -1)
    if opp_wins:
        # If multiple blocks exist, pick the best blocking square heuristically.
        best_block = opp_wins[0]
        best_score = -10**18
        for mv in opp_wins:
            r, c = mv
            board[r][c] = 1
            s = _evaluate(board) + _move_heuristic(board, mv)
            board[r][c] = 0
            if s > best_score:
                best_score = s
                best_block = mv
        return best_block

    # 3. Score candidate moves with shallow adversarial lookahead
    ordered = sorted(empties, key=lambda mv: _move_heuristic(board, mv), reverse=True)

    best_move = ordered[0]
    best_value = -10**18

    # Search top candidates to stay fast and robust
    candidates = ordered[:min(len(ordered), 10)]

    for mv in candidates:
        r, c = mv
        board[r][c] = 1

        if _is_win(board, 1):
            value = 1000000
            board[r][c] = 0
            if value > best_value:
                best_value = value
                best_move = mv
            continue

        opp_replies = _empty_cells(board)
        if not opp_replies:
            value = _evaluate(board)
            board[r][c] = 0
            if value > best_value:
                best_value = value
                best_move = mv
            continue

        # Opponent chooses move minimizing our evaluation
        worst_case = 10**18
        opp_ordered = sorted(opp_replies, key=lambda omv: _move_heuristic(board, omv), reverse=True)
        opp_candidates = opp_ordered[:min(len(opp_ordered), 10)]

        forced_loss = False
        for orow, ocol in opp_candidates:
            board[orow][ocol] = -1
            if _is_win(board, -1):
                reply_value = -1000000
                forced_loss = True
            else:
                # One more tactical layer: can we then win immediately?
                next_my_wins = _winning_moves(board, 1)
                if next_my_wins:
                    reply_value = 900000
                else:
                    reply_value = _evaluate(board)
            board[orow][ocol] = 0

            if reply_value < worst_case:
                worst_case = reply_value

            if forced_loss:
                break

        value = worst_case
        board[r][c] = 0

        if value > best_value:
            best_value = value
            best_move = mv

    # 4. Guaranteed legal fallback
    if 0 <= best_move[0] < N and 0 <= best_move[1] < N and board[best_move[0]][best_move[1]] == 0:
        return best_move

    for mv in empties:
        return mv

    return (0, 0)
