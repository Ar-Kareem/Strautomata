
import time

WIN = 10 ** 9
INF = 10 ** 12

# ----- Precomputed board geometry -----

LINES = []

# Horizontal length-5 windows
for r in range(6):
    for c in range(2):
        LINES.append(tuple(r * 6 + c + k for k in range(5)))

# Vertical length-5 windows
for c in range(6):
    for r in range(2):
        LINES.append(tuple((r + k) * 6 + c for k in range(5)))

# Diagonal down-right length-5 windows
for r in range(2):
    for c in range(2):
        LINES.append(tuple((r + k) * 6 + (c + k) for k in range(5)))

# Diagonal down-left length-5 windows
for r in range(2):
    for c in range(4, 6):
        LINES.append(tuple((r + k) * 6 + (c - k) for k in range(5)))

# Rotation specifications.
# rot index = quad * 2 + direction_bit, where 0 = L, 1 = R.
ROTATIONS = []
for q in range(4):
    br = 0 if q < 2 else 3
    bc = 0 if q % 2 == 0 else 3

    dests = []
    srcs_L = []
    srcs_R = []

    for rr in range(3):
        for cc in range(3):
            dest = (br + rr) * 6 + (bc + cc)
            dests.append(dest)

            # Left / anticlockwise: new[r][c] = old[c][2-r]
            src_l = (br + cc) * 6 + (bc + (2 - rr))
            srcs_L.append(src_l)

            # Right / clockwise: new[r][c] = old[2-c][r]
            src_r = (br + (2 - cc)) * 6 + (bc + rr)
            srcs_R.append(src_r)

    ROTATIONS.append((tuple(dests), tuple(srcs_L)))
    ROTATIONS.append((tuple(dests), tuple(srcs_R)))

CELL_WEIGHTS = (
    3, 4, 4, 4, 4, 3,
    4, 6, 6, 6, 6, 4,
    4, 6, 8, 8, 6, 4,
    4, 6, 8, 8, 6, 4,
    4, 6, 6, 6, 6, 4,
    3, 4, 4, 4, 4, 3,
)

LINE_WEIGHTS = (0, 2, 14, 90, 1400, 70000)
OPP_LINE_WEIGHTS = (0, 3, 18, 120, 1800, 70000)


# ----- Core helpers -----

def apply_move(board, pos, rot, player):
    """Return a new flat 36-cell board after placing player at pos and rotating."""
    nb = board[:]
    nb[pos] = player

    dests, srcs = ROTATIONS[rot]
    vals = [nb[i] for i in srcs]
    for i in range(9):
        nb[dests[i]] = vals[i]

    return nb


def terminal_score(board):
    """Return WIN, -WIN, 0 for draw, or None if non-terminal."""
    max_win = False
    min_win = False

    for line in LINES:
        a, b, c, d, e = line
        s = board[a] + board[b] + board[c] + board[d] + board[e]
        if s == 5:
            max_win = True
        elif s == -5:
            min_win = True

        if max_win and min_win:
            return 0

    if max_win:
        return WIN
    if min_win:
        return -WIN

    # Full board draw
    for v in board:
        if v == 0:
            return None
    return 0


def evaluate(board):
    """Static evaluation from our perspective."""
    score = 0

    for i, v in enumerate(board):
        if v:
            score += CELL_WEIGHTS[i] * v

    for line in LINES:
        a, b, c, d, e = line
        v0 = board[a]
        v1 = board[b]
        v2 = board[c]
        v3 = board[d]
        v4 = board[e]

        s = v0 + v1 + v2 + v3 + v4
        occ = (v0 != 0) + (v1 != 0) + (v2 != 0) + (v3 != 0) + (v4 != 0)

        if occ == 0:
            continue

        # Segment contains only our stones and empties.
        if s == occ:
            score += LINE_WEIGHTS[occ]
        # Segment contains only opponent stones and empties.
        elif -s == occ:
            score -= OPP_LINE_WEIGHTS[occ]

    return score


def move_to_str(pos, rot):
    r = pos // 6 + 1
    c = pos % 6 + 1
    q = rot // 2
    direction = "L" if (rot & 1) == 0 else "R"
    return f"{r},{c},{q},{direction}"


def fallback_move(board):
    for i, v in enumerate(board):
        if v == 0:
            return move_to_str(i, 0)
    return "1,1,0,L"


def opponent_reply_value(board, alpha, deadline):
    """
    Value of a position after our candidate move, assuming opponent replies
    optimally with one full legal move.
    """
    best = INF
    searched = 0

    empties = [i for i, v in enumerate(board) if v == 0]
    if not empties:
        ts = terminal_score(board)
        return 0 if ts is None else ts

    for pos in empties:
        for rot in range(8):
            child = apply_move(board, pos, rot, -1)
            ts = terminal_score(child)
            if ts is None:
                val = evaluate(child)
            else:
                val = ts

            if val < best:
                best = val

            # Alpha cutoff: this root move is already no better than a move
            # we have previously found.
            if best <= alpha:
                return best

            searched += 1
            if (searched & 31) == 0 and time.perf_counter() > deadline:
                return best if best < INF else evaluate(board)

    return best


# ----- Required API -----

def policy(you, opponent) -> str:
    """
    Return a legal Pentago move string: "row,col,quad,dir".
    We are always the player to move.
    """
    board = []
    stones = 0

    for r in range(6):
        for c in range(6):
            if int(you[r][c]):
                board.append(1)
                stones += 1
            elif int(opponent[r][c]):
                board.append(-1)
                stones += 1
            else:
                board.append(0)

    safe_fallback = fallback_move(board)

    # Simple strong opening: occupy one of the central cells while rotating
    # an empty quadrant, so the placed marble remains central.
    if stones == 0:
        return "3,3,3,L"

    deadline = time.perf_counter() + 0.92

    empties = [i for i, v in enumerate(board) if v == 0]
    if not empties:
        return safe_fallback

    candidates = []

    # Generate all legal moves. Immediately take a clean winning move.
    for pos in empties:
        for rot in range(8):
            child = apply_move(board, pos, rot, 1)
            ts = terminal_score(child)

            if ts == WIN:
                return move_to_str(pos, rot)

            static_val = ts if ts is not None else evaluate(child)
            candidates.append((static_val, pos, rot, child, ts))

    if not candidates:
        return safe_fallback

    # Good move ordering improves pruning in the opponent reply search.
    candidates.sort(reverse=True, key=lambda x: x[0])

    best_score = -INF
    best_move = safe_fallback

    for static_val, pos, rot, child, ts in candidates:
        if time.perf_counter() > deadline:
            break

        if ts is not None:
            val = ts
        else:
            val = opponent_reply_value(child, best_score, deadline)

        if val > best_score:
            best_score = val
            best_move = move_to_str(pos, rot)

    return best_move
