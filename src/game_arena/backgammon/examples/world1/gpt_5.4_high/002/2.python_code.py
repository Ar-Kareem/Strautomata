
from typing import List, Tuple, Dict

# 21 unordered rolls with backgammon probabilities out of 36.
_ROLLS = [(a, b, 1 if a == b else 2) for a in range(1, 7) for b in range(a, 7)]


def _make_board(state: dict) -> dict:
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
    }


def _clone(board: dict) -> dict:
    return {
        "my_pts": board["my_pts"][:],
        "opp_pts": board["opp_pts"][:],
        "my_bar": board["my_bar"],
        "opp_bar": board["opp_bar"],
        "my_off": board["my_off"],
        "opp_off": board["opp_off"],
    }


def _flip(board: dict) -> dict:
    # Convert to the opponent-to-move perspective.
    return {
        "my_pts": board["opp_pts"][::-1],
        "opp_pts": board["my_pts"][::-1],
        "my_bar": board["opp_bar"],
        "opp_bar": board["my_bar"],
        "my_off": board["opp_off"],
        "opp_off": board["my_off"],
    }


def _all_in_home(board: dict) -> bool:
    if board["my_bar"] > 0:
        return False
    pts = board["my_pts"]
    for i in range(6, 24):
        if pts[i] > 0:
            return False
    return True


def _apply_from_point(board: dict, i: int, dest: int) -> dict:
    b = _clone(board)
    b["my_pts"][i] -= 1
    if dest is None:
        b["my_off"] += 1
    else:
        if b["opp_pts"][dest] == 1:
            b["opp_pts"][dest] = 0
            b["opp_bar"] += 1
        b["my_pts"][dest] += 1
    return b


def _single_moves(board: dict, die: int) -> List[Tuple[str, dict]]:
    moves: List[Tuple[str, dict]] = []
    if die < 1 or die > 6:
        return moves

    # Bar entry has priority.
    if board["my_bar"] > 0:
        dest = 24 - die  # 23..18 for die 1..6
        if 0 <= dest < 24 and board["opp_pts"][dest] < 2:
            b = _clone(board)
            b["my_bar"] -= 1
            if b["opp_pts"][dest] == 1:
                b["opp_pts"][dest] = 0
                b["opp_bar"] += 1
            b["my_pts"][dest] += 1
            moves.append(("B", b))
        return moves

    home_ready = _all_in_home(board)
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]

    for i in range(24):
        if my_pts[i] <= 0:
            continue

        dest = i - die
        token = f"A{i}"

        if dest >= 0:
            if opp_pts[dest] < 2:
                moves.append((token, _apply_from_point(board, i, dest)))
        else:
            if not home_ready:
                continue
            legal_bearoff = False
            # Exact bear-off.
            if i == die - 1:
                legal_bearoff = True
            # Oversized die: allowed only from the highest occupied point.
            elif i < die - 1:
                legal_bearoff = True
                for j in range(i + 1, 6):
                    if my_pts[j] > 0:
                        legal_bearoff = False
                        break
            if legal_bearoff:
                moves.append((token, _apply_from_point(board, i, None)))

    return moves


def _dedup_actions(actions: List[Tuple[str, dict]]) -> List[Tuple[str, dict]]:
    seen = {}
    for action, board in actions:
        if action not in seen:
            seen[action] = board
    return list(seen.items())


def _legal_actions_from_board(board: dict, dice: List[int]) -> List[Tuple[str, dict]]:
    dice = list(dice[:2])

    if len(dice) == 0:
        return [("H:P,P", board)]

    if len(dice) == 1:
        d = int(dice[0])
        first = _single_moves(board, d)
        if not first:
            return [("H:P,P", board)]
        return _dedup_actions([(f"H:{t1},P", b1) for t1, b1 in first])

    d1, d2 = int(dice[0]), int(dice[1])

    if d1 == d2:
        d = d1
        actions: List[Tuple[str, dict]] = []
        first = _single_moves(board, d)
        for t1, b1 in first:
            second = _single_moves(b1, d)
            for t2, b2 in second:
                actions.append((f"H:{t1},{t2}", b2))
        if actions:
            return _dedup_actions(actions)

        # If both cannot be played, play one if possible.
        if first:
            return _dedup_actions([(f"H:{t1},P", b1) for t1, b1 in first])
        return [("H:P,P", board)]

    hi = max(d1, d2)
    lo = min(d1, d2)

    actions: List[Tuple[str, dict]] = []

    # Higher die first.
    for t1, b1 in _single_moves(board, hi):
        for t2, b2 in _single_moves(b1, lo):
            actions.append((f"H:{t1},{t2}", b2))

    # Lower die first.
    for t1, b1 in _single_moves(board, lo):
        for t2, b2 in _single_moves(b1, hi):
            actions.append((f"L:{t1},{t2}", b2))

    if actions:
        return _dedup_actions(actions)

    # If only one die can be played, the higher die must be used if possible.
    hi_moves = _single_moves(board, hi)
    if hi_moves:
        return _dedup_actions([(f"H:{t1},P", b1) for t1, b1 in hi_moves])

    lo_moves = _single_moves(board, lo)
    if lo_moves:
        return _dedup_actions([(f"L:{t1},P", b1) for t1, b1 in lo_moves])

    return [("H:P,P", board)]


