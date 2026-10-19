
from typing import List, Tuple

def policy(state: dict) -> str:
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = int(state['my_bar'])
    opp_bar = int(state['opp_bar'])
    my_off = int(state['my_off'])
    opp_off = int(state['opp_off'])
    dice = list(state['dice'])

    # No dice / no move case
    if len(dice) == 0:
        return "H:P,P"

    # Normalize dice into low/high for action encoding.
    if len(dice) == 1:
        low = high = dice[0]
    else:
        low, high = sorted(dice)

    # ---------- Helpers ----------
    def all_in_home(pts: List[int], bar: int) -> bool:
        if bar > 0:
            return False
        return sum(pts[6:]) == 0

    def can_bear_off_from(pts: List[int], bar: int, src: int, die: int) -> bool:
        if bar > 0 or pts[src] <= 0:
            return False
        if not all_in_home(pts, bar):
            return False
        dest = src - die
        if dest == -1:
            return True
        if dest < -1:
            # Oversized die: only legal if no checker on higher points than src
            for j in range(src + 1, 6):
                if pts[j] > 0:
                    return False
            return True
        return False

    def legal_sources(pts: List[int], opp: List[int], bar: int, die: int) -> List[str]:
        out = []
        if bar > 0:
            dest = 24 - die
            if 0 <= dest <= 23 and opp[dest] < 2:
                out.append("B")
            return out

        home_ready = all_in_home(pts, bar)
        for src in range(24):
            if pts[src] <= 0:
                continue
            dest = src - die
            if 0 <= dest <= 23:
                if opp[dest] < 2:
                    out.append(f"A{src}")
            else:
                if home_ready and can_bear_off_from(pts, bar, src, die):
                    out.append(f"A{src}")
        return out

    def apply_move(pts: List[int], opp: List[int], bar: int, opp_bar_local: int, off: int,
                   src_token: str, die: int):
        pts2 = pts[:]
        opp2 = opp[:]
        bar2 = bar
        opp_bar2 = opp_bar_local
        off2 = off

        if src_token == "P":
            return pts2, opp2, bar2, opp_bar2, off2, False

        if src_token == "B":
            if bar2 <= 0:
                return pts2, opp2, bar2, opp_bar2, off2, False
            src = None
            dest = 24 - die
            if not (0 <= dest <= 23):
                return pts2, opp2, bar2, opp_bar2, off2, False
            if opp2[dest] >= 2:
                return pts2, opp2, bar2, opp_bar2, off2, False
            bar2 -= 1
            if opp2[dest] == 1:
                opp2[dest] = 0
                opp_bar2 += 1
            pts2[dest] += 1
            return pts2, opp2, bar2, opp_bar2, off2, True

        if not src_token.startswith("A"):
            return pts2, opp2, bar2, opp_bar2, off2, False
        try:
            src = int(src_token[1:])
        except Exception:
            return pts2, opp2, bar2, opp_bar2, off2, False
        if not (0 <= src <= 23) or pts2[src] <= 0 or bar2 > 0:
            return pts2, opp2, bar2, opp_bar2, off2, False

        dest = src - die
        pts2[src] -= 1

        if 0 <= dest <= 23:
            if opp2[dest] >= 2:
                return pts[:], opp[:], bar, opp_bar_local, off, False
            if opp2[dest] == 1:
                opp2[dest] = 0
                opp_bar2 += 1
            pts2[dest] += 1
            return pts2, opp2, bar2, opp_bar2, off2, True

        # bear off
        if can_bear_off_from(pts, bar, src, die):
            off2 += 1
            return pts2, opp2, bar2, opp_bar2, off2, True

        return pts[:], opp[:], bar, opp_bar_local, off, False

    def pip_count(pts: List[int], bar: int, off: int) -> int:
        # Distance to bear off for our orientation.
        total = bar * 25
        for i, n in enumerate(pts):
            if n:
                total += n * (i + 1)
        return total

    def count_blots(pts: List[int]) -> int:
        return sum(1 for x in pts if x == 1)

    def count_points(pts: List[int]) -> int:
        return sum(1 for x in pts if x >= 2)

    def longest_prime(pts: List[int]) -> int:
        best = cur = 0
        for i in range(24):
            if pts[i] >= 2:
                cur += 1
                if cur > best:
                    best = cur
            else:
                cur = 0
        return best

    def blot_exposure(pts: List[int], opp: List[int], my_bar_local: int) -> int:
        # Approximate number of direct shots on our blots from opponent side.
        # Since opponent moves opposite direction, an opponent checker at j can hit our blot at i
        # if i-j in [1..6].
        if my_bar_local > 0:
            # being on bar is bad already, no need here
            pass
        exp = 0
        for i in range(24):
            if pts[i] == 1:
                shots = 0
                for d in range(1, 7):
                    j = i - d
                    if 0 <= j <= 23 and opp[j] > 0:
                        shots += opp[j]
                exp += shots
        return exp

    def entry_block_points(pts: List[int]) -> int:
        # Our made points in opponent's entry zone (points 18..23 for us)
        return sum(1 for i in range(18, 24) if pts[i] >= 2)

    def race_mode(pts: List[int], opp: List[int], my_bar_local: int, opp_bar_local: int) -> bool:
        if my_bar_local > 0 or opp_bar_local > 0:
            return False
        my_farthest = max((i for i, n in enumerate(pts) if n > 0), default=-1)
        opp_nearest = min((i for i, n in enumerate(opp) if n > 0), default=24)
        # No contact if all our checkers are behind all opponent checkers in our orientation.
        return my_farthest < opp_nearest

    def evaluate(pts: List[int], opp: List[int], bar: int, opp_bar_local: int, off: int, opp_off_local: int) -> float:
        my_pip = pip_count(pts, bar, off)
        opp_pip = pip_count(opp, opp_bar_local, opp_off_local)

        score = 0.0

        # Strong terminal pressure
        score += 120.0 * off
        score -= 115.0 * opp_off_local

        # Bar and race
        score -= 90.0 * bar
        score += 75.0 * opp_bar_local
        score += 1.25 * (opp_pip - my_pip)

        # Structure
        my_blots = count_blots(pts)
        opp_blots = count_blots(opp)
        my_points = count_points(pts)
        opp_points = count_points(opp)

        score -= 14.0 * my_blots
        score += 10.0 * opp_blots
        score += 8.0 * my_points
        score -= 6.0 * opp_points

        # Valuable made points
        for i in range(6):      # home board
            if pts[i] >= 2:
                score += 9.0
            if opp[i] >= 2:
                score -= 4.0
        for i in range(6, 12):  # outer board
            if pts[i] >= 2:
                score += 4.0

        # Entry blocking when opponent on bar
        if opp_bar_local > 0:
            score += 18.0 * entry_block_points(pts)

        # Prime value
        score += 7.0 * longest_prime(pts)
        score -= 4.0 * longest_prime(opp)

        # Vulnerability
        score -= 3.0 * blot_exposure(pts, opp, bar)

        # Encourage safe bear-off / race play in pure race
        if race_mode(pts, opp, bar, opp_bar_local):
            score += 0.9 * (opp_pip - my_pip)
            score -= 8.0 * my_blots
            score += 2.0 * off

        return score

    # ---------- Enumerate legal actions ----------
    actions = []

    # one die case
    if len(dice) == 1:
        die = dice[0]
        srcs = legal_sources(my_pts, opp_pts, my_bar, die)
        if not srcs:
            actions.append(("H:P,P", my_pts, opp_pts, my_bar, opp_bar, my_off))
        else:
            for s in srcs:
                pts2, opp2, bar2, oppb2, off2, ok = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, s, die)
                if ok:
                    actions.append((f"H:{s},P", pts2, opp2, bar2, oppb2, off2))
    else:
        # Try both orders and enforce max-play / both-dice logic by construction.
        order_specs = [
            ("H", high, low),   # first move uses high die
            ("L", low, high),   # first move uses low die
        ]

        legal_two = []
        legal_one = []

        for order_char, d1, d2 in order_specs:
            srcs1 = legal_sources(my_pts, opp_pts, my_bar, d1)
            if not srcs1:
                continue
            for s1 in srcs1:
                pts1, opp1, bar1, oppb1, off1, ok1 = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, s1, d1)
                if not ok1:
                    continue
                srcs2 = legal_sources(pts1, opp1, bar1, d2)
                if srcs2:
                    for s2 in srcs2:
                        pts2, opp2, bar2, oppb2, off2, ok2 = apply_move(pts1, opp1, bar1, oppb1, off1, s2, d2)
                        if ok2:
                            legal_two.append((f"{order_char}:{s1},{s2}", pts2, opp2, bar2, oppb2, off2))
                else:
                    legal_one.append((order_char, s1, pts1, opp1, bar1, oppb1, off1))

        if legal_two:
            actions = legal_two
        else:
            # If only one die can be played, higher die must be played when possible.
            high_srcs = legal_sources(my_pts, opp_pts, my_bar, high)
            if high_srcs:
                for s in high_srcs:
                    pts2, opp2, bar2, oppb2, off2, ok = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, s, high)
                    if ok:
                        actions.append((f"H:{s},P", pts2, opp2, bar2, oppb2, off2))
            else:
                low_srcs = legal_sources(my_pts, opp_pts, my_bar, low)
                if low_srcs:
                    for s in low_srcs:
                        pts2, opp2, bar2, oppb2, off2, ok = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, s, low)
                        if ok:
                            actions.append((f"L:{s},P", pts2, opp2, bar2, oppb2, off2))
                else:
                    actions.append(("H:P,P", my_pts, opp_pts, my_bar, opp_bar, my_off))

    # ---------- Choose best ----------
    best_action = None
    best_score = -10**18

    for act, pts2, opp2, bar2, oppb2, off2 in actions:
        sc = evaluate(pts2, opp2, bar2, oppb2, off2, opp_off)
        # Tiny tie-breakers: prefer using both dice, then higher-first, then lexical stability.
        if len(dice) == 2:
            if not act.endswith(",P"):
                sc += 0.01
            if act.startswith("H:"):
                sc += 0.001
        if sc > best_score or (sc == best_score and (best_action is None or act < best_action)):
            best_score = sc
            best_action = act

    return best_action if best_action is not None else "H:P,P"
