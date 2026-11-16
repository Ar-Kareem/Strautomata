
import numpy as np

# Directions for queen‑like movement (orthogonal and diagonal)
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

def generate_moves(board, player):
    """
    Return a list of possible moves for `player` (1 = us, 2 = opponent).
    Each move is a tuple ((fr,fc),(tr,tc),(ar,ac)).
    """
    moves = []
    # Locate player's amazon(s)
    for r in range(6):
        for c in range(6):
            if board[r, c] == player:
                # Try every direction for the movement
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                        # The destination (nr,nc) is empty – now consider arrow shots.
                        # Create a temporary board where the amazon has been moved.
                        tmp = board.copy()
                        tmp[r, c] = 0
                        tmp[nr, nc] = player

                        # Shoot arrow from (nr,nc)
                        for dr2, dc2 in DIRS:
                            ar, ac = nr + dr2, nc + dc2
                            while 0 <= ar < 6 and 0 <= ac < 6 and tmp[ar, ac] == 0:
                                moves.append(((r, c), (nr, nc), (ar, ac)))
                                ar += dr2
                                ac += dc2

                        nr += dr
                        nc += dc
    return moves


def apply_move(board, move, player):
    """Return a new board after applying `move` by `player`."""
    (fr, fc), (tr, tc), (ar, ac) = move
    new_board = board.copy()
    new_board[fr, fc] = 0
    new_board[tr, tc] = player
    new_board[ar, ac] = -1          # arrow blocks the square
    return new_board


def evaluate(board):
    """
    Simple evaluation: difference in mobility plus a small centre‑weight.
    Positive values favour us.
    """
    my_moves = len(generate_moves(board, 1))
    opp_moves = len(generate_moves(board, 2))

    # Optional centre bonus – prefer squares near the centre (2.5,2.5)
    bonus = 0.0
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:
                bonus += (3.0 - (abs(r - 2.5) + abs(c - 2.5)) / 2.0) * 0.1
            elif board[r, c] == 2:
                bonus -= (3.0 - (abs(r - 2.5) + abs(c - 2.5)) / 2.0) * 0.1

    return (my_moves - opp_moves) + bonus


def best_move(board):
    """Return the move chosen by depth‑2 minimax."""
    my_moves = generate_moves(board, 1)
    if not my_moves:
        return None

    # 1) Immediate winning move?
    for move in my_moves:
        nxt = apply_move(board, move, 1)
        if not generate_moves(nxt, 2):       # opponent has no move → we win
            return move

    # 2) Depth‑2 search: look ahead to opponent's best response.
    best_score = -10**9
    chosen = my_moves[0]

    for move in my_moves:
        nxt = apply_move(board, move, 1)
        opp_moves = generate_moves(nxt, 2)

        # Opponent will choose the response that minimises our score.
        worst = 10**9
        for opp_move in opp_moves:
            nxt2 = apply_move(nxt, opp_move, 2)
            score = evaluate(nxt2)
            if score < worst:
                worst = score

        # We want to maximise the worst‑case score.
        if worst > best_score:
            best_score = worst
            chosen = move

    return chosen


def move_to_string(move):
    (fr, fc), (tr, tc), (ar, ac) = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    """
    Main entry point required by the arena.
    `board` is a 6x6 numpy array (dtype int):
        0 – empty,  1 – our amazon, 2 – opponent amazon, -1 – arrow.
    Returns a move string "r1,c1:r2,c2:r3,c3".
    """
    move = best_move(board)
    if move is None:
        # Should never happen (the environment guarantees a move exists)
        return ""
    return move_to_string(move)
