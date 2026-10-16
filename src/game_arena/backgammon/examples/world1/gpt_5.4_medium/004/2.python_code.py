
from typing import List, Tuple, Union, Dict

Source = Union[int, str]  # int point index or 'B'


def tok(src: Union[Source, None]) -> str:
    if src is None:
        return "P"
    if src == "B":
        return "B"
    return f"A{src}"


def clone_board(state: dict) -> dict:
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
    }


def all_in_home(board: dict) -> bool:
    return board["my_bar"] == 0 and sum(board["my_pts"][6:]) == 0


def legal_sources_for_die(board: dict, die: int) -> List[Source]:
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]

    # Must enter from bar first.
    if board["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] <= 1:
            return ["B"]
        return []

    sources: List[Source] = []
    in_home = all_in_home(board)

    highest_home = -1
    if in_home:
        for p in range(5, -1, -1):
            if my_pts[p] > 0:
                highest_home = p
                break

    for p in range(24):
        if my_pts[p] <= 0:
            continue

        dest = p - die

        # Normal move on board.
        if dest >= 0:
            if opp_pts[dest] <= 1:
                sources.append(p)
            continue

        # Bearing off.
        if in_home:
            # Exact bear off.
            if p == die - 1:
                sources.append(p)
            # Oversized die: only from highest occupied point.
            elif p < die - 1 and highest_home == p:
                sources.append(p)

    return sources


def apply_move(board: dict, die: int, src: Source) -> dict:
    nb = {
        "my_pts": board["my_pts"][:],
        "opp_pts": board["opp_pts"][:],
        "my_bar": board["my_bar"],
        "opp_bar": board["opp_bar"],
        "my_off": board["my_off"],
        "opp_off": board["opp_off"],
    }

    if src == "B":
        nb["my_bar"] -= 1
        dest = 24 - die
    else:
        nb["my_pts"][src] -= 1
        dest = src - die

    if dest < 0:
        nb["my_off"] += 1
        return nb

    if nb["opp_pts"][dest] == 1:
        nb["opp_pts"][dest] = 0
        nb["opp_bar"] += 1

    nb["my_pts"][dest] += 1
    return nb


def legal_actions(state: dict) -> List[Tuple[str, dict]]:
    board = clone_board(state)
    dice = list(state.get("dice", []))

    if len(dice) == 0:
        return [("H:P,P", board)]

    # One die only.
    if len(dice) == 1:
        d = dice[0]
        srcs = legal_sources_for_die(board, d)
        if not srcs:
            return [("H:P,P", board)]
        return [(f"H:{tok(s)},P", apply_move(board, d, s)) for s in srcs]

    d1, d2 = dice[0], dice[1]
    hi, lo = (d1, d2) if d1 >= d2 else (d2, d1)

    # Doubles / same dice value.
    if hi == lo:
        firsts = legal_sources_for_die(board, hi)
        two_moves: List[Tuple[str, dict]] = []
        for s1 in firsts:
            b1 = apply_move(board, hi, s1)
            seconds = legal_sources_for_die(b1, hi)
            for s2 in seconds:
                b2 = apply_move(b1, hi, s2)
                two_moves.append((f"H:{tok(s1)},{tok(s2)}", b2))
        if two_moves:
            return two_moves
        if firsts:
            return [(f"H:{tok(s)},P", apply_move(board, hi, s)) for s in firsts]
        return [("H:P,P", board)]

    # Distinct dice: first search all legal two-die plays.
    two_moves: List[Tuple[str, dict]] = []

    # High then low.
    for s1 in legal_sources_for_die(board, hi):
        b1 = apply_move(board, hi, s1)
        for s2 in legal_sources_for_die(b1, lo):
            b2 = apply_move(b1, lo, s2)
            two_moves.append((f"H:{tok(s1)},{tok(s2)}", b2))

    # Low then high.
    for s1 in legal_sources_for_die(board, lo):
        b1 = apply_move(board, lo, s1)
        for s2 in legal_sources_for_die(b1, hi):
            b2 = apply_move(b1, hi, s2)
            two_moves.append((f"L:{tok(s1)},{tok(s2)}", b2))

    if two_moves:
        return two_moves

    # If only one die can be played, must play the higher die when possible.
    high_srcs = legal_sources_for_die(board, hi)
    if high_srcs:
        return [(f"H:{tok(s)},P", apply_move(board, hi, s)) for s in high_srcs]

    low_srcs = legal_sources_for_die(board, lo)
    if low_srcs:
        return [(f"L:{tok(s)},P", apply_move(board, lo, s)) for s in low_srcs]

    return [("H:P,P", board)]


def pip_count_my(board: dict) -> int:
    return 25 * board["my_bar"] + sum((p + 1) * n for p, n in enumerate(board["my_pts"]))


def pip_count_opp(board: dict) -> int:
    return 25 * board["opp_bar"] + sum((24 - p) * n for p, n in enumerate(board["opp_pts"]))


def max_prime_len(pts: List[int]) -> int:
    best = 0
    cur = 0
    for n in pts:
        if n >= 2:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def has_contact(board: dict) -> bool:
    if board["opp_bar"] > 0:
        return True

    my_positions = [i for i, n in enumerate(board["my_pts"]) if n > 0]
    opp_positions = [i for i, n in enumerate(board["opp_pts"]) if n > 0]

    if not my_positions or not opp_positions:
        return False

    return max(my_positions) > min(opp_positions)


def exposure_penalty(board: dict) -> float:
    # Approximate immediate blot danger from opponent direct shots.
    if not has_contact(board):
        return 0.0

    opp_pts = board["opp_pts"]
    pen = 0.0

    for p, n in enumerate(board["my_pts"]):
        if n != 1:
            continue

        danger = 0.0

        # Opponent entering from bar can hit our blots in points 0..5.
        if board["opp_bar"] > 0 and p <= 5:
            danger += 2.5

        for die in range(1, 7):
            s = p - die
            if s >= 0 and opp_pts[s] > 0:
                # More nearby attackers => more danger.
                danger += min(2, opp_pts[s]) * (1.2 if die <= 3 else 1.0)

        pen += danger

    return pen


def back_checker_penalty(board: dict) -> float:
    # Penalize very deep back checkers in contact positions.
    pts = board["my_pts"]
    found: List[int] = []
    for p in range(23, -1, -1):
        c = pts[p]
        while c > 0 and len(found) < 2:
            found.append(p)
            c -= 1
        if len(found) >= 2:
            break
    return float(sum(found))


def evaluate(board: dict) -> float:
    my_pts = board["my_pts"]

    my_pip = pip_count_my(board)
    opp_pip = pip_count_opp(board)

    home_made = sum(1 for p in range(6) if my_pts[p] >= 2)
    outer_made = sum(1 for p in range(6, 18) if my_pts[p] >= 2)
    anchors = sum(1 for p in range(18, 24) if my_pts[p] >= 2)
    blots = sum(1 for n in my_pts if n == 1)
    stacks = sum(max(0, n - 3) for n in my_pts)
    prime = max_prime_len(my_pts)
    exp_pen = exposure_penalty(board)
    back_pen = back_checker_penalty(board)

    score = 0.0

    # Big objectives.
    score += 160.0 * board["my_off"]
    score -= 160.0 * board["opp_off"]
    score += 1.25 * (opp_pip - my_pip)
    score += 34.0 * board["opp_bar"]
    score -= 42.0 * board["my_bar"]

    # Structure.
    score += 9.0 * home_made
    score += 5.0 * outer_made
    score += 3.0 * anchors
    score += 5.0 * prime

    # Closing out a player on the bar is valuable.
    score += 10.0 * min(2, board["opp_bar"]) * home_made

    if has_contact(board):
        score -= 3.5 * blots
        score -= 5.5 * exp_pen
        score -= 1.5 * stacks
        score -= 0.35 * back_pen
    else:
        # Racing / bearoff.
        score -= 1.2 * blots
        score -= 2.0 * stacks
        score += 0.6 * sum(my_pts[:6])

    return score


def policy(state: dict) -> str:
    actions = legal_actions(state)
    if len(actions) == 1:
        return actions[0][0]

    try:
        best_action = actions[0][0]
        best_score = evaluate(actions[0][1])

        for action, board in actions[1:]:
            score = evaluate(board)
            if score > best_score + 1e-12 or (abs(score - best_score) <= 1e-12 and action < best_action):
                best_score = score
                best_action = action

        return best_action
    except Exception:
        # Fallback: still return a legal move.
        return actions[0][0]
