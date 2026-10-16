
from typing import List, Tuple, Dict

# Backgammon policy:
# - Always returns a legal move string.
# - Generates all legal actions for the given dice and state.
# - Evaluates resulting positions with a heuristic and picks the best.


def policy(state: dict) -> str:
    my_pts = list(state["my_pts"])
    opp_pts = list(state["opp_pts"])
    my_bar = int(state["my_bar"])
    opp_bar = int(state["opp_bar"])
    my_off = int(state["my_off"])
    opp_off = int(state["opp_off"])
    dice = list(state["dice"])

    if len(dice) == 0:
        return "H:P,P"

    # Normalize to two dice slots for output protocol.
    if len(dice) == 1:
        d1 = d2 = dice[0]
    else:
        d1, d2 = dice[0], dice[1]

    # Determine higher/lower labels for output.
    if d1 >= d2:
        high_die, low_die = d1, d2
    else:
        high_die, low_die = d2, d1

    # Enumerate legal actions under engine rules for 0, 1, or 2 dice.
    actions = enumerate_actions(
        my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, dice
    )

    if not actions:
        return "H:P,P"

    # Score all candidate resulting states.
    best_score = None
    best_action = None
    for action in actions:
        score = evaluate_state(
            action["my_pts"],
            action["opp_pts"],
            action["my_bar"],
            action["opp_bar"],
            action["my_off"],
            action["opp_off"],
        )
        # Small preference for simpler canonical output when tied.
        score += tie_break_bonus(action["move_str"])
        if best_score is None or score > best_score:
            best_score = score
            best_action = action["move_str"]

    return best_action


def tie_break_bonus(move_str: str) -> float:
    # Prefer non-pass, then H on ties for determinism.
    bonus = 0.0
    if ":P,P" not in move_str:
        bonus += 0.001
    if move_str.startswith("H:"):
        bonus += 0.0001
    return bonus


def all_in_home(my_pts: List[int], my_bar: int) -> bool:
    if my_bar > 0:
        return False
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True


def legal_single_moves(
    my_pts: List[int],
    opp_pts: List[int],
    my_bar: int,
    my_off: int,
    die: int,
) -> List[Tuple[str, int, List[int], List[int], int, int, bool]]:
    """
    Returns list of legal single checker moves for this die.
    Each item: (from_token, from_index_or_-1, new_my_pts, new_opp_pts, new_my_bar, new_my_off, hit)
    from_token is 'B' or f'A{i}'.
    """
    moves = []

    # Must enter from bar first
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest <= 23 and opp_pts[dest] < 2:
            nmy = my_pts[:]
            nopp = opp_pts[:]
            nbar = my_bar - 1
            noff = my_off
            hit = False
            if nopp[dest] == 1:
                nopp[dest] = 0
                hit = True
            nmy[dest] += 1
            moves.append(("B", -1, nmy, nopp, nbar, noff, hit))
        return moves

    home = all_in_home(my_pts, my_bar)

    for src in range(24):
        if my_pts[src] <= 0:
            continue
        dest = src - die

        # Normal move on board
        if dest >= 0:
            if opp_pts[dest] >= 2:
                continue
            nmy = my_pts[:]
            nopp = opp_pts[:]
            nbar = my_bar
            noff = my_off
            nmy[src] -= 1
            hit = False
            if nopp[dest] == 1:
                nopp[dest] = 0
                hit = True
            nmy[dest] += 1
            moves.append((f"A{src}", src, nmy, nopp, nbar, noff, hit))
        else:
            # Bearing off
            if not home:
                continue
            exact = (src - die == -1)  # same as src + 1 == die
            if exact:
                nmy = my_pts[:]
                nopp = opp_pts[:]
                nbar = my_bar
                noff = my_off + 1
                nmy[src] -= 1
                moves.append((f"A{src}", src, nmy, nopp, nbar, noff, False))
            else:
                # Oversized die allowed only if no checker on higher points than src
                # "Higher points" for us are farther from bearing off => indices > src.
                if die > src + 1:
                    any_higher = False
                    for j in range(src + 1, 24):
                        if my_pts[j] > 0:
                            any_higher = True
                            break
                    if not any_higher:
                        nmy = my_pts[:]
                        nopp = opp_pts[:]
                        nbar = my_bar
                        noff = my_off + 1
                        nmy[src] -= 1
                        moves.append((f"A{src}", src, nmy, nopp, nbar, noff, False))

    return moves


