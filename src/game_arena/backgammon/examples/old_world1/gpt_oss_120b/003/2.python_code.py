
import copy
from typing import List, Tuple, Optional, Dict

def policy(state: dict) -> str:
    """
    Return a legal backgammon move string for the given state.
    """
    my_pts: List[int] = state["my_pts"]
    opp_pts: List[int] = state["opp_pts"]
    my_bar: int = state["my_bar"]
    opp_bar: int = state["opp_bar"]
    my_off: int = state["my_off"]
    dice: List[int] = state["dice"]

    # Helper: are all my checkers already inside the home board (points 0‑5)?
    def all_in_home(my_pts_local: List[int]) -> bool:
        return sum(my_pts_local[6:]) == 0

    # Helper: given a source token ('B' or integer point) and a die,
    # decide whether the move is legal in the *current* board.
    def legal_sources(my_pts_local: List[int],
                      opp_pts_local: List[int],
                      my_bar_local: int,
                      die: int) -> List[str]:
        sources = []

        # If we have a checker on the bar we must move it (and cannot move any other checker).
        if my_bar_local > 0:
            dest = 24 - die  # entry point from the bar
            if 0 <= dest <= 23 and opp_pts_local[dest] <= 1:
                sources.append("B")
            return sources  # bar moves are exclusive
        # Otherwise consider normal points.
        for i in range(23, -1, -1):          # start from the farthest point
            if my_pts_local[i] == 0:
                continue
            dest = i - die
            if dest >= 0:
                if opp_pts_local[dest] <= 1:   # empty or blot
                    sources.append(f"A{i}")
            else:  # bearing off
                if all_in_home(my_pts_local) and i <= 5:
                    # simple bearing‑off legality (exact or over‑roll)
                    sources.append(f"A{i}")
        return sources

    # Apply a move to a *copy* of the state and return the new components.
    def apply_move(my_pts_local: List[int],
                   opp_pts_local: List[int],
                   my_bar_local: int,
                   opp_bar_local: int,
                   my_off_local: int,
                   src_token: str,
                   die: int) -> Tuple[List[int], List[int], int, int, int]:
        my_pts_new = my_pts_local[:]
        opp_pts_new = opp_pts_local[:]
        my_bar_new = my_bar_local
        opp_bar_new = opp_bar_local
        my_off_new = my_off_local

        # Determine source index
        if src_token == "B":
            src_is_bar = True
        else:
            src_is_bar = False
            src_idx = int(src_token[1:])  # strip the leading 'A'

        # Destination
        if src_is_bar:
            dest = 24 - die
            my_bar_new -= 1
        else:
            dest = src_idx - die
            my_pts_new[src_idx] -= 1

        # Bearing off
        if dest < 0:
            my_off_new += 1
            return my_pts_new, opp_pts_new, my_bar_new, opp_bar_new, my_off_new

        # Normal move / hit handling
        if opp_pts_new[dest] == 1:
            # hit opponent blot
            opp_pts_new[dest] = 0
            opp_bar_new += 1
        # else opp_pts_new[dest] is 0 (empty) – nothing to do
        my_pts_new[dest] += 1
        return my_pts_new, opp_pts_new, my_bar_new, opp_bar_new, my_off_new

    # Try to find a sequence that uses both dice.
    def find_two_moves(first_die: int, second_die: int) -> Optional[Tuple[str, str, str]]:
        # order char depends on which die we treat as the first one
        order_char = "H" if first_die == max(dice) else "L"
        # generate possible first moves
        first_sources = legal_sources(my_pts, opp_pts, my_bar, first_die)
        for src1 in first_sources:
            # simulate first move
            (my_pts1, opp_pts1,
             my_bar1, opp_bar1,
             my_off1) = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off,
                                   src1, first_die)
            # generate possible second moves in the resulting position
            second_sources = legal_sources(my_pts1, opp_pts1, my_bar1, second_die)
            for src2 in second_sources:
                return order_char, src1, src2
        return None

    # Main decision logic
    if len(dice) == 1:
        die = dice[0]
        sources = legal_sources(my_pts, opp_pts, my_bar, die)
        if sources:
            return f"H:{sources[0]},P"
        else:
            return "H:P,P"
    else:
        # Two dice – possibly equal (double)
        d1, d2 = dice
        higher = max(d1, d2)
        lower = min(d1, d2)

        # 1) try higher‑first then lower‑first
        attempt = find_two_moves(higher, lower)
        if attempt is None:
            attempt = find_two_moves(lower, higher)

        if attempt:
            order_char, src1, src2 = attempt
            return f"{order_char}:{src1},{src2}"

        # 2) unable to play both dice – try to play a single die
        #    higher die first
        sources_high = legal_sources(my_pts, opp_pts, my_bar, higher)
        if sources_high:
            return f"H:{sources_high[0]},P"
        #    then lower die
        sources_low = legal_sources(my_pts, opp_pts, my_bar, lower)
        if sources_low:
            return f"L:{sources_low[0]},P"

        # 3) no move at all
        return "H:P,P"
