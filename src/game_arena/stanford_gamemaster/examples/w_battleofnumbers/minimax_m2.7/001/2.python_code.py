
import sys
import copy
sys.setrecursionlimit(10000)

def opponent_of(role):
    """Return the opposite colour."""
    return "green" if role == "red" else "red"

def can_capture(v_self, v_opp):
    """
    Determine whether a piece with value v_self can capture a piece with value v_opp.
    The rule: a piece can capture any smaller or equal value,
    except that 5 cannot capture 1 while 1 can capture 5.
    """
    if v_self == 5 and v_opp == 1:
        return False
    if v_self >= v_opp:
        return True
    if v_self == 1 and v_opp == 5:
        return True
    return False

def parse_state(state):
    """Convert the list of facts into a dictionary keyed by (row, col)."""
    board = {}
    for fact in state:
        if fact[0] == "cell":
            row = int(fact[1])
            col = int(fact[2])
            value = int(fact[3])
            role = fact[4]
            board[(row, col)] = {"value": value, "role": role}
    return board

# Forward directions for each role (orthogonal + diagonal forward)
FORWARD_DELTAS = {
    "red":   [(0, 1), (-1, 1), (1, 1)],   # col +1, row -1/0/+1
    "green": [(0, -1), (-1, -1), (1, -1)] # col -1, row -1/0/+1
}

def generate_moves(board, role):
    """
    Produce a list of legal moves for `role`.
    Each move is a tuple:
        ('move', r1, c1, r2, c2)   – ordinary forward step
        ('capture', r1, c1, r2, c2) – diagonal capture
    """
    moves = []
    forward = FORWARD_DELTAS[role]

    for (r, c), piece in board.items():
        if piece["role"] != role:
            continue
        v = piece["value"]

        # --- forward empty steps and forward diagonal captures -----------------
        for dr, dc in forward:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 5 and 1 <= nc <= 5:
                target = board.get((nr, nc))
                if target is None:
                    moves.append(("move", r, c, nr, nc))
                elif target["role"] != role and abs(dr) == 1 and abs(dc) == 1:
                    # diagonal capture (forward direction)
                    if can_capture(v, target["value"]):
                        moves.append(("capture", r, c, nr, nc))

        # --- all diagonal captures (including backward) -----------------------
        for dr in (-1, 1):
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 5 and 1 <= nc <= 5:
                    target = board.get((nr, nc))
                    if target and target["role"] != role:
                        if can_capture(v, target["value"]):
                            moves.append(("capture", r, c, nr, nc))

    # Remove duplicates (a forward diagonal capture may appear twice)
    unique = set(moves)
    # Order: captures first, then ordinary moves
    ordered = [m for m in unique if m[0] == "capture"]
    ordered += [m for m in unique if m[0] == "move"]
    return ordered

def apply_move(board, move, role):
    """
    Return a new board after applying `move` (a tuple as described above).
    The move is guaranteed to be legal.
    """
    new_board = {pos: p.copy() for pos, p in board.items()}
    start = (move[1], move[2])
    piece = new_board.pop(start)          # remove from original square
    end = (move[3], move[4])
    new_board[end] = piece                # place on destination
    return new_board

def evaluate(board, role):
    """
    Heuristic evaluation for `role`.
    Positive values favour `role`.
    """
    my_sum = opp_sum = 0
    my_adv = opp_adv = 0

    for (r, c), p in board.items():
        if p["role"] == role:
            my_sum += p["value"]
            if role == "red":
                my_adv += (c - 1)       # distance from left edge
            else:
                my_adv += (5 - c)       # distance from right edge
        else:
            opp_sum += p["value"]
            if role == "red":
                opp_adv += (5 - c)
            else:
                opp_adv += (c - 1)

    # Terminal situations
    if opp_sum == 0:
        return 10000 + my_sum
    if my_sum == 0:
        return -10000 - opp_sum

    # Material balance + a small bonus for advancement
    return (my_sum - opp_sum) + 0.05 * (my_adv - opp_adv)

def minmax(board, depth, alpha, beta, maximizing, role):
    """Alpha‑beta minimax search."""
    if depth == 0:
        return evaluate(board, role)

    moves = generate_moves(board, role)
    if not moves:                     # no legal moves – treat as terminal
        return evaluate(board, role)

    opp = opponent_of(role)

    if maximizing:
        value = -float('inf')
        for m in moves:
            nb = apply_move(board, m, role)
            value = max(value, minmax(nb, depth - 1, alpha, beta, False, opp))
            if value > alpha:
                alpha = value
            if beta <= alpha:
                break
        return value
    else:
        value = float('inf')
        for m in moves:
            nb = apply_move(board, m, role)
            value = min(value, minmax(nb, depth - 1, alpha, beta, True, opp))
            if value < beta:
                beta = value
            if beta <= alpha:
                break
        return value

def policy(state, role):
    """
    Main entry point.  Returns a legal move in Stanford syntax, e.g. 'move(1,1,1,2)'.
    """
    board = parse_state(state)
    moves = generate_moves(board, role)

    # Defensive fallback – should never happen in a real game state
    if not moves:
        return "move(1,1,1,2)"

    depth = 3                         # 3‑ply search gives a good balance speed/strength
    best_move = None
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    opp = opponent_of(role)

    for m in moves:
        nb = apply_move(board, m, role)
        val = minmax(nb, depth - 1, alpha, beta, False, opp)
        if val > best_value:
            best_value = val
            best_move = m
        # Keep alpha for possible move ordering (optional)
        if val > alpha:
            alpha = val

    # best_move is a tuple (type, r1, c1, r2, c2); ignore the type
    return f"move({best_move[1]},{best_move[2]},{best_move[3]},{best_move[4]})"
