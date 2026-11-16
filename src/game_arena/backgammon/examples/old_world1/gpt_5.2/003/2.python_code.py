
import random
from typing import List, Tuple, Optional, Dict, Any


def policy(state: dict) -> str:
    """
    Backgammon policy:
    - Enumerate all legal actions for the current dice (both H and L orders when applicable).
    - Enforce mandatory usage: play both dice if possible; else play one, preferring higher die if only one can be played.
    - Evaluate resulting positions with a heuristic and choose the best action.
    Always returns a legal move string: "<ORDER>:<FROM1>,<FROM2>".
    """

    # ---------- Helpers: state access ----------
    my_pts0 = list(state.get("my_pts", [0] * 24))
    opp_pts0 = list(state.get("opp_pts", [0] * 24))
    my_bar0 = int(state.get("my_bar", 0))
    opp_bar0 = int(state.get("opp_bar", 0))
    my_off0 = int(state.get("my_off", 0))
    opp_off0 = int(state.get("opp_off", 0))
    dice = list(state.get("dice", []))

    # Dice handling: engine may provide 0, 1, or 2 dice.
    if len(dice) == 0:
        return "H:P,P"
    if len(dice) == 1:
        # Only one die: treat as a single-step turn; second move must be P.
        d_high = d_low = int(dice[0])
        orders = [("H", [d_high, None])]  # second die absent
    else:
        a, b = int(dice[0]), int(dice[1])
        d_high, d_low = (a, b) if a >= b else (b, a)
        if d_high == d_low:
            orders = [("H", [d_high, d_low])]
        else:
            orders = [("H", [d_high, d_low]), ("L", [d_low, d_high])]

    # ---------- Core move legality/simulation ----------
    def in_home_only(my_pts: List[int], my_bar: int) -> bool:
        if my_bar > 0:
            return False
        return sum(my_pts[6:]) == 0

    def entry_point_for_die(d: int) -> int:
        # We move 23 -> 0; enter from bar onto 24-d (die 1 -> 23, die 6 -> 18)
        return 24 - d

    def is_open(opp_pts: List[int], dest: int) -> bool:
        return opp_pts[dest] < 2

    def token_point(tok: str) -> Optional[int]:
        if tok == "B" or tok == "P":
            return None
        if tok.startswith("A"):
            return int(tok[1:])
        return None

    def point_token(i: int) -> str:
        return f"A{i}"

    def legal_sources_for_die(
        my_pts: List[int],
        opp_pts: List[int],
        my_bar: int,
        d: int,
    ) -> List[str]:
        """
        Return a list of FROM tokens ('B' or 'A#') that are legal to play with die d
        given current board, including bearing off rules.
        """
        if d is None:
            return []

        # Must enter from bar first if any on bar.
        if my_bar > 0:
            dest = entry_point_for_die(d)
            if is_open(opp_pts, dest):
                return ["B"]
            return []

        sources: List[str] = []
        can_bear = in_home_only(my_pts, my_bar)

        for i in range(24):
            if my_pts[i] <= 0:
                continue
            dest = i - d
            if dest >= 0:
                if is_open(opp_pts, dest):
                    sources.append(point_token(i))
            else:
                # Potential bear off
                if not can_bear:
                    continue
                if i <= 5:
                    # Exact bear off: i == d-1
                    if i == d - 1:
                        sources.append(point_token(i))
                    else:
                        # Overshoot allowed only from highest occupied point
                        # when no checkers on higher points (i+1..5).
                        if d > i + 1 and sum(my_pts[i + 1 : 6]) == 0:
                            sources.append(point_token(i))
        return sources

    def apply_single_move(
        my_pts: List[int],
        opp_pts: List[int],
        my_bar: int,
        opp_bar: int,
        my_off: int,
        d: int,
        from_tok: str,
    ) -> Tuple[List[int], List[int], int, int, int]:
        """
        Apply one move (die d from from_tok) to copies of arrays.
        Assumes legality.
        """
        my_pts = my_pts[:]  # copy
        opp_pts = opp_pts[:]

        if d is None or from_tok == "P":
            return my_pts, opp_pts, my_bar, opp_bar, my_off

        if from_tok == "B":
            # Enter from bar
            dest = entry_point_for_die(d)
            my_bar -= 1
            # Hit if exactly one opponent checker
            if opp_pts[dest] == 1:
                opp_pts[dest] -= 1
                opp_bar += 1
            my_pts[dest] += 1
            return my_pts, opp_pts, my_bar, opp_bar, my_off

        i = token_point(from_tok)
        assert i is not None
        my_pts[i] -= 1
        dest = i - d
        if dest >= 0:
            if opp_pts[dest] == 1:
                opp_pts[dest] -= 1
                opp_bar += 1
            my_pts[dest] += 1
        else:
            # Bear off
            my_off += 1
        return my_pts, opp_pts, my_bar, opp_bar, my_off

    def generate_actions_for_order(order_char: str, dice_seq: List[Optional[int]]) -> List[Tuple[str, str, str]]:
        """
        Generate all (order, from1, from2) actions for a given dice order.
        If a die cannot be played at its step, that step becomes 'P'.
        """
        d1 = dice_seq[0]
        d2 = dice_seq[1] if len(dice_seq) > 1 else None

        actions: List[Tuple[str, str, str]] = []

        # Step 1
        srcs1 = legal_sources_for_die(my_pts0, opp_pts0, my_bar0, d1) if d1 is not None else []
        if not srcs1:
            srcs1 = ["P"]

        for from1 in srcs1:
            my1, opp1, bar1, oppbar1, off1 = apply_single_move(
                my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, d1, from1
            )

            # Step 2
            if d2 is None:
                actions.append((order_char, from1, "P"))
                continue

            srcs2 = legal_sources_for_die(my1, opp1, bar1, d2)
            if not srcs2:
                srcs2 = ["P"]
            for from2 in srcs2:
                actions.append((order_char, from1, from2))

        return actions

    def dice_used_in_action(action: Tuple[str, str, str], d_high: int, d_low: int) -> List[int]:
        order_char, f1, f2 = action
        used = []
        if len(dice) == 1:
            if f1 != "P":
                used.append(d_high)
            return used

        if d_high == d_low:
            if f1 != "P":
                used.append(d_high)
            if f2 != "P":
                used.append(d_high)
            return used

        if order_char == "H":
            if f1 != "P":
                used.append(d_high)
            if f2 != "P":
                used.append(d_low)
        else:  # "L"
            if f1 != "P":
                used.append(d_low)
            if f2 != "P":
                used.append(d_high)
        return used

    def apply_action(action: Tuple[str, str, str]) -> Tuple[List[int], List[int], int, int, int]:
        order_char, f1, f2 = action
        if len(dice) == 1:
            d1 = d_high
            d2 = None
        else:
            if d_high == d_low:
                d1, d2 = d_high, d_low
            else:
                d1, d2 = (d_high, d_low) if order_char == "H" else (d_low, d_high)

        my1, opp1, bar1, oppbar1, off1 = apply_single_move(
            my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, d1, f1
        )
        my2, opp2, bar2, oppbar2, off2 = apply_single_move(
            my1, opp1, bar1, oppbar1, off1, d2, f2
        )
        return my2, opp2, bar2, oppbar2, off2

    # ---------- Generate all actions ----------
    all_actions: List[Tuple[str, str, str]] = []
    for oc, dseq in orders:
        all_actions.extend(generate_actions_for_order(oc, dseq))

    if not all_actions:
        return "H:P,P"

    # ---------- Enforce mandatory dice usage ----------
    def action_used_count(a: Tuple[str, str, str]) -> int:
        return (1 if a[1] != "P" else 0) + (1 if a[2] != "P" else 0)

    max_used = max(action_used_count(a) for a in all_actions)
    cand = [a for a in all_actions if action_used_count(a) == max_used]

    # If only one move can be played, must play higher die when possible.
    if max_used == 1 and len(dice) == 2 and d_high != d_low:
        # Is there any candidate that plays the high die?
        def uses_high(a: Tuple[str, str, str]) -> bool:
            used = dice_used_in_action(a, d_high, d_low)
            return (d_high in used)

        if any(uses_high(a) for a in cand):
            cand = [a for a in cand if uses_high(a)]

    # If still empty (shouldn't happen), pass.
    if not cand:
        return "H:P,P"

    # ---------- Evaluation heuristic ----------
    def pip_count_my(my_pts: List[int], my_bar: int) -> int:
        # Distance to bear off: point i contributes i+1 pips (since bear off beyond point 0)
        return sum((i + 1) * my_pts[i] for i in range(24)) + 25 * my_bar

    def pip_count_opp(opp_pts: List[int], opp_bar: int) -> int:
        # Opponent moves 0 -> 23, so distance is (24 - i)
        return sum((24 - i) * opp_pts[i] for i in range(24)) + 25 * opp_bar

    def longest_prime(my_pts: List[int]) -> int:
        best = cur = 0
        for i in range(24):
            if my_pts[i] >= 2:
                cur += 1
                if cur > best:
                    best = cur
            else:
                cur = 0
        return best

    def blot_vulnerability(my_pts: List[int], opp_pts: List[int]) -> float:
        """
        Simple shot estimate: a blot at j is "directly hittable" if opponent has a checker
        within 1..6 points behind it: at j-d (d=1..6). (Ignores opponent bar entries and combos.)
        """
        vuln = 0.0
        for j in range(24):
            if my_pts[j] == 1:
                # higher penalty for blots further from home (typically more valuable to keep safe)
                base = 1.0 + (j / 23.0)
                for d in range(1, 7):
                    k = j - d
                    if k >= 0 and opp_pts[k] > 0:
                        vuln += base
                        break
        return vuln

    def eval_position(
        my_pts: List[int],
        opp_pts: List[int],
        my_bar: int,
        opp_bar: int,
        my_off: int,
        opp_off: int,
        old_my_off: int,
        old_opp_bar: int,
        old_my_bar: int,
    ) -> float:
        score = 0.0

        # Winning progress
        score += 120.0 * (my_off - opp_off)

        # Race component
        my_pip = pip_count_my(my_pts, my_bar)
        opp_pip = pip_count_opp(opp_pts, opp_bar)
        score += 0.6 * (opp_pip - my_pip)

        # Immediate tactical results
        score += 10.0 * (opp_bar - old_opp_bar)   # hitting is strong
        score -= 12.0 * (my_bar - old_my_bar)     # shouldn't increase on our turn

        # Bearing off preference when available
        if in_home_only(my_pts0, my_bar0):
            score += 25.0 * (my_off - old_my_off)

        # Structure: made points and home-board blocks
        made_points = sum(1 for i in range(24) if my_pts[i] >= 2)
        home_blocks = sum(1 for i in range(6) if my_pts[i] >= 2)
        score += 1.8 * made_points
        score += 2.5 * home_blocks
        if opp_bar > 0:
            score += 4.0 * home_blocks  # closing board matters more if opponent is on bar

        # Prime building
        prime_len = longest_prime(my_pts)
        score += 2.0 * (prime_len ** 2)

        # Anchors in opponent home (points 18..23)
        anchors = sum(1 for i in range(18, 24) if my_pts[i] >= 2)
        score += 3.0 * anchors

        # Blots and vulnerability
        blots = sum(1 for i in range(24) if my_pts[i] == 1)
        score -= 1.2 * blots
        score -= 2.2 * blot_vulnerability(my_pts, opp_pts)

        return score

    best_action = cand[0]
    best_score = -1e18

    # Deterministic but avoid pathological ties by stable secondary sorting
    for a in cand:
        my1, opp1, bar1, oppbar1, off1 = apply_action(a)
        sc = eval_position(
            my1, opp1, bar1, oppbar1, off1, opp_off0,
            old_my_off=my_off0,
            old_opp_bar=opp_bar0,
            old_my_bar=my_bar0,
        )

        # Tie-breakers: prefer actions that (a) hit, (b) bear off, (c) move from bar
        used = dice_used_in_action(a, d_high, d_low)
        hit_bonus = (oppbar1 - opp_bar0) * 0.01
        off_bonus = (off1 - my_off0) * 0.01
        bar_move_bonus = (1 if ("B" in a[1:] and my_bar0 > 0) else 0) * 0.005
        sc2 = sc + hit_bonus + off_bonus + bar_move_bonus

        if sc2 > best_score:
            best_score = sc2
            best_action = a

    order_char, f1, f2 = best_action
    return f"{order_char}:{f1},{f2}"
