
import numpy as np

ROWS, COLS = 5, 6

DIRS = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1)
}

def _legal_moves(you, opp):
    # Returns list of (r,c,dir, nr,nc)
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if you[r, c] != 1:
                continue
            for dch, (dr, dc) in DIRS.items():
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and opp[nr, nc] == 1:
                    moves.append((r, c, dch, nr, nc))
    return moves

def _apply_move(you, opp, move):
    r, c, dch, nr, nc = move
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 0
    new_you[nr, nc] = 1
    new_opp[nr, nc] = 0
    return new_you, new_opp

def _count_moves(player_you, player_opp):
    return len(_legal_moves(player_you, player_opp))

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you, dtype=int).reshape(ROWS, COLS)
    opponent = np.array(opponent, dtype=int).reshape(ROWS, COLS)

    moves = _legal_moves(you, opponent)
    if not moves:
        # No legal move exists: return any syntactically valid move string.
        # (The game environment should only call policy when a move is required;
        # disqualification is avoided by still returning a legal-looking format.)
        # Find any own piece and attempt a direction (may be illegal in reality).
        for r in range(ROWS):
            for c in range(COLS):
                if you[r, c] == 1:
                    return f"{r},{c},U"
        return "0,0,U"

    # Evaluate each move with a fast 1-ply heuristic.
    # Score favors:
    #  - More mobility for us after the move
    #  - Fewer immediate captures for opponent after the move
    #  - Slight preference for staying central (to reduce being trapped)
    center_r, center_c = (ROWS - 1) / 2.0, (COLS - 1) / 2.0

    best_move = None
    best_score = -10**18

    for move in moves:
        new_you, new_opp = _apply_move(you, opponent, move)
        # After we move, opponent is to play.
        opp_moves_after = _count_moves(new_opp, new_you)
        my_moves_after = _count_moves(new_you, new_opp)

        r, c, dch, nr, nc = move
        # Center/advancement heuristic
        dist_center = abs(nr - center_r) + abs(nc - center_c)
        center_score = -dist_center

        # Big weights to prioritize zugzwang-like effects.
        score = (
            1000 * (my_moves_after)          # maximize our future options
            - 1200 * (opp_moves_after)       # minimize their options
            + 5 * center_score               # small tie-breaker
        )

        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score and best_move is not None:
            # Tie-break: choose move that captures while leaving more for us (already equal),
            # otherwise choose deterministic smallest (r,c,dir).
            if move[:3] < best_move[:3]:
                best_move = move

    r, c, dch, nr, nc = best_move
    return f"{r},{c},{dch}"
