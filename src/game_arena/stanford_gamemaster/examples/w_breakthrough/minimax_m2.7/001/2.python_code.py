
import sys

# ----------------------------------------------------------------------
# Constants
BOARD_SIZE = 8
ROLE_OPPONENT = {"white": "black", "black": "white"}

# ----------------------------------------------------------------------
# Board parsing ---------------------------------------------------------
def parse_board(state):
    """Convert the list of Stanford propositions into a dict
       {(col,row): 'white' or 'black'}."""
    board = {}
    for prop in state:
        if prop[0] == "cell":
            col = int(prop[1])
            row = int(prop[2])
            colour = prop[3]
            board[(col, row)] = colour
    return board

# ----------------------------------------------------------------------
# Move generation -------------------------------------------------------
def generate_moves(board, player):
    """Return a list of tuples (x1,y1,x2,y2) for all legal moves of `player`."""
    opponent = ROLE_OPPONENT[player]
    forward = 1 if player == "white" else -1
    moves = []
    for (x, y), colour in board.items():
        if colour != player:
            continue
        # straight forward
        nx, ny = x, y + forward
        if 1 <= nx <= BOARD_SIZE and 1 <= ny <= BOARD_SIZE and (nx, ny) not in board:
            moves.append((x, y, nx, ny))
        # diagonal captures
        for dx in (-1, 1):
            nx, ny = x + dx, y + forward
            if 1 <= nx <= BOARD_SIZE and 1 <= ny <= BOARD_SIZE:
                if board.get((nx, ny)) == opponent:
                    moves.append((x, y, nx, ny))
    return moves

# ----------------------------------------------------------------------
# Apply a move ----------------------------------------------------------
def apply_move(board, move):
    """Return a new board after performing `move`."""
    x1, y1, x2, y2 = move
    new_board = dict(board)
    piece = new_board.pop((x1, y1))
    new_board.pop((x2, y2), None)   # capture – harmless if empty
    new_board[(x2, y2)] = piece
    return new_board

# ----------------------------------------------------------------------
# Move ordering (heuristic) --------------------------------------------
def order_moves(board, moves, player):
    """Return moves sorted by a simple heuristic (captures first)."""
    opponent = ROLE_OPPONENT[player]
    scored = []
    for move in moves:
        _, _, x2, y2 = move
        score = 0
        # capture?
        if board.get((x2, y2)) == opponent:
            # value the captured pawn (its progress)
            prog = (y2 - 1) if opponent == "white" else (BOARD_SIZE - y2)
            score += prog * 10 + 5 + 100
        # forward (non‑capture) advance
        if x2 == move[0]:          # straight forward, no capture
            score += 5
        # promotion
        if (player == "white" and y2 == BOARD_SIZE) or (player == "black" and y2 == 1):
            score += 1000
        scored.append((score, move))
    scored.sort(reverse=True)
    return [m for _, m in scored]

# ----------------------------------------------------------------------
# Evaluation ------------------------------------------------------------
def evaluate(board, player):
    """Numeric score from `player`'s perspective."""
    opponent = ROLE_OPPONENT[player]

    # terminal – win / loss
    if player == "white":
        if any(y == BOARD_SIZE for (x, y), c in board.items() if c == player):
            return 10000
    else:
        if any(y == 1 for (x, y), c in board.items() if c == player):
            return 10000

    if opponent == "white":
        if any(y == BOARD_SIZE for (x, y), c in board.items() if c == opponent):
            return -10000
    else:
        if any(y == 1 for (x, y), c in board.items() if c == opponent):
            return -10000

    my_score = 0.0
    opp_score = 0.0
    for (x, y), c in board.items():
        # progress towards promotion
        if c == "white":
            prog = y - 1
        else:          # black
            prog = BOARD_SIZE - y
        base = prog * 10 + 5
        centre = max(0.0, 3.0 - abs(x - 4.5))
        if c == player:
            my_score += base + centre
        else:
            opp_score += base + centre

    my_moves = len(generate_moves(board, player))
    opp_moves = len(generate_moves(board, opponent))
    mobility = (my_moves - opp_moves) * 0.5

    return my_score - opp_score + mobility

# ----------------------------------------------------------------------
# Minimax search (depth‑limited) ---------------------------------------
def search(board, depth, maximizing, player):
    """Return the minimax value for the position.  `player` is the original
       side whose perspective the evaluation uses."""
    opponent = ROLE_OPPONENT[player]

    if depth == 0:
        return evaluate(board, player)

    if maximizing:
        moves = generate_moves(board, player)
        if not moves:
            return -10000
        ordered = order_moves(board, moves, player)
        best = -float('inf')
        for mv in ordered:
            nb = apply_move(board, mv)
            val = search(nb, depth - 1, False, player)
            if val > best:
                best = val
        return best
    else:
        moves = generate_moves(board, opponent)
        if not moves:
            return 10000
        ordered = order_moves(board, moves, opponent)
        worst = float('inf')
        for mv in ordered:
            nb = apply_move(board, mv)
            val = search(nb, depth - 1, True, player)
            if val < worst:
                worst = val
        return worst

# ----------------------------------------------------------------------
# Choose best move -----------------------------------------------------
def best_move(board, player):
    """Return the move (x1,y1,x2,y2) chosen by the policy."""
    moves = generate_moves(board, player)
    if not moves:
        return None

    # Immediate win?
    for mv in moves:
        _, _, x2, y2 = mv
        if (player == "white" and y2 == BOARD_SIZE) or (player == "black" and y2 == 1):
            return mv

    ordered = order_moves(board, moves, player)
    opponent = ROLE_OPPONENT[player]

    best_val = -float('inf')
    chosen = ordered[0]          # fallback
    for mv in ordered:
        nb = apply_move(board, mv)
        # depth‑2 search: opponent replies (depth‑1) and our follow‑up (depth‑0)
        val = search(nb, depth=2, maximizing=False, player=player)
        if val > best_val:
            best_val = val
            chosen = mv
    return chosen

# ----------------------------------------------------------------------
# Public policy ---------------------------------------------------------
def policy(state, role):
    """
    Stanford GameMaster compatible policy.
    `state` – list of Stanford propositions.
    `role`  – 'white' or 'black'.
    Returns a legal move in Stanford syntax, e.g. 'move(1,2,1,3)'.
    """
    board = parse_board(state)
    move = best_move(board, role)
    if move is None:                     # should never happen
        moves = generate_moves(board, role)
        move = moves[0] if moves else (1, 1, 1, 2)
    x1, y1, x2, y2 = move
    return f"move({x1},{y1},{x2},{y2})"
