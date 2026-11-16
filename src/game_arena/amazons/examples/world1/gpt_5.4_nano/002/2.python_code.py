
import numpy as np
from typing import List, Tuple, Optional

N = 6

DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

def inb(r, c):
    return 0 <= r < N and 0 <= c < N

def queen_lines(from_r, from_c):
    for dr, dc in DIRS:
        r, c = from_r + dr, from_c + dc
        while inb(r, c):
            yield dr, dc, r, c
            r += dr
            c += dc

def parse_move(move: str):
    a, b, c = move.split(':')
    fr, fc = map(int, a.split(','))
    tr, tc = map(int, b.split(','))
    ar, ac = map(int, c.split(','))
    return fr, fc, tr, tc, ar, ac

def move_to_str(fr, fc, tr, tc, ar, ac):
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

def generate_moves(board: np.ndarray, player_val: int) -> List[Tuple[int,int,int,int,int,int]]:
    # board: 6x6 with 0 empty, 1 our, 2 opp, -1 arrow
    # player_val is 1 or 2
    opp_val = 2 if player_val == 1 else 1
    moves = []
    my_positions = np.argwhere(board == player_val)
    for fr, fc in my_positions:
        # Try amazon move to empty to
        for dr, dc, tr, tc in queen_lines(fr, fc):
            if board[tr, tc] != 0:
                break  # blocked further in this direction
            # Simulate move
            # We vacate (fr,fc), occupy (tr,tc)
            # Then arrow from (tr,tc) to empty square along queen lines on updated board
            # For shot legality, treat (fr,fc) as empty after move.
            # We'll check unobstructed with updated occupancy.
            for adr, adc, ar, ac in queen_lines(tr, tc):
                # Determine if path squares are empty in the updated board
                if board[ar, ac] != 0:
                    break
                # Need to ensure arrow path from (tr,tc) doesn't cross any non-empty squares,
                # but queen_lines already steps square-by-square; we must ensure intermediate squares empty too.
                # We'll check by stepping.
                rr, cc = tr + adr, tc + adc
                ok = True
                while (rr, cc) != (ar, ac):
                    # intermediate squares in updated state:
                    # (fr,fc) is now empty; (tr,tc) has our amazon; no other changes.
                    val = board[rr, cc]
                    if rr == fr and cc == fc:
                        val = 0
                    # tr,tc is starting point, so intermediates won't be it.
                    if val != 0:
                        ok = False
                        break
                    rr += adr
                    cc += adc
                if not ok:
                    continue
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves

def apply_move(board: np.ndarray, move: Tuple[int,int,int,int,int,int], player_val: int) -> np.ndarray:
    fr, fc, tr, tc, ar, ac = move
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = player_val
    b[ar, ac] = -1
    return b

def count_legal_moves(board: np.ndarray, player_val: int) -> int:
    return len(generate_moves(board, player_val))

def mobility_score(board: np.ndarray) -> int:
    # Higher is better for player 1
    m1 = count_legal_moves(board, 1)
    m2 = count_legal_moves(board, 2)
    return m1 - m2

def tactical_score(board_after: np.ndarray) -> int:
    # Composite heuristic for player 1
    # - mobility diff
    # - slight bonus for being closer to opponent (sum of negative distances from ours to opps)
    sc = mobility_score(board_after)

    opp_positions = np.argwhere(board_after == 2)
    my_positions = np.argwhere(board_after == 1)
    if len(opp_positions) > 0 and len(my_positions) > 0:
        # Use Manhattan-ish shortest along queen? We'll use Chebyshev distance (king distance)
        # because queen moves correspond to chebyshev lines.
        dist_sum = 0
        for r1, c1 in my_positions:
            best = 10
            for r2, c2 in opp_positions:
                d = max(abs(r1 - r2), abs(c1 - c2))
                if d < best:
                    best = d
            dist_sum += best
        # Prefer smaller distance sum; scale down
        sc += int(20 - dist_sum)  # heuristic cap-ish
    return sc

def pick_best_move(board: np.ndarray) -> Optional[Tuple[int,int,int,int,int,int]]:
    my_moves = generate_moves(board, 1)
    if not my_moves:
        return None

    # Shallow lookahead:
    # For each move, evaluate:
    # our mobility - sampled opponent best mobility after we move.
    # sample up to K opponent moves for speed; use max/min adversarial.
    K = 18

    best_move = my_moves[0]
    best_val = -10**9

    for mv in my_moves:
        b1 = apply_move(board, mv, 1)
        # If opponent has no moves, we win immediately
        opp_moves = generate_moves(b1, 2)
        if not opp_moves:
            return mv

        # Our immediate score
        base = tactical_score(b1)

        # Opponent response sampling: they try to maximize their mobility diff (i.e., reduce ours)
        # We'll take a worst-case estimate for us: choose response that maximizes (opponent mobility - our mobility),
        # which is equivalent to minimizing our mobility diff.
        # Convert to our perspective: score_after = -mobility_score(b2) roughly.
        # We'll sample and take the minimum of our heuristic over sampled opponent moves.
        worst = base
        # sample opponent moves
        if len(opp_moves) > K:
            # deterministic subsampling: spread by interval
            step = max(1, len(opp_moves) // K)
            sampled = opp_moves[::step][:K]
        else:
            sampled = opp_moves

        for omv in sampled:
            b2 = apply_move(b1, omv, 2)
            # If we are in terminal loss state (no moves for us), punish heavily
            our_after_moves = count_legal_moves(b2, 1)
            if our_after_moves == 0:
                cand = -10**7
            else:
                cand = tactical_score(b2)
            if cand < worst:
                worst = cand

        # Prefer moves that keep worst-case high; add small depth-1 mobility to break ties.
        val = worst * 10 + (count_legal_moves(b1, 1) - count_legal_moves(b1, 2))
        if val > best_val:
            best_val = val
            best_move = mv

    return best_move

def policy(board) -> str:
    board = np.asarray(board)
    mv = pick_best_move(board)
    if mv is None:
        # Robust fallback: return any legal move if available (shouldn't happen if env guarantees legality)
        all_moves = generate_moves(board, 1)
        if not all_moves:
            # No legal moves; return dummy (should never be used)
            return "0,0:0,0:0,0"
        mv = all_moves[0]
    fr, fc, tr, tc, ar, ac = mv
    return move_to_str(fr, fc, tr, tc, ar, ac)

# For arena harnesses that expect the module-level function:
# def policy(board) -> str:
#     ...

