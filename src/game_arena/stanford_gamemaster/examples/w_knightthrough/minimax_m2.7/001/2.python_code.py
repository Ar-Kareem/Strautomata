
import copy
import random
from typing import Dict, List, Tuple, Optional

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
INF = 10 ** 9
GOAL_BONUS = 10000

COLS = 'abcdefgh'
COL_IDX = {c: i for i, c in enumerate(COLS)}          # 'a' -> 0, ..., 'h' -> 7

# Forward knight offsets for each colour:
#   white moves to larger row numbers, black to smaller row numbers.
OFFSETS = {
    'white': [(1, 2), (-1, 2), (2, 1), (-2, 1)],
    'black': [(1, -2), (-1, -2), (2, -1), (-2, -1)]
}

# ----------------------------------------------------------------------
# State parsing
# ----------------------------------------------------------------------
def parse_state(state: List[List[object]]) -> Dict[Tuple[str, int], str]:
    """
    Convert the list of Stanford propositions into a dict:
        (col_letter, row_number) -> 'white' or 'black'
    Only 'cell' facts are relevant.
    """
    board: Dict[Tuple[str, int], str] = {}
    for fact in state:
        if fact[0] == 'cell':
            col = fact[1]          # e.g. 'a'
            row = int(fact[2])    # e.g. 1
            colour = fact[3]      # 'white' or 'black'
            board[(col, row)] = colour
        # We ignore other fact types (e.g. 'control') – the role is given explicitly.
    return board

# ----------------------------------------------------------------------
# Move generation
# ----------------------------------------------------------------------
def generate_moves(board: Dict[Tuple[str, int], str], role: str) -> List[Tuple[str, int, str, int]]:
    """
    Return a list of all legal knight moves for `role` on `board`.
    Each move is a tuple (src_col, src_row, dst_col, dst_row).
    """
    moves: List[Tuple[str, int, str, int]] = []
    offsets = OFFSETS[role]

    for (col, row), colour in board.items():
        if colour != role:
            continue
        for dc, dr in offsets:
            new_col = chr(ord(col) + dc)
            new_row = row + dr
            # stay inside the board
            if not ('a' <= new_col <= 'h' and 1 <= new_row <= 8):
                continue
            dest = (new_col, new_row)
            # own piece blocks the square
            if dest in board and board[dest] == role:
                continue
            moves.append((col, row, new_col, new_row))
    return moves

# ----------------------------------------------------------------------
# Move application (pure, returns a new board)
# ----------------------------------------------------------------------
def apply_move(board: Dict[Tuple[str, int], str],
               move: Tuple[str, int, str, int],
               role: str) -> Dict[Tuple[str, int], str]:
    """Return a new board after performing the given move."""
    src_col, src_row, dst_col, dst_row = move
    new_board = dict(board)
    # remove piece from source square
    del new_board[(src_col, src_row)]
    # place piece on destination (captures any opponent piece already there)
    new_board[(dst_col, dst_row)] = role
    return new_board

# ----------------------------------------------------------------------
# Goal detection
# ----------------------------------------------------------------------
def is_winning_move(move: Tuple[str, int, str, int], role: str) -> bool:
    """True if the move reaches the opposite back rank."""
    _, _, _, dst_row = move
    if role == 'white':
        return dst_row == 8
    else:  # black
        return dst_row == 1

# ----------------------------------------------------------------------
# Board evaluation (higher is better for `role`)
# ----------------------------------------------------------------------
def evaluate_board(board: Dict[Tuple[str, int], str], role: str) -> int:
    """
    Heuristic evaluation from the perspective of `role`.
    +GOAL_BONUS if `role` has a piece on the opposite back rank,
    -GOAL_BONUS if the opponent already has a piece on its back rank,
    otherwise    (sum of opponent distances) - (sum of own distances).
    """
    opponent = 'black' if role == 'white' else 'white'

    # Immediate win / loss check
    for (col, row), colour in board.items():
        if colour == role:
            if (role == 'white' and row == 8) or (role == 'black' and row == 1):
                return GOAL_BONUS
        else:  # opponent piece
            if (role == 'white' and row == 1) or (role == 'black' and row == 8):
                return -GOAL_BONUS

    own_dist_sum = 0
    opp_dist_sum = 0
    for (col, row), colour in board.items():
        if colour == role:
            if role == 'white':
                own_dist_sum += (8 - row)
            else:
                own_dist_sum += (row - 1)
        else:
            if role == 'white':
                opp_dist_sum += (row - 1)
            else:
                opp_dist_sum += (8 - row)

    # Larger is better for us: opponent far, ourselves close.
    return opp_dist_sum - own_dist_sum

