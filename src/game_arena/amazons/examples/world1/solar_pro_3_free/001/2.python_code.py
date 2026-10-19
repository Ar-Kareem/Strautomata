
import numpy as np
import random

# Constants
EMPTY = 0
ME = 1
OPP = 2
BLOCKED = -1

# Small board size
SIZE = 6
MAX_DEPTH = 3

# Piece → hash index
PIECE_IDX = {EMPTY: 0, ME: 1, OPP: 2, BLOCKED: 3}

# Zobrist table (random 30‑bit numbers) – same for both players
random.seed(42)
zobrist = np.random.randint(0, 2**30, size=(SIZE, SIZE, 4), dtype=np.uint64)

def compute_hash(board):
    """Return a Zobrist hash of the board (numpy array)."""
    h = 0
    b = np.asarray(board)
    for i in range(SIZE):
        for j in range(SIZE):
            p = b[i, j]
            if p != EMPTY:
                h ^= zobrist[i, j, PIECE_IDX[p]]
    return h

def parse_move(move_str):
    """Split a move string into (from, to, arrow) tuples."""
    parts = move_str.split(":")
    frm, to, ar = parts
    fr, fc = map(int, frm.split(","))
    tr, tc = map(int, to.split(","))
    ar_, ac = map(int, ar.split(","))
    return (fr, fc), (tr, tc), (ar_, ac)

def apply_move(board, move_str):
    """Return a new board after executing the given legal move."""
    frm, to, ar = parse_move(move_str)
    new_board = np.copy(board)
    new_board[frm] = EMPTY
    new_board[to] = board[frm]          # move our amazon
    new_board[ar] = BLOCKED
    return new_board

def generate_moves(board, player):
    """
    Generate all legal moves for `player` (ME or OPP) as strings.
    Duplicate resulting boards are removed to keep the search space small.
    """
    b = np.asarray(board)
    moves = []
    seen_boards = set()   # store keys as tuple of board content

    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)]

    amazon_pos = [(i, j) for i in range(SIZE) for j in range(SIZE) if b[i, j] == player]
    for (fr, fc) in amazon_pos:
        # All queen‑style landing squares
        for dx, dy in dirs:
            rr, cc = fr + dx, fc + dy
            while 0 <= rr < SIZE and 0 <= cc < SIZE and b[rr, cc] == EMPTY:
                to = (rr, cc)
                # Arrow shots from this landing square
                for ax, ay in dirs:
                    arr, acc = rr + ax, cc + ay
                    arrow_path = []
                    while 0 <= arr < SIZE and 0 <= acc < SIZE and b[arr, acc] == EMPTY:
                        arrow_path.append((arr, acc))
                        arr += ax
                        acc += ay
                    for arrow in arrow_path:
                        move = f"{fr},{fc}:{to[0]},{to[1]}:{arrow[0]},{arrow[1]}"
                        new_board = apply_move(b, move)
                        key = tuple(new_board.tolist())
                        if key not in seen_boards:
                            seen_boards.add(key)
                            moves.append(move)
                # advance to next landing square
                rr += dx
                cc += dy
    return moves

def safety_score(board):
    """Very rough count of pieces that are farther than 2 squares from any enemy queen."""
    b = np.asarray(board)
    my = [(i, j) for i in range(SIZE) for j in range(SIZE) if b[i, j] == ME]
    opp = [(i, j) for i in range(SIZE) for j in range(SIZE) if b[i, j] == OPP]
    safe = 0
    for (mr, mc) in my:
        threatened = False
        for (or_, oc) in opp:
            d = max(abs(mr - or_), abs(mc - oc))
            if d <= 2:
                threatened = True
                break
        if not threatened:
            safe += 1
    # opponent's safety is symmetric – we add the same value to the evaluation
    return safe

