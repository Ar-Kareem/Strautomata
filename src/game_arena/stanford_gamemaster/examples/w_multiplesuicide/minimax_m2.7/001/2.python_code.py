
import random

# ----------------------------------------------------------------------
# Helper functions for the 3x3 middle board (board (2,2))
# ----------------------------------------------------------------------
def parse_state(state):
    """
    Parse the raw Stanford fact list.
    Returns:
        - central: 3x3 list with 'x','o','b' (empty) for the middle board.
        - non_central_empty: list of (boardRow, boardCol, row, col) of empty cells outside the middle board.
    """
    # initialise middle board as empty
    central = [['b' for _ in range(3)] for __ in range(3)]
    non_central_empty = []

    for fact in state:
        if not isinstance(fact, list) or fact[0] != 'cell':
            continue
        br = int(fact[1])
        bc = int(fact[2])
        r = int(fact[3])
        c = int(fact[4])
        mark = fact[5]

        if br == 2 and bc == 2:
            # middle board
            central[r - 1][c - 1] = mark
        else:
            if mark == 'b':
                non_central_empty.append((br, bc, r, c))

    return central, non_central_empty


def is_line(board, player):
    """Return True if `player` has a three‑in‑a‑row on the 3x3 board."""
    # rows
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True
    # columns
    for j in range(3):
        if all(board[i][j] == player for i in range(3)):
            return True
    # diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False


def minimax(board, player):
    """
    Misère minimax for a 3x3 board.
    Returns:
        +1  – the current player can force a win (opponent will be the one to make a line).
        -1  – the current player will inevitably lose.
         0  – draw.
    """
    empties = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 'b']
    if not empties:
        # full board with no line -> draw
        return 0

    # Try to find a winning move
    for i, j in empties:
        board[i][j] = player
        if is_line(board, player):
            # making a line is an immediate loss for the mover
            board[i][j] = 'b'
            continue
        opp = 'o' if player == 'x' else 'x'
        result = minimax(board, opp)
        board[i][j] = 'b'
        if result == -1:
            # opponent loses => we win
            return 1

    # No winning move – try to force a draw
    for i, j in empties:
        board[i][j] = player
        if is_line(board, player):
            board[i][j] = 'b'
            continue
        opp = 'o' if player == 'x' else 'x'
        result = minimax(board, opp)
        board[i][j] = 'b'
        if result == 0:
            return 0

    # All moves lead to loss
    return -1


def best_central_move(central_board, player):
    """
    Choose the best safe move on the middle board.
    Returns (row, col) in 0‑based coordinates.
    """
    empties = [(i, j) for i in range(3) for j in range(3) if central_board[i][j] == 'b']
    # filter out moves that would create a line for us
    safe_moves = []
    for i, j in empties:
        central_board[i][j] = player
        if is_line(central_board, player):
            central_board[i][j] = 'b'
            continue
        central_board[i][j] = 'b'
        safe_moves.append((i, j))

    if not safe_moves:
        # Every move loses – just pick any empty cell
        return empties[0] if empties else (0, 0)

    # Evaluate each safe move; take the first one that leads to a win
    for i, j in safe_moves:
        central_board[i][j] = player
        opp = 'o' if player == 'x' else 'x'
        result = minimax(central_board, opp)
        outcome = -result  # outcome for the player who just moved
        central_board[i][j] = 'b'
        if outcome == 1:
            return (i, j)

    # No winning move – settle for a drawing move (if any)
    for i, j in safe_moves:
        central_board[i][j] = player
        opp = 'o' if player == 'x' else 'x'
        result = minimax(central_board, opp)
        central_board[i][j] = 'b'
        if -result == 0:
            return (i, j)

    # All safe moves lead to loss – return any of them
    return safe_moves[0]


# ----------------------------------------------------------------------
# Main policy entry point
# ----------------------------------------------------------------------
def policy(state, role):
    """
    Stanford GameMaster policy for the 'multiplesuicide' game.
    `state` – list of facts (see description)
    `role`  – 'x' or 'o'
    Returns a legal action string like 'mark(2,2,1,1)'.
    """
    # Parse the board
    central_board, non_central_empty = parse_state(state)

    # If there is any free cell outside the middle board, play there.
    if non_central_empty:
        # Randomly choose one of the available non‑central cells
        br, bc, r, c = random.choice(non_central_empty)
        return f"mark({br},{bc},{r},{c})"

    # No non‑central moves left – we must play on the middle board.
    row, col = best_central_move(central_board, role)
    # Convert to 1‑based indices for the action string
    return f"mark(2,2,{row + 1},{col + 1})"
