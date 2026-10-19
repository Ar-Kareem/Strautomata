
import numpy as np

# Board is fixed: 5 rows x 6 cols
ROWS, COLS = 5, 6

DIRS = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1),
}

def _to_arr(x):
    a = np.array(x, dtype=int)
    if a.shape != (ROWS, COLS):
        a = a.reshape((ROWS, COLS))
    return a

def _legal_moves(you, opp):
    moves = []
    # own pieces
    ys = np.argwhere(you == 1)
    for r, c in ys:
        for dch, (dr, dc) in DIRS.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and opp[nr, nc] == 1:
                moves.append((r, c, dch))
    return moves

def _apply_move(you, opp, move):
    r, c, dch = move
    dr, dc = DIRS[dch]
    nr, nc = r + dr, c + dc
    # assumes legal
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 0
    new_opp[nr, nc] = 0
    new_you[nr, nc] = 1
    return new_you, new_opp

def _score_move(you, opp, move):
    # 1-ply lookahead:
    # After we play move, estimate:
    #   - opponent's mobility decreases => good
    #   - our mobility increases => good
    # Also incorporate piece removal proximity and avoiding giving opponent many captures.
    new_you, new_opp = _apply_move(you, opp, move)

    my_moves = _legal_moves(new_you, new_opp)
    opp_moves = _legal_moves(new_opp, new_you)  # opponent's moves if turn switches

    # Primary: minimize opponent mobility
    # Secondary: maximize our mobility
    # Tertiary: prefer moves that reduce total opponent pieces
    opp_piece_count_before = int(np.sum(opp))
    opp_piece_count_after = int(np.sum(new_opp))
    removed = opp_piece_count_before - opp_piece_count_after  # should be 1 for legal move

    # Additional micro-tactic: prefer capturing pieces that are "threatening"
    # i.e., the captured square had many adjacent own pieces (meaning it enabled many captures).
    r, c, dch = move
    dr, dc = DIRS[dch]
    tr, tc = r + dr, c + dc  # target / captured location
    # count adjacent opponent-neighborhood? We want count of our pieces adjacent to target pre-capture
    # because those create capture opportunities for the opponent after the swap pattern.
    adj_ours = 0
    for (ddr, ddc) in DIRS.values():
        ar, ac = tr + ddr, tc + ddc
        if 0 <= ar < ROWS and 0 <= ac < COLS and you[ar, ac] == 1:
            adj_ours += 1

    # Weighted score (higher is better)
    score = 0
    score += 5.0 * (0 - len(opp_moves))          # fewer opp moves is better
    score += 1.5 * (len(my_moves))             # more of our moves is better
    score += 0.8 * removed                     # always 1, but keep structure
    score += 0.2 * adj_ours                   # slight preference if we captured a "connected" piece
    return score

def policy(you: list[int], opponent: list[int]) -> str:
    you = _to_arr(you)
    opp = _to_arr(opponent)

    moves = _legal_moves(you, opp)
    # Must always return a legal move; if none, return any placeholder (but arena says disqualify;
    # typically game ends before policy called). Still, provide safest fallback: scan for any legal.
    if not moves:
        # No legal moves: return '0,0,U' as fallback (may be disallowed if called in terminal state)
        # but in normal play policy shouldn't be invoked.
        return "0,0,U"

    # Choose best scored move
    best_move = None
    best_score = -1e18
    # Shuffle-like deterministic ordering to ensure varied play: sort by (r,c,dir)
    dir_order = ['U', 'R', 'D', 'L']
    moves_sorted = sorted(moves, key=lambda m: (m[0], m[1], dir_order.index(m[2])))

    for mv in moves_sorted:
        sc = _score_move(you, opp, mv)
        # Tie-break: prefer moves that immediately increase our mobility and reduce opponent mobility most
        if sc > best_score:
            best_score = sc
            best_move = mv
        elif sc == best_score and best_move is not None:
            # Tie-break deterministically
            # compare (opp mobility, my mobility, row, col, dir)
            new_you, new_opp = _apply_move(you, opp, mv)
            my_moves = len(_legal_moves(new_you, new_opp))
            opp_moves = len(_legal_moves(new_opp, new_you))
            bnew_you, bnew_opp = _apply_move(you, opp, best_move)
            bmy = len(_legal_moves(bnew_you, bnew_opp))
            bopp = len(_legal_moves(bnew_opp, bnew_you))
            if (opp_moves, -my_moves, mv[0], mv[1], mv[2]) < (bopp, -bmy, best_move[0], best_move[1], best_move[2]):
                best_move = mv

    r, c, dch = best_move
    return f"{r},{c},{dch}"
