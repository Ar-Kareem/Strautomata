
from typing import List, Tuple, Dict

# Unordered roll outcomes with standard 2d6 weights.
# Weight = 1 for doubles, 2 for non-doubles, total weight = 36.
ROLLS = [(a, b, 1 if a == b else 2) for a in range(1, 7) for b in range(a, 7)]


def _normalize_state(state: dict) -> dict:
    return {
        "my_pts": [int(x) for x in state["my_pts"]],
        "opp_pts": [int(x) for x in state["opp_pts"]],
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
        "dice": [int(d) for d in state.get("dice", [])],
    }


def _copy_board(board: dict) -> dict:
    return {
        "my_pts": board["my_pts"][:],
        "opp_pts": board["opp_pts"][:],
        "my_bar": board["my_bar"],
        "opp_bar": board["opp_bar"],
        "my_off": board["my_off"],
        "opp_off": board["opp_off"],
    }


def _token(start) -> str:
    if start == "B":
        return "B"
    return f"A{start}"


def _all_in_home(board: dict) -> bool:
    return board["my_bar"] == 0 and all(board["my_pts"][i] == 0 for i in range(6, 24))


def _legal_starts(board: dict, die: int) -> List:
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]

    # Must enter from bar first.
    if board["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            return ["B"]
        return []

    home_ready = _all_in_home(board)
    highest_home = -1
    if home_ready:
        for i in range(5, -1, -1):
            if my_pts[i] > 0:
                highest_home = i
                break

    starts = []
    for i in range(24):
        if my_pts[i] <= 0:
            continue

        dest = i - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                starts.append(i)
        else:
            # Bearing off.
            if not home_ready:
                continue
            if die == i + 1 or (die > i + 1 and i == highest_home):
                starts.append(i)

    return starts


def _apply_move(board: dict, die: int, start) -> dict:
    new_board = _copy_board(board)

    if start == "B":
        new_board["my_bar"] -= 1
        dest = 24 - die
    else:
        src = int(start)
        new_board["my_pts"][src] -= 1
        dest = src - die
        if dest < 0:
            new_board["my_off"] += 1
            return new_board

    # Hit if opponent has a blot.
    if new_board["opp_pts"][dest] == 1:
        new_board["opp_pts"][dest] = 0
        new_board["opp_bar"] += 1

    new_board["my_pts"][dest] += 1
    return new_board


def _dedupe_actions(actions: List[Tuple[str, dict, int, int]]) -> List[Tuple[str, dict, int, int]]:
    out = []
    seen = set()
    for action in actions:
        move_str = action[0]
        if move_str not in seen:
            seen.add(move_str)
            out.append(action)
    return out


def _generate_legal_actions(state: dict) -> List[Tuple[str, dict, int, int]]:
    dice = list(state.get("dice", []))

    if len(dice) == 0:
        return [("H:P,P", _copy_board(state), 0, 0)]

    # Single-die case.
    if len(dice) == 1:
        d = dice[0]
        actions = []
        for s1 in _legal_starts(state, d):
            b1 = _apply_move(state, d, s1)
            actions.append((f"H:{_token(s1)},P", b1, 1, d))
        if actions:
            return _dedupe_actions(actions)
        return [("H:P,P", _copy_board(state), 0, 0)]

    # Two-dice case.
    d1, d2 = dice[0], dice[1]
    high, low = (d1, d2) if d1 >= d2 else (d2, d1)

    orders = [("H", high, low)]
    if low != high:
        orders.append(("L", low, high))

    candidates = []
    for order_char, first_die, second_die in orders:
        first_starts = _legal_starts(state, first_die)
        for s1 in first_starts:
            b1 = _apply_move(state, first_die, s1)
            second_starts = _legal_starts(b1, second_die)
            if second_starts:
                for s2 in second_starts:
                    b2 = _apply_move(b1, second_die, s2)
                    candidates.append((f"{order_char}:{_token(s1)},{_token(s2)}", b2, 2, first_die))
            else:
                candidates.append((f"{order_char}:{_token(s1)},P", b1, 1, first_die))

    # Rules:
    # - If both dice can be played, must play both.
    # - If only one die can be played, must play the higher die when possible.
    if any(a[2] == 2 for a in candidates):
        candidates = [a for a in candidates if a[2] == 2]
    elif any(a[2] == 1 for a in candidates):
        best_single_die = max(a[3] for a in candidates)
        candidates = [a for a in candidates if a[3] == best_single_die]
    else:
        return [("H:P,P", _copy_board(state), 0, 0)]

    return _dedupe_actions(candidates)


def _my_pip(board: dict) -> int:
    return 25 * board["my_bar"] + sum((i + 1) * n for i, n in enumerate(board["my_pts"]))


def _opp_pip(board: dict) -> int:
    return 25 * board["opp_bar"] + sum((24 - i) * n for i, n in enumerate(board["opp_pts"]))


def _has_contact(board: dict) -> bool:
    if board["my_bar"] > 0 or board["opp_bar"] > 0:
        return True

    my_high = -1
    for i in range(23, -1, -1):
        if board["my_pts"][i] > 0:
            my_high = i
            break

    opp_low = 24
    for i in range(24):
        if board["opp_pts"][i] > 0:
            opp_low = i
            break

    if my_high == -1 or opp_low == 24:
        return False

    return my_high >= opp_low


def _max_run(pts: List[int]) -> int:
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


def _blockade_my(board: dict) -> int:
    # How much my made points block opponent checkers moving upward.
    val = 0
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]
    for j, n in enumerate(opp_pts):
        if n <= 0:
            continue
        blocks = 0
        hi = min(24, j + 7)
        for k in range(j + 1, hi):
            if my_pts[k] >= 2:
                blocks += 1
        val += n * blocks
    return val