# ----------------------------------------------------------------------
# Depth‑2 minimax search (our move, then opponent reply)
# ----------------------------------------------------------------------
def best_move_depth2(board: Dict[Tuple[str, int], str],
                    role: str) -> Optional[Tuple[str, int, str, int]]:
    """
    Return the move that maximises the worst‑case evaluation after one opponent reply.
    If several moves tie, we pick one arbitrarily (first encountered).
    """
    own_moves = generate_moves(board, role)
    if not own_moves:
        return None

    opponent = 'black' if role == 'white' else 'white'
    best_value = -INF
    best_move = None

    for move in own_moves:
        # Immediate winning move?
        if is_winning_move(move, role):
            return move

        # Simulate our move
        board_after = apply_move(board, move, role)

        # Generate opponent replies
        opp_moves = generate_moves(board_after, opponent)
        if not opp_moves:
            # Opponent cannot move → we effectively win
            return move

        # Worst‑case value for us after opponent's best reply
        worst_value = INF
        for opp_move in opp_moves:
            board_after_opp = apply_move(board_after, opp_move, opponent)
            val = evaluate_board(board_after_opp, role)
            if val < worst_value:
                worst_value = val
                # prune if we already know this branch is worse than current best
                if worst_value <= best_value:
                    break
        if worst_value > best_value:
            best_value = worst_value
            best_move = move

    return best_move

# ----------------------------------------------------------------------
# Main policy entry point
# ----------------------------------------------------------------------
def policy(state: List[List[object]], role: str) -> str:
    """
    Stanford GameMaster policy for Knightthrough.
    Returns a legal move string like 'move(a,1,b,3)'.
    """
    # Parse the board
    board = parse_state(state)

    # Generate all legal moves for the current player
    moves = generate_moves(board, role)
    if not moves:
        # Defensive fallback – should never happen in a real game.
        # Return a dummy move; the arena will likely reject it,
        # but this avoids a crash.
        return "move(a,1,b,3)"

    # Check for an immediate winning move first
    for m in moves:
        if is_winning_move(m, role):
            src_col, src_row, dst_col, dst_row = m
            return f"move({src_col},{src_row},{dst_col},{dst_row})"

    # Use depth‑2 search to pick the best move
    chosen = best_move_depth2(board, role)
    if chosen is None:
        # Fallback – just return the first legal move
        chosen = moves[0]

    src_col, src_row, dst_col, dst_row = chosen
    return f"move({src_col},{src_row},{dst_col},{dst_row})"

# ----------------------------------------------------------------------
# Optional: quick self‑test (not executed in the submission environment)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Example state from the problem statement (Turn 0, white to move)
    example_state = [
        ["cell", "a", "1", "white"], ["cell", "b", "1", "white"],
        ["cell", "c", "1", "white"], ["cell", "d", "1", "white"],
        ["cell", "e", "1", "white"], ["cell", "f", "1", "white"],
        ["cell", "g", "1", "white"], ["cell", "h", "1", "white"],
        ["cell", "a", "2", "white"], ["cell", "b", "2", "white"],
        ["cell", "c", "2", "white"], ["cell", "d", "2", "white"],
        ["cell", "e", "2", "white"], ["cell", "f", "2", "white"],
        ["cell", "g", "2", "white"], ["cell", "h", "2", "white"],
        ["cell", "a", "7", "black"], ["cell", "b", "7", "black"],
        ["cell", "c", "7", "black"], ["cell", "d", "7", "black"],
        ["cell", "e", "7", "black"], ["cell", "f", "7", "black"],
        ["cell", "g", "7", "black"], ["cell", "h", "7", "black"],
        ["cell", "a", "8", "black"], ["cell", "b", "8", "black"],
        ["cell", "c", "8", "black"], ["cell", "d", "8", "black"],
        ["cell", "e", "8", "black"], ["cell", "f", "8", "black"],
        ["cell", "g", "8", "black"], ["cell", "h", "8", "black"],
        ["control", "white"]
    ]
    print(policy(example_state, "white"))
