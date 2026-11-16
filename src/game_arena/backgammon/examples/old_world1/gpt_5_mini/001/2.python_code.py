
import math
from typing import List, Tuple

def policy(state: dict) -> str:
    """
    Return a move string "<ORDER>:<FROM1>,<FROM2>" for the given state.
    Assumptions:
      - Movement direction uses dest = start - die (i.e., moving from higher indices toward lower).
      - Bar entry for die d is dest = 24 - d.
      - Bearing off (dest < 0) only allowed if all checkers are in home (points 0..5).
    """
    my_pts: List[int] = state.get('my_pts', [0]*24)
    opp_pts: List[int] = state.get('opp_pts', [0]*24)
    my_bar: int = int(state.get('my_bar', 0))
    dice: List[int] = list(state.get('dice', []))

    # Helper functions
    def total_on_board() -> int:
        return sum(my_pts) + my_bar

    def all_in_home() -> bool:
        # home defined as points 0..5 under the "dest = start - d" convention
        return sum(my_pts[6:]) == 0

    def dest_from(start, d) -> int:
        if start == 'B':
            return 24 - d  # bar entry assumption
        else:
            return int(start) - d

    def start_has_checker(s) -> bool:
        if s == 'B':
            return my_bar > 0
        else:
            return my_pts[int(s)] > 0

    def dest_is_legal(start, d) -> Tuple[bool,int]:
        """Return (is_legal, dest_index_or_negative_for_bearoff)."""
        dest = dest_from(start, d)
        if dest >= 0 and dest <= 23:
            # destination occupied by 2+ opponent checkers -> illegal
            if opp_pts[dest] >= 2:
                return (False, dest)
            else:
                return (True, dest)
        else:
            # dest < 0 -> potential bear off. Only allow if all checkers in home.
            if dest < 0 and all_in_home():
                return (True, dest)
            else:
                return (False, dest)

    # If no dice, pass
    if not dice:
        return "H:P,P"

    # Prepare dice values and identify high/low
    if len(dice) == 1:
        high_die = dice[0]
        low_die = dice[0]
    else:
        a, b = dice[0], dice[1]
        if a >= b:
            high_die, low_die = a, b
        else:
            high_die, low_die = b, a

    dice_orderings = [('H', high_die, low_die), ('L', low_die, high_die)]

    # Build playable start sets for each die value (under our assumed mapping)
    def playable_starts_for_die(d: int) -> List[str]:
        starts = []
        # bar
        if my_bar > 0:
            ok, dest = dest_is_legal('B', d)
            if ok:
                starts.append('B')
        # board points
        for i in range(24):
            if my_pts[i] <= 0:
                continue
            ok, dest = dest_is_legal(str(i), d)
            if ok:
                starts.append(str(i))
        return starts

    plays_high = playable_starts_for_die(high_die)
    plays_low = playable_starts_for_die(low_die)

    # Score function prefers hits (opp_pts[dest] == 1) then moving from higher indices
    def score_move(start: str, die: int) -> float:
        if start == 'P':
            return -1000.0
        ok, dest = dest_is_legal(start, die)
        if not ok:
            return -1000.0
        # hitting
        hit_score = 0
        if isinstance(dest, int) and 0 <= dest <= 23:
            if opp_pts[dest] == 1:
                hit_score = 100.0
        base_pos = 0.0
        if start == 'B':
            # approximate by favoring bar entries as significant
            base_pos = 12.0
        else:
            base_pos = float(int(start))
        return hit_score + base_pos / 24.0

    # If neither die has any playable starts -> pass
    if not plays_high and not plays_low:
        return "H:P,P"

    # If only one die value present (single die) then second move must be P.
    single_die_mode = (len(dice) == 1)

    # Try both orders and pick best legal combination
    best_action = None
    best_score = -1e9

    for order_char, first_die, second_die in dice_orderings:
        # For bar rule: if I have bar pieces and any bar-play is possible for either die,
        # we must ensure the first die in this order is capable of playing a bar entry.
        bar_needed = (my_bar > 0) and (('B' in plays_high) or ('B' in plays_low))
        # Determine playable sets for dice in this order
        first_plays = plays_high if first_die == high_die and not single_die_mode else plays_low if first_die == low_die and not single_die_mode else plays_high if single_die_mode else plays_high
        # (above handling is to cover single die case; simpler approach below)
        # Recompute properly:
        if first_die == high_die:
            first_plays = plays_high
        else:
            first_plays = plays_low
        if second_die == high_die:
            second_plays = plays_high
        else:
            second_plays = plays_low

        # If single die mode, second must be P; allow only first moves
        if single_die_mode:
            # if no playable starts for the only die, we already returned pass earlier
            candidates_first = first_plays[:] if first_plays else ['P']
            for s1 in candidates_first:
                # enforce bar-first if needed
                if bar_needed and s1 != 'B':
                    continue
                if s1 == 'P':
                    sc = -1000.0
                else:
                    sc = score_move(s1, first_die)
                if sc > best_score:
                    best_score = sc
                    best_action = f"{order_char}:{'A'+s1 if s1!='B' and s1!='P' else ('B' if s1=='B' else 'P')},P"
            continue

        # multi-die mode (2 dice)
        # If first_plays empty, we will allow 'P' only if no plays exist for that die
        first_candidates = first_plays[:] if first_plays else ['P']
        second_candidates = second_plays[:] if second_plays else ['P']

        # Enforce bar-first: if bar_needed then first must be B (and must be in first_candidates)
        if bar_needed:
            if 'B' not in first_candidates:
                # can't use this ordering (bar entry must be played first)
                continue
            # restrict first candidates to B only
            first_candidates = ['B']

        for s1 in first_candidates:
            for s2 in second_candidates:
                # Avoid selecting 'P' for a die while there is a legal play for that die
                if s1 == 'P' and first_plays:
                    continue
                if s2 == 'P' and second_plays:
                    continue
                # Do not attempt to move the same single checker twice unless there is at least two there
                if s1 not in ('P','B') and s2 not in ('P','B') and s1 == s2:
                    if my_pts[int(s1)] < 2:
                        continue
                if s1 == 'B' and s2 == 'B':
                    if my_bar < 2:
                        # can't enter two from bar if only one on bar
                        continue

                # Now calculate score: sum of individual move scores (taking dests into account)
                sc1 = score_move(s1, first_die) if s1 != 'P' else -1000.0
                sc2 = score_move(s2, second_die) if s2 != 'P' else -1000.0
                # If either is illegal under dest_is_legal, skip
                if s1 != 'P' and not dest_is_legal(s1, first_die)[0]:
                    continue
                if s2 != 'P' and not dest_is_legal(s2, second_die)[0]:
                    continue

                sc = sc1 + sc2
                # prefer using both dice (avoid P) slightly
                if s1 != 'P' and s2 != 'P':
                    sc += 1.0

                if sc > best_score:
                    best_score = sc
                    # Format starts: A<idx> for indices, B for bar, P for pass
                    def fmt(s):
                        if s == 'P':
                            return 'P'
                        if s == 'B':
                            return 'B'
                        return 'A' + str(int(s))
                    best_action = f"{order_char}:{fmt(s1)},{fmt(s2)}"

    # Fallbacks if nothing found (shouldn't happen because we handled pass earlier)
    if best_action is None:
        return "H:P,P"

    return best_action