def enumerate_actions(
    my_pts: List[int],
    opp_pts: List[int],
    my_bar: int,
    opp_bar: int,
    my_off: int,
    opp_off: int,
    dice: List[int],
) -> List[Dict]:
    """
    Enumerate legal actions according to:
      - if both dice can be played, must play both
      - if only one die can be played, must play higher die when possible
    Output action dicts include move_str and resulting state.
    """
    if len(dice) == 0:
        return [{
            "move_str": "H:P,P",
            "my_pts": my_pts[:],
            "opp_pts": opp_pts[:],
            "my_bar": my_bar,
            "opp_bar": opp_bar,
            "my_off": my_off,
            "opp_off": opp_off,
        }]

    if len(dice) == 1:
        die = dice[0]
        singles = legal_single_moves(my_pts, opp_pts, my_bar, my_off, die)
        if not singles:
            return [{
                "move_str": "H:P,P",
                "my_pts": my_pts[:],
                "opp_pts": opp_pts[:],
                "my_bar": my_bar,
                "opp_bar": opp_bar,
                "my_off": my_off,
                "opp_off": opp_off,
            }]
        acts = []
        for tok, _src, nmy, nopp, nbar, noff, _hit in singles:
            acts.append({
                "move_str": f"H:{tok},P",
                "my_pts": nmy,
                "opp_pts": nopp,
                "my_bar": nbar,
                "opp_bar": opp_bar + bar_increment(opp_pts, nopp),
                "my_off": noff,
                "opp_off": opp_off,
            })
        return acts

    d1, d2 = dice[0], dice[1]
    high_die = max(d1, d2)
    low_die = min(d1, d2)

    # Try both orders; output order tag indicates first move uses H or L.
    seqs = []
    # H first
    seqs.extend(enumerate_sequence(
        my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off,
        first_die=high_die, second_die=low_die, order_char="H"
    ))
    # L first
    seqs.extend(enumerate_sequence(
        my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off,
        first_die=low_die, second_die=high_die, order_char="L"
    ))

    # If any 2-move actions exist, only they are legal.
    two_move = [a for a in seqs if not a["move_str"].endswith(",P")]
    if two_move:
        # Deduplicate by move string/result
        return dedup_actions(two_move)

    # Otherwise only one die can be played. Must play higher die when possible.
    high_singles = legal_single_moves(my_pts, opp_pts, my_bar, my_off, high_die)
    low_singles = legal_single_moves(my_pts, opp_pts, my_bar, my_off, low_die)

    acts = []
    if high_singles:
        for tok, _src, nmy, nopp, nbar, noff, _hit in high_singles:
            acts.append({
                "move_str": f"H:{tok},P",
                "my_pts": nmy,
                "opp_pts": nopp,
                "my_bar": nbar,
                "opp_bar": opp_bar + bar_increment(opp_pts, nopp),
                "my_off": noff,
                "opp_off": opp_off,
            })
        return dedup_actions(acts)

    if low_singles:
        for tok, _src, nmy, nopp, nbar, noff, _hit in low_singles:
            acts.append({
                "move_str": f"L:{tok},P",
                "my_pts": nmy,
                "opp_pts": nopp,
                "my_bar": nbar,
                "opp_bar": opp_bar + bar_increment(opp_pts, nopp),
                "my_off": noff,
                "opp_off": opp_off,
            })
        return dedup_actions(acts)

    return [{
        "move_str": "H:P,P",
        "my_pts": my_pts[:],
        "opp_pts": opp_pts[:],
        "my_bar": my_bar,
        "opp_bar": opp_bar,
        "my_off": my_off,
        "opp_off": opp_off,
    }]


def bar_increment(old_opp: List[int], new_opp: List[int]) -> int:
    # If a blot was hit, opponent loses one checker from board to bar.
    old_sum = sum(old_opp)
    new_sum = sum(new_opp)
    dec = old_sum - new_sum
    return dec if dec > 0 else 0


def enumerate_sequence(
    my_pts: List[int],
    opp_pts: List[int],
    my_bar: int,
    opp_bar: int,
    my_off: int,
    opp_off: int,
    first_die: int,
    second_die: int,
    order_char: str,
) -> List[Dict]:
    acts = []
    first_moves = legal_single_moves(my_pts, opp_pts, my_bar, my_off, first_die)

    if not first_moves:
        return []

    for tok1, _src1, my1, opp1, bar1, off1, _hit1 in first_moves:
        opp_bar1 = opp_bar + bar_increment(opp_pts, opp1)
        second_moves = legal_single_moves(my1, opp1, bar1, off1, second_die)
        if second_moves:
            for tok2, _src2, my2, opp2, bar2, off2, _hit2 in second_moves:
                opp_bar2 = opp_bar1 + bar_increment(opp1, opp2)
                acts.append({
                    "move_str": f"{order_char}:{tok1},{tok2}",
                    "my_pts": my2,
                    "opp_pts": opp2,
                    "my_bar": bar2,
                    "opp_bar": opp_bar2,
                    "my_off": off2,
                    "opp_off": opp_off,
                })
        else:
            acts.append({
                "move_str": f"{order_char}:{tok1},P",
                "my_pts": my1,
                "opp_pts": opp1,
                "my_bar": bar1,
                "opp_bar": opp_bar1,
                "my_off": off1,
                "opp_off": opp_off,
            })

    return acts