def _my_pip(board: dict) -> int:
    total = 25 * board["my_bar"]
    for i, c in enumerate(board["my_pts"]):
        if c:
            total += (i + 1) * c
    return total


def _opp_pip(board: dict) -> int:
    total = 25 * board["opp_bar"]
    for i, c in enumerate(board["opp_pts"]):
        if c:
            total += (24 - i) * c
    return total


def _count_made(pts: List[int]) -> int:
    return sum(1 for c in pts if c >= 2)


def _count_blots(pts: List[int]) -> int:
    return sum(1 for c in pts if c == 1)


def _longest_prime(pts: List[int]) -> int:
    best = 0
    cur = 0
    for c in pts:
        if c >= 2:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def _stack_penalty(pts: List[int]) -> int:
    return sum((c - 3) * (c - 3) for c in pts if c > 3)


def _home_stack_penalty_my(pts: List[int]) -> int:
    return sum(max(0, pts[i] - 2) * (i + 1) for i in range(6))


def _home_stack_penalty_opp(pts: List[int]) -> int:
    return sum(max(0, pts[i] - 2) * (24 - i) for i in range(18, 24))


def _my_back(pts: List[int]) -> int:
    for i in range(23, -1, -1):
        if pts[i] > 0:
            return i
    return -1


def _opp_back(pts: List[int]) -> int:
    for i in range(24):
        if pts[i] > 0:
            return i
    return 24


def _has_contact(board: dict) -> bool:
    if board["my_bar"] > 0 or board["opp_bar"] > 0:
        return True
    my_back = _my_back(board["my_pts"])
    opp_back = _opp_back(board["opp_pts"])
    return my_back > opp_back


def _my_exposure(board: dict) -> int:
    total = 0
    opp_pts = board["opp_pts"]
    opp_bar = board["opp_bar"]
    for i, c in enumerate(board["my_pts"]):
        if c != 1:
            continue
        shots = 0
        for j in range(max(0, i - 6), i):
            if opp_pts[j] > 0:
                shots += 2 if opp_pts[j] >= 2 else 1
        if i <= 5 and opp_bar > 0:
            shots += 2 if opp_bar >= 2 else 1
        total += shots
    return total


def _opp_exposure(board: dict) -> int:
    total = 0
    my_pts = board["my_pts"]
    my_bar = board["my_bar"]
    for i, c in enumerate(board["opp_pts"]):
        if c != 1:
            continue
        shots = 0
        for j in range(i + 1, min(24, i + 7)):
            if my_pts[j] > 0:
                shots += 2 if my_pts[j] >= 2 else 1
        if i >= 18 and my_bar > 0:
            shots += 2 if my_bar >= 2 else 1
        total += shots
    return total