def _blockade_opp(board: dict) -> int:
    # How much opponent made points block my checkers moving downward.
    val = 0
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]
    for i, n in enumerate(my_pts):
        if n <= 0:
            continue
        blocks = 0
        lo = max(0, i - 6)
        for k in range(lo, i):
            if opp_pts[k] >= 2:
                blocks += 1
        val += n * blocks
    return val


def _static_eval(board: dict) -> float:
    if board["my_off"] >= 15:
        return 1e9
    if board["opp_off"] >= 15:
        return -1e9

    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]

    my_pip = _my_pip(board)
    opp_pip = _opp_pip(board)
    contact = _has_contact(board)

    my_home = sum(1 for i in range(6) if my_pts[i] >= 2)
    opp_home = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)

    my_blots = sum(1 for n in my_pts if n == 1)
    opp_blots = sum(1 for n in opp_pts if n == 1)

    my_stack = sum(max(0, n - 4) for n in my_pts)
    opp_stack = sum(max(0, n - 4) for n in opp_pts)

    score = 0.0

    # Core race / score terms.
    score += 125.0 * (board["my_off"] - board["opp_off"])
    score += 42.0 * (board["opp_bar"] - board["my_bar"])
    score += (1.15 if contact else 1.90) * (opp_pip - my_pip)
    score += 0.25 * (opp_stack - my_stack)

    # Bar/home interaction.
    score += 4.0 * board["opp_bar"] * my_home
    score -= 4.0 * board["my_bar"] * opp_home

    if contact:
        my_anchors = sum(1 for i in range(18, 24) if my_pts[i] >= 2)
        opp_anchors = sum(1 for i in range(6) if opp_pts[i] >= 2)

        my_run = _max_run(my_pts)
        opp_run = _max_run(opp_pts)

        my_back = sum(my_pts[18:24])
        opp_back = sum(opp_pts[0:6])

        score += 7.0 * (my_home - opp_home)
        score += 4.0 * (my_anchors - opp_anchors)
        score += 3.0 * (my_run - opp_run)
        score += 0.55 * (_blockade_my(board) - _blockade_opp(board))
        score += 0.90 * (opp_blots - my_blots)
        score += 0.45 * (opp_back - my_back)
    else:
        # In a pure race, structure matters less; distribution in the home board matters more.
        my_shape = sum(max(0, my_pts[i] - 2) * (i + 1) for i in range(6))
        opp_shape = sum(max(0, opp_pts[i] - 2) * (24 - i) for i in range(18, 24))

        score += 2.0 * (my_home - opp_home)
        score += 0.20 * (opp_blots - my_blots)
        score += 0.40 * (opp_shape - my_shape)

    return score


def _flip_to_opponent(board: dict, dice: List[int]) -> dict:
    # Convert absolute board to opponent-to-move relative board
    # so they also move 23 -> 0 in the transformed frame.
    return {
        "my_pts": list(reversed(board["opp_pts"])),
        "opp_pts": list(reversed(board["my_pts"])),
        "my_bar": board["opp_bar"],
        "opp_bar": board["my_bar"],
        "my_off": board["opp_off"],
        "opp_off": board["my_off"],
        "dice": list(dice),
    }


def _flip_from_opponent(rel_board: dict) -> dict:
    # Convert transformed opponent-relative board back to my absolute frame.
    return {
        "my_pts": list(reversed(rel_board["opp_pts"])),
        "opp_pts": list(reversed(rel_board["my_pts"])),
        "my_bar": rel_board["opp_bar"],
        "opp_bar": rel_board["my_bar"],
        "my_off": rel_board["opp_off"],
        "opp_off": rel_board["my_off"],
    }


def _expected_after_opponent(board: dict) -> float:
    if board["my_off"] >= 15 or board["opp_off"] >= 15:
        return _static_eval(board)

    total = 0.0
    for a, b, w in ROLLS:
        opp_state = _flip_to_opponent(board, [a, b])
        opp_actions = _generate_legal_actions(opp_state)

        # Opponent chooses the move that is worst for us.
        worst_for_us = None
        for _, rel_after, _, _ in opp_actions:
            abs_after = _flip_from_opponent(rel_after)
            val = _static_eval(abs_after)
            if worst_for_us is None or val < worst_for_us:
                worst_for_us = val

        total += w * worst_for_us

    return total / 36.0


def policy(state: dict) -> str:
    try:
        s = _normalize_state(state)
        actions = _generate_legal_actions(s)

        if not actions:
            return "H:P,P"
        if len(actions) == 1:
            return actions[0][0]

        best_move = actions[0][0]
        best_total = float("-inf")
        best_immediate = float("-inf")

        for move_str, after_board, _, _ in actions:
            immediate = _static_eval(after_board)

            # Use one-ply opponent-roll lookahead only in contact/tactical positions.
            if _has_contact(after_board):
                future = _expected_after_opponent(after_board)
                total = 0.35 * immediate + 0.65 * future
            else:
                total = immediate

            if (
                total > best_total + 1e-12
                or (
                    abs(total - best_total) <= 1e-12
                    and (
                        immediate > best_immediate + 1e-12
                        or (
                            abs(immediate - best_immediate) <= 1e-12
                            and move_str < best_move
                        )
                    )
                )
            ):
                best_total = total
                best_immediate = immediate
                best_move = move_str

        return best_move

    except Exception:
        # Robust fallback: still try to return a legal move.
        try:
            s = _normalize_state(state)
            actions = _generate_legal_actions(s)
            if actions:
                return actions[0][0]
        except Exception:
            pass
        return "H:P,P"
