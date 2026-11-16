
import copy

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
COLS = 7
ROWS = 7
CENTER_COLS = [3, 4, 5]
CENTER_ROWS = [3, 4, 5]

# All possible centre lines (three‑in‑a‑row)
CENTER_LINES = [
    [(3, 3), (4, 3), (5, 3)],  # row 3
    [(3, 4), (4, 4), (5, 4)],  # row 4
    [(3, 5), (4, 5), (5, 5)],  # row 5
    [(3, 3), (3, 4), (3, 5)],  # col 3
    [(4, 3), (4, 4), (4, 5)],  # col 4
    [(5, 3), (5, 4), (5, 5)],  # col 5
    [(3, 3), (4, 4), (5, 5)],  # diagonal \
    [(5, 3), (4, 4), (3, 5)],  # diagonal /
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def opponent(role: str) -> str:
    return "black" if role == "white" else "white"


def parse_state(state):
    """Convert the list‑of‑facts representation into a dict {(col,row): piece}."""
    board = {}
    for fact in state:
        if fact[0] == "cell":
            col = int(fact[1])
            row = int(fact[2])
            piece = fact[3]
            board[(col, row)] = piece
    return board


def find_drop_row(board, col):
    """Return the largest row number (lowest on the board) that is empty in the column."""
    for r in range(ROWS, 0, -1):
        if (col, r) not in board:
            return r
    return None


def is_winning(board, role):
    """Check whether `role` has three in a row in the centre."""
    for line in CENTER_LINES:
        if all(board.get(cell) and board[cell].startswith(role) for cell in line):
            return True
    return False


def evaluate_board(board, role):
    """
    Heuristic score for a board position from `role`'s perspective.
    Positive is good for `role`, negative good for the opponent.
    """
    opp = opponent(role)
    score = 0
    for line in CENTER_LINES:
        own = sum(1 for c in line if board.get(c) and board[c].startswith(role))
        their = sum(1 for c in line if board.get(c) and board[c].startswith(opp))
        score += own
        if own == 2:
            score += 5          # strong threat
        if their == 2:
            score -= 5          # block opponent's threat
        if their == 3:
            score -= 1000       # opponent would win – very bad
    return score


# ----------------------------------------------------------------------
# Move generation
# ----------------------------------------------------------------------
def generate_pawn_moves(board, c, r, role):
    """All legal pawn moves (including initial double step)."""
    moves = []
    forward = 1 if role == "white" else -1
    start_row = 1 if role == "white" else 7

    # one step forward
    nr = r + forward
    if 1 <= nr <= ROWS:
        if (c, nr) not in board:  # forward move must be empty
            moves.append({"type": "move", "role": role, "piece": "pawn",
                           "from": (c, r), "to": (c, nr)})

        # captures (diagonal forward)
        for dc in (-1, 1):
            nc = c + dc
            if 1 <= nc <= COLS and 1 <= nr <= ROWS:
                target = (nc, nr)
                if target in board and board[target].startswith(opponent(role)):
                    moves.append({"type": "move", "role": role, "piece": "pawn",
                                   "from": (c, r), "to": target})

    # double step from start rank
    if r == start_row:
        nr2 = r + 2 * forward
        if 1 <= nr2 <= ROWS:
            # both squares must be empty
            if (c, nr) not in board and (c, nr2) not in board:
                moves.append({"type": "move", "role": role, "piece": "pawn",
                               "from": (c, r), "to": (c, nr2)})
    return moves


def generate_checker_moves(board, c, r, role):
    """Checker‑king moves (any diagonal direction) and captures."""
    moves = []
    for dc, dr in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nc, nr = c + dc, r + dr
        if not (1 <= nc <= COLS and 1 <= nr <= ROWS):
            continue
        target = (nc, nr)
        if target not in board:
            # simple move
            moves.append({"type": "move", "role": role, "piece": "checker",
                           "from": (c, r), "to": target})
        else:
            # capture – must jump over opponent piece
            if board[target].startswith(opponent(role)):
                jc, jr = nc + dc, nr + dr
                if 1 <= jc <= COLS and 1 <= jr <= ROWS:
                    jump = (jc, jr)
                    if jump not in board:
                        moves.append({"type": "move", "role": role, "piece": "checker",
                                       "from": (c, r), "to": jump})
    return moves


def generate_knight_moves(board, c, r, role):
    """Knight moves (L‑shapes) with optional capture."""
    moves = []
    offsets = [(2, 1), (2, -1), (-2, 1), (-2, -1),
               (1, 2), (1, -2), (-1, 2), (-1, -2)]
    for dc, dr in offsets:
        nc, nr = c + dc, r + dr
        if not (1 <= nc <= COLS and 1 <= nr <= ROWS):
            continue
        target = (nc, nr)
        if target not in board:
            moves.append({"type": "move", "role": role, "piece": "knight",
                           "from": (c, r), "to": target})
        else:
            if board[target].startswith(opponent(role)):
                moves.append({"type": "move", "role": role, "piece": "knight",
                               "from": (c, r), "to": target})
    return moves


def generate_drop_moves(board, role):
    """Drop a disk in one of the central columns (3‑5)."""
    moves = []
    for col in CENTER_COLS:
        row = find_drop_row(board, col)
        if row is not None:
            moves.append({"type": "drop", "role": role, "col": col, "row": row})
    return moves


def generate_all_moves(board, role):
    """Collect all legal moves for `role`."""
    moves = []
    for (c, r), piece in board.items():
        if piece.startswith(role):
            ptype = piece[len(role):]  # strip colour prefix
            if ptype == "pawn":
                moves.extend(generate_pawn_moves(board, c, r, role))
            elif ptype == "checker":
                moves.extend(generate_checker_moves(board, c, r, role))
            elif ptype == "knight":
                moves.extend(generate_knight_moves(board, c, r, role))
            # disks cannot be moved
    moves.extend(generate_drop_moves(board, role))
    return moves


# ----------------------------------------------------------------------
# Apply a move to a board (pure function)
# ----------------------------------------------------------------------
def apply_move(board, move):
    nb = copy.copy(board)
    if move["type"] == "move":
        fc, fr = move["from"]
        tc, tr = move["to"]
        piece = nb[(fc, fr)]
        del nb[(fc, fr)]
        if (tc, tr) in nb:      # capture – remove opponent piece
            del nb[(tc, tr)]
        nb[(tc, tr)] = piece
    elif move["type"] == "drop":
        col = move["col"]
        row = move["row"]
        nb[(col, row)] = move["role"] + "disk"
    return nb


# ----------------------------------------------------------------------
# Turn the move description into the required string format
# ----------------------------------------------------------------------
def move_to_string(move):
    if move["type"] == "move":
        fc, fr = move["from"]
        tc, tr = move["to"]
        return f"{move['piece']}move({fc},{fr},{tc},{tr})"
    elif move["type"] == "drop":
        return f"drop({move['col']})"
    # fallback – should never happen
    return "noop"


# ----------------------------------------------------------------------
# Main policy entry point
# ----------------------------------------------------------------------
def policy(state, role):
    """
    Given the current `state` (list of facts) and the `role` to move,
    return a legal action string in Stanford syntax.
    """
    board = parse_state(state)

    # Generate all possible moves
    all_moves = generate_all_moves(board, role)

    # If no legal move, we must pass
    if not all_moves:
        return "noop"

    best_score = -float('inf')
    best_move = None

    for mv in all_moves:
        nb = apply_move(board, mv)
        # Immediate win?
        if is_winning(nb, role):
            best_move = mv
            break  # take the first winning move
        # Otherwise evaluate the position
        sc = evaluate_board(nb, role)
        if sc > best_score:
            best_score = sc
            best_move = mv

    # If somehow no best move was selected (should not happen), fall back
    if best_move is None:
        return "noop"

    return move_to_string(best_move)
