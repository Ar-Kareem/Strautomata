
from typing import List, Tuple
import time

# ---------- Precomputed geometry ----------

# All 5-cell windows on a 6x6 board.
WINDOWS: List[List[Tuple[int, int]]] = []

# Horizontal
for r in range(6):
    for c in range(2):
        WINDOWS.append([(r, c + i) for i in range(5)])

# Vertical
for c in range(6):
    for r in range(2):
        WINDOWS.append([(r + i, c) for i in range(5)])

# Diagonal down-right
for r in range(2):
    for c in range(2):
        WINDOWS.append([(r + i, c + i) for i in range(5)])

# Diagonal down-left
for r in range(2):
    for c in range(4, 6):
        WINDOWS.append([(r + i, c - i) for i in range(5)])

# Cell order: center-ish cells first for better move ordering.
CELL_ORDER = sorted(
    [(r, c) for r in range(6) for c in range(6)],
    key=lambda rc: (abs(rc[0] - 2.5) + abs(rc[1] - 2.5), abs(rc[0] - 2.5), abs(rc[1] - 2.5))
)

# Small center preference table.
CENTER_WEIGHT = [
    [0, 1, 1, 1, 1, 0],
    [1, 2, 3, 3, 2, 1],
    [1, 3, 4, 4, 3, 1],
    [1, 3, 4, 4, 3, 1],
    [1, 2, 3, 3, 2, 1],
    [0, 1, 1, 1, 1, 0],
]

PATTERN_SCORE = [0, 2, 12, 80, 800, 1000000]


# ---------- Board helpers ----------

def to_list_board(b):
    return [list(map(int, row)) for row in b]


def copy_board(b):
    return [row[:] for row in b]


def board_full(you, opp) -> bool:
    for r in range(6):
        yr = you[r]
        orow = opp[r]
        for c in range(6):
            if yr[c] == 0 and orow[c] == 0:
                return False
    return True


def quadrant_bounds(q: int):
    if q == 0:
        return 0, 0
    if q == 1:
        return 0, 3
    if q == 2:
        return 3, 0
    return 3, 3


def rotate_quadrant(board, q: int, d: str):
    r0, c0 = quadrant_bounds(q)
    a00 = board[r0][c0]
    a01 = board[r0][c0 + 1]
    a02 = board[r0][c0 + 2]
    a10 = board[r0 + 1][c0]
    a11 = board[r0 + 1][c0 + 1]
    a12 = board[r0 + 1][c0 + 2]
    a20 = board[r0 + 2][c0]
    a21 = board[r0 + 2][c0 + 1]
    a22 = board[r0 + 2][c0 + 2]

    if d == 'R':
        board[r0][c0] = a20
        board[r0][c0 + 1] = a10
        board[r0][c0 + 2] = a00
        board[r0 + 1][c0] = a21
        board[r0 + 1][c0 + 1] = a11
        board[r0 + 1][c0 + 2] = a01
        board[r0 + 2][c0] = a22
        board[r0 + 2][c0 + 1] = a12
        board[r0 + 2][c0 + 2] = a02
    else:  # 'L'
        board[r0][c0] = a02
        board[r0][c0 + 1] = a12
        board[r0][c0 + 2] = a22
        board[r0 + 1][c0] = a01
        board[r0 + 1][c0 + 1] = a11
        board[r0 + 1][c0 + 2] = a21
        board[r0 + 2][c0] = a00
        board[r0 + 2][c0 + 1] = a10
        board[r0 + 2][c0 + 2] = a20


def apply_move(you, opp, move):
    r, c, q, d = move
    ny = copy_board(you)
    no = copy_board(opp)
    ny[r][c] = 1
    rotate_quadrant(ny, q, d)
    rotate_quadrant(no, q, d)
    return ny, no


def has_five(board) -> bool:
    for window in WINDOWS:
        ok = True
        for r, c in window:
            if board[r][c] != 1:
                ok = False
                break
        if ok:
            return True
    return False


def terminal_score(you, opp):
    yw = has_five(you)
    ow = has_five(opp)
    if yw and not ow:
        return 10**9
    if ow and not yw:
        return -10**9
    if yw and ow:
        return 0
    if board_full(you, opp):
        return 0
    return None


# ---------- Move generation ----------

def legal_moves(you, opp):
    moves = []
    for r, c in CELL_ORDER:
        if you[r][c] == 0 and opp[r][c] == 0:
            # Include all rotations. Order quadrants and dirs consistently.
            for q in (0, 1, 2, 3):
                moves.append((r, c, q, 'R'))
                moves.append((r, c, q, 'L'))
    return moves


def move_to_str(move):
    r, c, q, d = move
    return f"{r+1},{c+1},{q},{d}"


# ---------- Evaluation ----------

