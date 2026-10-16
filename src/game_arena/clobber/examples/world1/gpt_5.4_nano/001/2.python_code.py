
import numpy as np
from functools import lru_cache

# Board dimensions
ROWS = 5
COLS = 6

DIRS = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1),
}

DIR_ORDER = ['U', 'R', 'D', 'L']  # deterministic tie-break

def _legal_moves(you: np.ndarray, opp: np.ndarray):
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if you[r, c] != 1:
                continue
            for dchar in DIR_ORDER:
                dr, dc = DIRS[dchar]
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and opp[nr, nc] == 1:
                    moves.append((r, c, dchar))
    return moves

def _apply_move(you: np.ndarray, opp: np.ndarray, move):
    r, c, dchar = move
    dr, dc = DIRS[dchar]
    nr, nc = r + dr, c + dc
    new_you = you.copy()
    new_opp = opp.copy()
    # capture: move onto opponent cell
    new_you[r, c] = 0
    new_you[nr, nc] = 1
    new_opp[nr, nc] = 0
    return new_you, new_opp

def _mobility(you: np.ndarray, opp: np.ndarray) -> int:
    return len(_legal_moves(you, opp))

def _count_pieces(you: np.ndarray) -> int:
    return int(you.sum())

def _board_to_key(you: np.ndarray, opp: np.ndarray):
    # Compact deterministic key for memoization (27 bits each max, but use bytes)
    return (you.tobytes(), opp.tobytes())

def policy(you: list[int], opponent: list[int]) -> str:
    you_arr = np.array(you, dtype=np.int8).reshape((ROWS, COLS))
    opp_arr = np.array(opponent, dtype=np.int8).reshape((ROWS, COLS))

    moves = _legal_moves(you_arr, opp_arr)
    if not moves:
        # No legal move: return a legal-looking fallback (should not occur per rules that player to move loses).
        # But to satisfy output format, just return something deterministic.
        return "0,0,U"

    # Shallow minimax with evaluation:
    # Terminal: if opponent has no moves after our move -> we win (score +inf)
    # Also discourage giving opponent very high mobility.
    # We also prefer capturing that reduces opponent pieces and increases our mobility.
    eval_weights = {
        "mobility": 10.0,
        "pieces": 1.0,
        "mobility_delta": 12.0,
        "capture_punish": 2.0,
    }

    # Limit search depth for speed: 2 plies (our move, opponent reply) plus one more for tactical resolution.
    # We'll do iterative: depth 2 first, then extend if branching is small.
    def evaluate_state(you_s: np.ndarray, opp_s: np.ndarray):
        # Heuristic score from perspective of the player whose pieces are `you_s`
        my_m = _mobility(you_s, opp_s)
        opp_m = _mobility(opp_s, you_s)  # opponent to move would see (opp as "you" in that role)
        # Pieces count
        my_p = _count_pieces(you_s)
        opp_p = _count_pieces(opp_s)

        # Mobility advantage is very important in Clobber
        score = 0.0
        score += eval_weights["mobility"] * my_m
        score += eval_weights["pieces"] * (my_p - opp_p)
        score += eval_weights["mobility_delta"] * (my_m - opp_m)

        # Small bias: prefer fewer opponent pieces (captured many)
        score -= eval_weights["capture_punish"] * max(0, opp_p - my_p) * 0.05
        return score

    # Memoized minimax
    @lru_cache(maxsize=20000)
    def minimax(you_key: bytes, opp_key: bytes, depth: int, turn: int):
        # turn: 0 -> our perspective player to move has state (you, opp)
        # We'll reconstruct arrays from keys by using frombuffer (small fixed size, ok).
        you_s = np.frombuffer(you_key, dtype=np.int8).reshape((ROWS, COLS))
        opp_s = np.frombuffer(opp_key, dtype=np.int8).reshape((ROWS, COLS))

        legal = _legal_moves(you_s, opp_s)
        if depth == 0 or not legal:
            # If no legal moves for current player -> losing for current player.
            if not legal:
                return -1e9  # current player loses
            return evaluate_state(you_s, opp_s)

        # For current player: if it's our turn (turn==0) we maximize, else opponent's turn maximize for opponent
        # But since evaluation is always from perspective of the "you_s" player, we can just alternate who is the maximizer by using turn.
        if turn == 0:
            best = -1e18
            for mv in legal:
                n_you, n_opp = _apply_move(you_s, opp_s, mv)
                nk = _board_to_key(n_you, n_opp)
                # After our move, roles swap for opponent's turn: opponent becomes "current player's you"
                val = minimax(nk[0], nk[1], depth - 1, 1)
                if val > best:
                    best = val
            return best
        else:
            best = 1e18
            for mv in legal:
                n_you, n_opp = _apply_move(you_s, opp_s, mv)
                nk = _board_to_key(n_you, n_opp)
                val = minimax(nk[0], nk[1], depth - 1, 0)
                if val < best:
                    best = val
            return best

    # Determine depth based on branching factor
    branching = len(moves)
    depth = 3 if branching <= 10 else 2  # keep fast

    # First pass: immediate win / avoid immediate loss + heuristic mobility
    best_moves = []
    best_score = -1e18

    for mv in moves:
        n_you, n_opp = _apply_move(you_arr, opp_arr, mv)

        # If opponent has no moves after our move, it's a winning move
        opp_legal = _legal_moves(n_opp, n_you)  # opponent to move sees its pieces as "you"
        if not opp_legal:
            return f"{mv[0]},{mv[1]},{mv[2]}"

        # Otherwise, run minimax from resulting state.
        nk = _board_to_key(n_you, n_opp)
        val = minimax(nk[0], nk[1], depth - 1, 1)  # opponent to move next
        # Add light tie-break on mobility
        my_m = _mobility(n_you, n_opp)
        val += 0.25 * my_m

        if val > best_score + 1e-9:
            best_score = val
            best_moves = [mv]
        elif abs(val - best_score) <= 1e-9:
            best_moves.append(mv)

    # Deterministic selection among best moves:
    # Prefer moves that maximize our mobility and reduce opponent mobility.
    if len(best_moves) == 1:
        mv = best_moves[0]
        return f"{mv[0]},{mv[1]},{mv[2]}"

    scored = []
    for mv in best_moves:
        n_you, n_opp = _apply_move(you_arr, opp_arr, mv)
        my_m = _mobility(n_you, n_opp)
        opp_m = _mobility(n_opp, n_you)
        scored.append((my_m - opp_m, my_m, -_count_pieces(n_opp), mv))
    scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    mv = scored[0][3]
    return f"{mv[0]},{mv[1]},{mv[2]}"