def _position_score(board: dict) -> float:
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]
    my_bar = board["my_bar"]
    opp_bar = board["opp_bar"]
    my_off = board["my_off"]
    opp_off = board["opp_off"]

    my_pip = _my_pip(board)
    opp_pip = _opp_pip(board)

    my_made = _count_made(my_pts)
    opp_made = _count_made(opp_pts)
    my_blots = _count_blots(my_pts)
    opp_blots = _count_blots(opp_pts)

    my_home_made = sum(1 for i in range(6) if my_pts[i] >= 2)
    opp_home_made = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)

    my_home_blots = sum(1 for i in range(6) if my_pts[i] == 1)
    opp_home_blots = sum(1 for i in range(18, 24) if opp_pts[i] == 1)

    my_anchor = sum(1 for i in range(18, 24) if my_pts[i] >= 2)
    opp_anchor = sum(1 for i in range(6) if opp_pts[i] >= 2)

    my_prime = _longest_prime(my_pts)
    opp_prime = _longest_prime(opp_pts)

    my_stack = _stack_penalty(my_pts)
    opp_stack = _stack_penalty(opp_pts)

    my_home_stack = _home_stack_penalty_my(my_pts)
    opp_home_stack = _home_stack_penalty_opp(opp_pts)

    my_exposed = _my_exposure(board)
    opp_exposed = _opp_exposure(board)

    my_back = _my_back(my_pts)
    opp_back = _opp_back(opp_pts)

    my_back_score = 24 if my_back < 0 else (23 - my_back)
    opp_back_score = 24 if opp_back > 23 else opp_back

    my_escaped = sum(my_pts[:opp_back]) if opp_back < 24 else sum(my_pts)
    opp_escaped = sum(opp_pts[my_back + 1:]) if my_back >= 0 else sum(opp_pts)

    # Valuable specific inner-board points.
    my_key = (
        1.5 * (1 if my_pts[4] >= 2 else 0) +
        1.0 * (1 if my_pts[3] >= 2 else 0) +
        0.7 * (1 if my_pts[5] >= 2 else 0)
    )
    opp_key = (
        1.5 * (1 if opp_pts[19] >= 2 else 0) +
        1.0 * (1 if opp_pts[20] >= 2 else 0) +
        0.7 * (1 if opp_pts[18] >= 2 else 0)
    )

    if _has_contact(board):
        score = 0.0
        score += 1200.0 * (my_off - opp_off)
        score += 180.0 * (opp_bar - my_bar)
        score += 2.2 * (opp_pip - my_pip)
        score += 24.0 * (my_home_made - opp_home_made)
        score += 7.0 * (my_made - opp_made)
        score += 12.0 * (my_prime - opp_prime)
        score += 6.0 * (my_anchor - opp_anchor)
        score += 3.0 * (my_escaped - opp_escaped)
        score += 1.2 * (my_back_score - opp_back_score)
        score += 3.2 * (opp_exposed - my_exposed)
        score += 1.6 * (opp_stack - my_stack)
        score += 1.0 * (opp_blots - my_blots)
        score += 1.5 * (opp_home_stack - my_home_stack)
        score += 9.0 * (my_key - opp_key)

        if opp_bar > 0:
            score += 10.0 * my_home_made
            score -= 18.0 * my_home_blots
        if my_bar > 0:
            score -= 16.0 * opp_home_made * my_bar
            score += 4.0 * opp_home_blots

        return score

    # Pure-ish race.
    my_out = sum(my_pts[6:])
    opp_out = sum(opp_pts[:18])

    score = 0.0
    score += 1600.0 * (my_off - opp_off)
    score += 250.0 * (opp_bar - my_bar)
    score += 6.5 * (opp_pip - my_pip)
    score += 6.0 * (opp_out - my_out)
    score += 2.5 * (opp_home_stack - my_home_stack)
    score += 2.0 * (opp_stack - my_stack)
    score += 0.8 * (opp_blots - my_blots)
    score += 0.6 * (opp_exposed - my_exposed)
    score += 4.0 * (my_key - opp_key)
    return score


def _move_bonus(after: dict, before: dict) -> float:
    bonus = 0.0

    bonus += 28.0 * (after["opp_bar"] - before["opp_bar"])
    bonus += 18.0 * (after["my_off"] - before["my_off"])
    bonus += 12.0 * (before["my_bar"] - after["my_bar"])
    bonus += 0.6 * (_my_pip(before) - _my_pip(after))

    before_home_made = sum(1 for i in range(6) if before["my_pts"][i] >= 2)
    after_home_made = sum(1 for i in range(6) if after["my_pts"][i] >= 2)
    before_made = _count_made(before["my_pts"])
    after_made = _count_made(after["my_pts"])

    bonus += 10.0 * (after_home_made - before_home_made)
    bonus += 4.0 * (after_made - before_made)

    exp_before = _my_exposure(before)
    exp_after = _my_exposure(after)
    if exp_after > exp_before:
        bonus -= 1.5 * (exp_after - exp_before)

    back_before = _my_back(before["my_pts"])
    back_after = _my_back(after["my_pts"])
    if back_before >= 0 and back_after >= 0:
        bonus += 1.5 * (back_before - back_after)

    return bonus


def _expected_reply_score(board: dict) -> float:
    # Opponent-to-move view.
    opp_board = _flip(board)
    total = 0.0

    for a, b, w in _ROLLS:
        opp_actions = _legal_actions_from_board(opp_board, [a, b])

        # Opponent is assumed to pick the move minimizing our score.
        best_for_opp = None
        for _, opp_after in opp_actions:
            my_view = _flip(opp_after)
            sc = _position_score(my_view)
            if best_for_opp is None or sc < best_for_opp:
                best_for_opp = sc

        total += w * best_for_opp

    return total / 36.0


def policy(state: dict) -> str:
    board = _make_board(state)
    dice = list(state.get("dice", []))
    actions = _legal_actions_from_board(board, dice)

    if not actions:
        return "H:P,P"
    if len(actions) == 1:
        return actions[0][0]

    scored = []
    for action, after in actions:
        base = _position_score(after) + _move_bonus(after, board)
        scored.append([base, action, after])

    # Sort by static score first.
    scored.sort(key=lambda x: (-x[0], x[1]))

    # Shallow opponent-reply lookahead in contact positions.
    if _has_contact(board):
        top_k = min(5, len(scored))
        for i in range(top_k):
            reply = _expected_reply_score(scored[i][2])
            scored[i][0] = 0.45 * scored[i][0] + 0.55 * reply

    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][1]