def static_eval(you, opp) -> int:
    ts = terminal_score(you, opp)
    if ts is not None:
        return ts

    score = 0

    # Pattern windows.
    for window in WINDOWS:
        yc = 0
        oc = 0
        for r, c in window:
            yc += you[r][c]
            oc += opp[r][c]
        if yc and oc:
            continue
        if yc:
            score += PATTERN_SCORE[yc]
        elif oc:
            score -= int(PATTERN_SCORE[oc] * 1.15)

    # Center preference.
    for r in range(6):
        yr = you[r]
        orow = opp[r]
        cw = CENTER_WEIGHT[r]
        for c in range(6):
            if yr[c]:
                score += cw[c]
            elif orow[c]:
                score -= cw[c]

    return score


def opponent_has_immediate_win(you, opp, time_deadline=None) -> bool:
    # Opponent to move: simulate by swapping roles in apply_move.
    for move in legal_moves(opp, you):
        if time_deadline is not None and time.time() > time_deadline:
            break
        no, ny = apply_move(opp, you, move)
        yw = has_five(ny)
        ow = has_five(no)
        if ow and not yw:
            return True
    return False


def count_immediate_wins_for_player(you, opp, limit=None, time_deadline=None) -> int:
    cnt = 0
    for move in legal_moves(you, opp):
        if time_deadline is not None and time.time() > time_deadline:
            break
        ny, no = apply_move(you, opp, move)
        yw = has_five(ny)
        ow = has_five(no)
        if yw and not ow:
            cnt += 1
            if limit is not None and cnt >= limit:
                return cnt
    return cnt


# ---------- Main policy ----------

def policy(you, opponent) -> str:
    you = to_list_board(you)
    opponent = to_list_board(opponent)

    moves = legal_moves(you, opponent)
    if not moves:
        # Should not happen per prompt, but keep a legal-ish fallback impossible state.
        return "1,1,0,R"

    fallback = move_to_str(moves[0])
    start = time.time()
    deadline = start + 0.92

    # 1) Immediate winning move.
    drawing_move = None
    for move in moves:
        ny, no = apply_move(you, opponent, move)
        yw = has_five(ny)
        ow = has_five(no)
        if yw and not ow:
            return move_to_str(move)
        if yw and ow and drawing_move is None:
            drawing_move = move

    # 2) Fast static scan of all moves.
    current_opp_threat = False
    # Try to detect if opponent already has an immediate winning reply available.
    # Short budget only.
    if time.time() < deadline - 0.35:
        current_opp_threat = opponent_has_immediate_win(you, opponent, time_deadline=deadline - 0.30)

    scored = []
    safe_moves = []

    for move in moves:
        if time.time() > deadline - 0.25:
            break
        ny, no = apply_move(you, opponent, move)

        ts = terminal_score(ny, no)
        if ts is not None:
            if ts == 0:
                scored.append((ts, move, ny, no))
            else:
                scored.append((ts, move, ny, no))
            continue

        score = static_eval(ny, no)

        # Tactical safety: heavily punish moves that allow an immediate opponent win.
        if time.time() < deadline - 0.15:
            opp_can_win = opponent_has_immediate_win(ny, no, time_deadline=deadline - 0.12)
            if opp_can_win:
                score -= 5000000
            else:
                safe_moves.append((score, move, ny, no))
                # Bonus if we create multiple immediate winning threats.
                wins_next = count_immediate_wins_for_player(ny, no, limit=2, time_deadline=deadline - 0.10)
                if wins_next >= 2:
                    score += 200000
        scored.append((score, move, ny, no))

    if not scored:
        return fallback

    # If under threat, strongly prefer safe moves.
    if current_opp_threat and safe_moves:
        safe_moves.sort(key=lambda x: x[0], reverse=True)
        # Search a few safe moves deeper.
        candidates = safe_moves[:10]
    else:
        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = scored[:12]

    # 3) Shallow minimax: opponent best reply.
    best_score = -10**18
    best_move = None

    for base_score, move, ny, no in candidates:
        if time.time() > deadline:
            break

        ts = terminal_score(ny, no)
        if ts is not None:
            val = ts
        else:
            # Opponent minimizes our evaluation.
            opp_moves = legal_moves(no, ny)
            worst = 10**18

            # Quick ordering: likely strong opponent replies first.
            # Place in center first already due to legal_moves ordering.
            checked = 0
            for om in opp_moves:
                if time.time() > deadline:
                    break
                nopp, nyou = apply_move(no, ny, om)
                rep_ts = terminal_score(nyou, nopp)
                if rep_ts is not None:
                    rep_val = rep_ts
                else:
                    rep_val = static_eval(nyou, nopp)

                if rep_val < worst:
                    worst = rep_val
                    if worst <= -10**9:
                        break
                checked += 1
                # Mild cap in early game to stay within time.
                if checked >= 140 and len(opp_moves) > 180 and time.time() > deadline - 0.06:
                    break

            if worst == 10**18:
                worst = static_eval(ny, no)
            val = worst

        # Slight tie-break toward better immediate shape.
        val2 = val + base_score * 0.001
        if best_move is None or val2 > best_score:
            best_score = val2
            best_move = move

    if best_move is not None:
        return move_to_str(best_move)

    # 4) Fallbacks.
    if drawing_move is not None:
        return move_to_str(drawing_move)

    scored.sort(key=lambda x: x[0], reverse=True)
    return move_to_str(scored[0][1])
