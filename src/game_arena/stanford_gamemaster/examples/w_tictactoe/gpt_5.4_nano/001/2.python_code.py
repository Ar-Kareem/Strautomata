
import math
from functools import lru_cache

def policy(state: list[list[object]], role: str) -> str:
    # Map board from state facts: ["cell", r, c, mark]
    board = [["b"] * 3 for _ in range(3)]
    for fact in state:
        if isinstance(fact, list) and len(fact) == 4 and fact[0] == "cell":
            r, c, m = int(fact[1]), int(fact[2]), fact[3]
            if 1 <= r <= 3 and 1 <= c <= 3 and m in ("x", "o", "b"):
                board[r-1][c-1] = m

    me = role  # "x" or "o"
    other = "o" if me == "x" else "x"

    def winner(b):
        # returns 'x'/'o'/'b'(none)
        lines = []
        lines.extend([b[i] for i in range(3)])  # rows
        lines.extend([[b[0][j], b[1][j], b[2][j]] for j in range(3)])  # cols
        lines.append([b[0][0], b[1][1], b[2][2]])
        lines.append([b[0][2], b[1][1], b[2][0]])
        for line in lines:
            if line[0] != "b" and line[0] == line[1] == line[2]:
                return line[0]
        return "b"

    def to_key(b, turn):
        # Encode as string for memoization
        s = "".join(b[r][c] for r in range(3) for c in range(3)) + "|" + turn
        return s

    def available_moves(b):
        moves = []
        for r in range(3):
            for c in range(3):
                if b[r][c] == "b":
                    moves.append((r, c))
        return moves

    def apply_move(b, r, c, mark):
        nb = [row[:] for row in b]
        nb[r][c] = mark
        return nb

    # Determine whose turn it is based on counts, but trust role as current player.
    # We'll use 'turn' variable in minimax starting with role.
    turn0 = me

    @lru_cache(maxsize=None)
    def minimax(key):
        # key is encoded: boardstr|turn
        boardstr, turn = key.split("|")
        b = [[boardstr[r*3 + c] for c in range(3)] for r in range(3)]
        w = winner(b)
        if w != "b":
            if w == me:
                return 1  # win
            else:
                return -1  # loss
        moves = available_moves(b)
        if not moves:
            return 0  # draw

        # Current player for this node is 'turn'
        next_turn = other if turn == me else me

        # If it's me to play, maximize; else minimize
        if turn == me:
            best = -2
            for r, c in moves:
                nb = apply_move(b, r, c, turn)
                val = minimax(to_key(nb, next_turn))
                if val > best:
                    best = val
                if best == 1:
                    break
            return best
        else:
            best = 2
            for r, c in moves:
                nb = apply_move(b, r, c, turn)
                val = minimax(to_key(nb, next_turn))
                if val < best:
                    best = val
                if best == -1:
                    break
            return best

    # Choose best move for the current role
    best_val = -2
    best_move = None
    moves = available_moves(board)

    # Move ordering: center, corners, edges for faster pruning
    priority = [(1,1), (0,0),(0,2),(2,0),(2,2), (0,1),(1,0),(1,2),(2,1)]
    moves_sorted = sorted(moves, key=lambda rc: priority.index(rc) if rc in priority else 99)

    for r, c in moves_sorted:
        nb = apply_move(board, r, c, me)
        val = minimax(to_key(nb, other))
        if val > best_val:
            best_val = val
            best_move = (r, c)
        if best_val == 1:
            break

    # Safety fallback (shouldn't be needed)
    if best_move is None:
        # pick any empty cell
        r, c = moves[0]
        best_move = (r, c)

    r, c = best_move
    return f"mark({r+1},{c+1})"