def dedup_actions(actions: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for a in actions:
        key = (
            a["move_str"],
            tuple(a["my_pts"]),
            tuple(a["opp_pts"]),
            a["my_bar"],
            a["opp_bar"],
            a["my_off"],
            a["opp_off"],
        )
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out


def pip_count(pts: List[int], bar: int) -> int:
    # Distance to bear off for our orientation: point i has distance i+1
    total = bar * 25
    for i, c in enumerate(pts):
        if c:
            total += c * (i + 1)
    return total


def evaluate_state(
    my_pts: List[int],
    opp_pts: List[int],
    my_bar: int,
    opp_bar: int,
    my_off: int,
    opp_off: int,
) -> float:
    score = 0.0

    # Strong primary goals
    score += 120.0 * my_off
    score -= 120.0 * opp_off
    score -= 85.0 * my_bar
    score += 70.0 * opp_bar

    my_pip = pip_count(my_pts, my_bar)
    opp_pip = pip_count(opp_pts, opp_bar)
    score += 0.22 * (opp_pip - my_pip)

    # Points made and blots
    my_points = 0
    opp_points = 0
    my_blots = 0
    opp_blots = 0
    for i in range(24):
        if my_pts[i] >= 2:
            my_points += 1
        elif my_pts[i] == 1:
            my_blots += 1
        if opp_pts[i] >= 2:
            opp_points += 1
        elif opp_pts[i] == 1:
            opp_blots += 1

    score += 9.0 * my_points
    score -= 7.0 * opp_points
    score -= 13.0 * my_blots
    score += 8.0 * opp_blots

    # Home board strength
    my_home_points = sum(1 for i in range(6) if my_pts[i] >= 2)
    opp_home_points = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)
    score += 14.0 * my_home_points
    score -= 10.0 * opp_home_points

    # Anchors / advanced points
    # Good to own points in opponent home (18..23) as anchors when contact exists
    my_anchors = sum(1 for i in range(18, 24) if my_pts[i] >= 2)
    opp_anchors = sum(1 for i in range(0, 6) if opp_pts[i] >= 2)
    score += 6.0 * my_anchors
    score -= 5.0 * opp_anchors

    # Penalize stripped points and heavy stacks a bit
    for i in range(24):
        if my_pts[i] >= 4:
            score -= 1.8 * (my_pts[i] - 3)
        if opp_pts[i] >= 4:
            score += 1.2 * (opp_pts[i] - 3)

    # Reward primes and consecutive blocks
    score += 6.0 * longest_prime(my_pts)
    score -= 4.5 * longest_prime(opp_pts)

    # Racing mode: if no contact, focus more on pip/off, less on blots
    if not has_contact(my_pts, opp_pts):
        score += 0.35 * (opp_pip - my_pip)
        score += 20.0 * my_off - 20.0 * opp_off
        score += 2.0 * home_smoothness(my_pts)
        score -= 0.5 * my_blots

    return score


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


def has_contact(my_pts: List[int], opp_pts: List[int]) -> bool:
    # Contact exists if any of my checkers are behind any opponent checker.
    my_positions = [i for i, c in enumerate(my_pts) if c > 0]
    opp_positions = [i for i, c in enumerate(opp_pts) if c > 0]
    if not my_positions or not opp_positions:
        return False
    # Since I move from high to low and opponent from low to high,
    # contact if my farthest-back checker is above opponent farthest-back from their side,
    # equivalently if there exists my i > opp j.
    return max(my_positions) > min(opp_positions)


def home_smoothness(my_pts: List[int]) -> float:
    # Prefer distribution in home board for bearoff efficiency.
    val = 0.0
    for i in range(6):
        c = my_pts[i]
        if c == 2:
            val += 1.5
        elif c == 3:
            val += 1.0
        elif c >= 4:
            val -= 0.5 * (c - 3)
        elif c == 1:
            val -= 0.5
    return val