def evaluate(board):
    """
    Static heuristic value for a given board.
    Positive → advantage for us, negative → advantage for opponent.
    """
    b = np.asarray(board)

    my_moves = generate_moves(b, ME)
    opp_moves = generate_moves(b, OPP)
    mobility = len(my_moves) - len(opp_moves)

    amazon_diff = np.sum(b == ME) - np.sum(b == OPP)

    arrow_penalty = -0.5 * np.sum(b == BLOCKED)

    safe = safety_score(b)

    # Weighted sum – higher is better for us
    return (5 * mobility) + (3 * amazon_diff) + (2 * safe) + (arrow_penalty)

def minimax(board, depth, player_turn, alpha, beta, cache):
    """
    Recursive alpha‑beta search. Returns (score, best_move).
    `player_turn` is 1 (our amazon) or 2 (opponent).
    """
    key = (player_turn, compute_hash(board))
    if key in cache:
        # Cache entry is (score, move). If we hit the same state with the same player
        # we can reuse the previously computed best move/value.
        return cache[key]

    moves = generate_moves(board, player_turn)
    if depth == 0 or not moves:
        score = evaluate(board)
        cache[key] = (score, None)
        return score, None

    # Order moves by static evaluation of the resulting board
    move_scores = []
    for mv in moves:
        new_board = apply_move(board, mv)
        mv_score = evaluate(new_board)
        move_scores.append((mv_score, mv))

    if player_turn == ME:       # maximizing
        move_scores.sort(reverse=True)
    else:                       # minimizing
        move_scores.sort()

    best_move = None
    if player_turn == ME:
        best_score = -float('inf')
    else:
        best_score = float('inf')

    for (mv_score, mv) in move_scores:
        new_board = apply_move(board, mv)
        # Tie‑break by random order when scores are equal
        # (random.shuffle only on equal scores)
        if player_turn == ME:
            if mv_score > best_score:
                best_score = mv_score
                best_move = mv
        else:
            if mv_score < best_score:
                best_score = mv_score
                best_move = mv

        if player_turn == ME:
            alpha = max(alpha, best_score)
        else:
            beta = min(beta, best_score)

        # Alpha‑beta cut‑off
        if alpha >= beta:
            break

        score, _ = minimax(new_board, depth - 1,
                           1 if player_turn == OPP else ME,
                           alpha, beta, cache)

        if player_turn == ME:
            if score > best_score:
                best_score = score
                best_move = mv
        else:
            if score < best_score:
                best_score = score
                best_move = mv

    cache[key] = (best_score, best_move)
    return best_score, best_move

def policy(board):
    """
    Main entry point. Returns a single legal move string.
    """
    # Ensure we work with a numpy array
    b = np.asarray(board)

    # Transposition table for the whole search (shared between calls)
    trans = {}

    # Depth‑limited look‑ahead (3 ply)
    _, best_move = minimax(b, MAX_DEPTH, ME, -float('inf'), float('inf'), trans)

    # Fallback: if somehow no legal move was found (should not happen)
    if best_move is None:
        # pick a random empty square and do nothing – this is illegal but the
        # specification guarantees at least one legal move for us.
        empty = np.where(b == EMPTY)
        if empty[0].size == 0:
            return "0,0:0,0:0,0"
        frm = empty[0][0]
        fr, fc = int(frm), int(empty[1][0])
        # try to move to the nearest empty square (horizontal first)
        for fx, fy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            to = (fr, fc)
            while 0 <= to[0] < SIZE and 0 <= to[1] < SIZE and b[to] == EMPTY:
                # pick any arrow direction that stays clear
                for ax, ay in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    arr = to[0] + ax
                    acc = to[1] + ay
                    while 0 <= arr < SIZE and 0 <= acc < SIZE and b[arr, acc] == EMPTY:
                        arr += ax
                        acc += ay
                    # the last square in the arrow path is a legal arrow
                    if 0 <= arr < SIZE and 0 <= acc < SIZE:
                        arrow = (arr - ax, acc - ay)
                        return f"{fr},{fc}:{to[0]},{to[1]}:{arrow[0]},{arrow[1]}"
                # Move the amazon a step forward
                fr, fc = to
                to = (fr + fx, fc + fy)

    return best_move

