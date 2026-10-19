
import typing
from typing import List, Tuple

def distance_to_home(row: int, color: str) -> int:
    """Return the distance of a piece from its own home row."""
    return 7 - row if color == 'w' else row

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Return a legal move as ((from_row, from_col), (to_row, to_col)).

    The algorithm follows:
    1. Immediate‑win moves (home‑row) are preferred.
    2. Capture moves (diagonal forward onto opponent piece with empty behind) are next.
    3. Forward non‑capture moves that reduce our own distance the most.
    """
    # target home row and forward direction
    target_home = 7 if color == 'w' else 0
    dr = 1 if color == 'w' else -1

    me_set = set(me)
    opp_set = set(opp)

    def is_empty_or_out(r: int, c: int) -> bool:
        """Return True if square is either empty or off‑board (treated as empty)."""
        return (r, c) not in me_set and (r, c) not in opp_set

    # Helper to compute opponent piece distance to its home row
    def opponent_home_dist(tgt: Tuple[int, int]) -> int:
        tr, tc = tgt
        return distance_to_home(tr, color)

    # Gather all legal candidate moves
    candidates = []  # list of dicts with keys: move, score, win, capture

    # Evaluate straight and diagonal forward moves (empty target)
    for (fr, fc) in me:
        # Straight forward
        tr = fr + dr
        if 0 <= tr <= 7:
            if is_empty_or_out(tr, fc):
                new_dist = distance_to_home(tr, color)
                win = tr == target_home
                candidates.append({
                    'move': ((fr, fc), (tr, fc)),
                    'score': new_dist,
                    'win': win,
                    'capture': False,
                    'piece': distance_to_home(fr, color),  # current distance (used later)
                })
        # Diagonal forward left
        for dc in (-1, 1):
            tr = fr + dr
            tc = fc + dc
            if 0 <= tr <= 7 and 0 <= tc <= 7:
                if is_empty_or_out(tr, tc):
                    new_dist = distance_to_home(tr, color)
                    win = tr == target_home
                    candidates.append({
                        'move': ((fr, fc), (tr, tc)),
                        'score': new_dist,
                        'win': win,
                        'capture': False,
                        'piece': distance_to_home(fr, color),
                    })

        # Capture moves (only on diagonal squares)
        for dc in (-1, 1):
            tr = fr + dr
            tc = fc + dc
            if 0 <= tr <= 7 and 0 <= tc <= 7:
                if (tr, tc) in opp_set:
                    # Check the square behind the opponent piece (if it is empty or off‑board)
                    beyond_r = tr + dr
                    beyond_c = tc + dc
                    if is_empty_or_out(beyond_r, beyond_c):
                        # Capture is legal
                        new_dist = distance_to_home(tr, color)   # our piece after capture
                        opp_dist = opponent_home_dist((tr, tc))
                        total_score = new_dist + opp_dist
                        win = (tr, tc) == (target_home, _)   # any capture onto home row wins
                        candidates.append({
                            'move': ((fr, fc), (tr, tc)),
                            'score': total_score,
                            'win': win,
                            'capture': True,
                            'piece': distance_to_home(fr, color),
                        })

    # Prioritise immediate wins
    if any(c['win'] for c in candidates):
        # Prefer captures that win (they remove an opponent piece)
        win_captures = [c for c in candidates if c['win'] and c['capture']]
        if win_captures:
            # Choose any (the first found is fine)
            return win_captures[0]['move']
        # Otherwise any forward win move
        win_forwards = [c for c in candidates if c['win'] and not c['capture']]
        return win_forwards[0]['move']

    # Among remaining captures, pick the best using the total_score heuristic
    if any(c['capture'] for c in candidates):
        best = min(
            (c for c in candidates if c['capture']),
            key=lambda m: (m['score'], -m['piece'])   # first minimize score, then favour larger current distance
        )
        return best['move']

    # No captures: pick the forward move that reduces our distance most
    # Prefer straight moves, then diagonal
    straight = [c for c in candidates if not c['capture'] and c['move'][1][1] == c['move'][0][1]]
    if straight:
        # Minimal new distance (closest to home)
        best = min(straight, key=lambda m: (m['score'], -m['piece']))
        return best['move']
    else:
        best = min(candidates, key=lambda m: (m['score'], -m['piece']))
        return best['move']
