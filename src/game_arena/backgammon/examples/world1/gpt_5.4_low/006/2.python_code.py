
from typing import List, Tuple, Dict

def policy(state: dict) -> str:
    my_pts = list(state["my_pts"])
    opp_pts = list(state["opp_pts"])
    my_bar = int(state["my_bar"])
    opp_bar = int(state["opp_bar"])
    my_off = int(state["my_off"])
    opp_off = int(state["opp_off"])
    dice = list(state["dice"])

    # No dice => no move
    if not dice:
        return "H:P,P"

    def clone_pos(pos):
        return {
            "my_pts": pos["my_pts"][:],
            "opp_pts": pos["opp_pts"][:],
            "my_bar": pos["my_bar"],
            "opp_bar": pos["opp_bar"],
            "my_off": pos["my_off"],
            "opp_off": pos["opp_off"],
        }

    def all_in_home(pos) -> bool:
        if pos["my_bar"] > 0:
            return False
        # All remaining on board must be in points 0..5
        return sum(pos["my_pts"][6:]) == 0

    def apply_move(pos, src, die):
        newp = clone_pos(pos)
        if src == "B":
            newp["my_bar"] -= 1
            dest = 24 - die
        else:
            p = src
            newp["my_pts"][p] -= 1
            dest = p - die

        if dest >= 0:
            if newp["opp_pts"][dest] == 1:
                newp["opp_pts"][dest] = 0
                newp["opp_bar"] += 1
            newp["my_pts"][dest] += 1
        else:
            newp["my_off"] += 1
        return newp

    def legal_single_moves(pos, die):
        moves = []

        # Must enter from bar first
        if pos["my_bar"] > 0:
            dest = 24 - die
            if 0 <= dest <= 23 and pos["opp_pts"][dest] < 2:
                moves.append(("B", apply_move(pos, "B", die)))
            return moves

        can_off = all_in_home(pos)

        for p in range(24):
            if pos["my_pts"][p] <= 0:
                continue

            dest = p - die
            if dest >= 0:
                if pos["opp_pts"][dest] < 2:
                    moves.append((p, apply_move(pos, p, die)))
            else:
                if not can_off:
                    continue
                # Exact bear off
                if die == p + 1:
                    moves.append((p, apply_move(pos, p, die)))
                # Oversize bear off allowed only from highest occupied point
                elif die > p + 1 and sum(pos["my_pts"][p + 1:6]) == 0:
                    moves.append((p, apply_move(pos, p, die)))
        return moves

    def generate_for_order(start_pos, order_char, dice_order):
        # Returns list of (action_string, final_pos, used_count, first_die_used)
        results = []

        def rec(pos, idx, srcs):
            if idx >= len(dice_order):
                # pad to two moves
                padded = srcs + ["P"] * (2 - len(srcs))
                action = f"{order_char}:{padded[0]},{padded[1]}"
                first_die = dice_order[0] if srcs else None
                results.append((action, pos, len(srcs), first_die))
                return

            die = dice_order[idx]
            moves = legal_single_moves(pos, die)

            if not moves:
                # Stop immediately; remaining moves are passes
                padded = srcs + ["P"] * (2 - len(srcs))
                action = f"{order_char}:{padded[0]},{padded[1]}"
                first_die = dice_order[0] if srcs else None
                results.append((action, pos, len(srcs), first_die))
                return

            for src, newp in moves:
                token = "B" if src == "B" else f"A{src}"
                rec(newp, idx + 1, srcs + [token])

        rec(start_pos, 0, [])
        return results

    start_pos = {
        "my_pts": my_pts,
        "opp_pts": opp_pts,
        "my_bar": my_bar,
        "opp_bar": opp_bar,
        "my_off": my_off,
        "opp_off": opp_off,
    }

    # Build candidate actions
    candidates = []

    if len(dice) == 1:
        d = dice[0]
        order_char = "H"
        candidates.extend(generate_for_order(start_pos, order_char, [d]))
    else:
        d1, d2 = dice[0], dice[1]
        hi = max(d1, d2)
        lo = min(d1, d2)

        # Even if equal, just use H order once
        candidates.extend(generate_for_order(start_pos, "H", [hi, lo]))
        if lo != hi:
            candidates.extend(generate_for_order(start_pos, "L", [lo, hi]))

    if not candidates:
        return "H:P,P"

    # Enforce "play both if possible"
    max_used = max(c[2] for c in candidates)
    candidates = [c for c in candidates if c[2] == max_used]

    # Enforce "if only one die can be played, must play higher when possible"
    if len(dice) == 2 and max_used == 1 and dice[0] != dice[1]:
        hi = max(dice)
        if any(c[3] == hi for c in candidates):
            candidates = [c for c in candidates if c[3] == hi]

    def pip_count(pos):
        # Distance to bear off: point i needs i+1 pips; bar approximated as 25
        return pos["my_bar"] * 25 + sum((i + 1) * n for i, n in enumerate(pos["my_pts"]))

    def evaluate(pos):
        score = 0.0

        # Strong objectives
        score += 120.0 * pos["my_off"]
        score -= 55.0 * pos["my_bar"]
        score += 25.0 * pos["opp_bar"]

        # Race
        score -= 1.2 * pip_count(pos)

        # Structure: made points and primes
        made = [1 if pos["my_pts"][i] >= 2 else 0 for i in range(24)]
        for i in range(24):
            if made[i]:
                score += 7.0
                if 0 <= i <= 5:
                    score += 3.0   # home board points
                if 18 <= i <= 23:
                    score += 1.5   # advanced anchors
            elif pos["my_pts"][i] == 1:
                # Blot penalty
                score -= 6.0
                if 6 <= i <= 17:
                    score -= 2.0

            # Slight penalty for huge stacks
            if pos["my_pts"][i] > 4:
                score -= 0.8 * (pos["my_pts"][i] - 4)

        # Consecutive made points are valuable
        for i in range(23):
            if made[i] and made[i + 1]:
                score += 4.0

        # Prefer bringing checkers home in race/contact-light situations too
        home_count = sum(pos["my_pts"][0:6])
        score += 1.0 * home_count

        return score

    # Pick best evaluated legal action, deterministic tiebreak by action string
    best = None
    best_key = None
    for action, pos, used, first_die in candidates:
        val = evaluate(pos)
        key = (val, action)
        if best is None or key > best_key:
            best = action
            best_key = key

    return best if best is not None else "H:P,P"
