
# Backgammon policy
# Implements: policy(state: dict) -> str

def policy(state: dict) -> str:
    """
    Return a legal move string in the format '<ORDER>:<FROM1>,<FROM2>'.
    The player to move always moves from A23 down toward A0.
    """
    try:
        candidates = _legal_candidates(state)
        if not candidates:
            return "H:P,P"

        best = None
        best_key = None
        for cand in candidates:
            order, starts, used_labels, board = cand
            score = _evaluate(board)
            # Deterministic tie-breakers: prefer fewer passes, then stable lexical order.
            move_count = (1 if starts[0] != "P" else 0) + (1 if starts[1] != "P" else 0)
            key = (score, move_count, order, starts[0], starts[1])
            if best is None or key > best_key:
                best = cand
                best_key = key

        order, starts, _, _ = best
        return f"{order}:{starts[0]},{starts[1]}"
    except Exception:
        # Last-resort fallback: try to produce the first generated legal move.
        try:
            candidates = _legal_candidates(state)
            if candidates:
                order, starts, _, _ = candidates[0]
                return f"{order}:{starts[0]},{starts[1]}"
        except Exception:
            pass
        return "H:P,P"


def _copy_board(state):
    return {
        "my_pts": list(state.get("my_pts", [0] * 24)),
        "opp_pts": list(state.get("opp_pts", [0] * 24)),
        "my_bar": int(state.get("my_bar", 0)),
        "opp_bar": int(state.get("opp_bar", 0)),
        "my_off": int(state.get("my_off", 0)),
        "opp_off": int(state.get("opp_off", 0)),
    }


def _legal_candidates(state):
    dice = list(state.get("dice", []))
    board = _copy_board(state)

    if len(dice) == 0:
        return [("H", ["P", "P"], [], board)]

    if len(dice) == 1:
        d = int(dice[0])
        raw = []
        _dfs_order(board, [d], ["H"], "H", [], [], raw)
        return raw if raw else [("H", ["P", "P"], [], board)]

    d1, d2 = int(dice[0]), int(dice[1])
    hi, lo = max(d1, d2), min(d1, d2)

    raw = []
    _dfs_order(board, [hi, lo], ["H", "L"], "H", [], [], raw)
    _dfs_order(board, [lo, hi], ["L", "H"], "L", [], [], raw)

    if not raw:
        return [("H", ["P", "P"], [], board)]

    def move_count(c):
        return (1 if c[1][0] != "P" else 0) + (1 if c[1][1] != "P" else 0)

    max_moves = max(move_count(c) for c in raw)

    if max_moves == 0:
        # Full pass.
        return [c for c in raw if move_count(c) == 0] or [("H", ["P", "P"], [], board)]

    if max_moves == 2:
        # If both dice can be played, both must be played.
        return [c for c in raw if move_count(c) == 2]

    # Only one die can be played. If the dice differ, the higher die must be
    # played when possible from the original position.
    if hi != lo:
        high_initial = bool(_legal_single_moves(board, hi))
        if high_initial:
            filtered = [
                c for c in raw
                if move_count(c) == 1 and "H" in c[2]
            ]
        else:
            filtered = [
                c for c in raw
                if move_count(c) == 1
            ]
    else:
        filtered = [c for c in raw if move_count(c) == 1]

    return filtered or [c for c in raw if move_count(c) == max_moves] or raw


def _dfs_order(board, dice_seq, label_seq, order_char, starts, used_labels, out):
    idx = len(starts)
    if idx >= len(dice_seq):
        padded = list(starts)
        while len(padded) < 2:
            padded.append("P")
        out.append((order_char, padded[:2], list(used_labels), board))
        return

    die = dice_seq[idx]
    label = label_seq[idx]
    moves = _legal_single_moves(board, die)

    if not moves:
        _dfs_order(board, dice_seq, label_seq, order_char,
                   starts + ["P"], used_labels, out)
    else:
        for src in moves:
            nb = _apply_move(board, src, die)
            _dfs_order(nb, dice_seq, label_seq, order_char,
                       starts + [src], used_labels + [label], out)


def _legal_single_moves(board, die):
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]

    # Bar checkers must enter first.
    if board["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            return ["B"]
        return []

    moves = []

    for i in range(24):
        if my_pts[i] <= 0:
            continue

        dest = i - die

        if dest >= 0:
            if opp_pts[dest] < 2:
                moves.append(f"A{i}")
        else:
            if _can_bear_off_from(board, i, die):
                moves.append(f"A{i}")

    return moves


def _all_in_home(board):
    if board["my_bar"] > 0:
        return False
    my_pts = board["my_pts"]
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True


def _can_bear_off_from(board, point, die):
    if not _all_in_home(board):
        return False

    dest = point - die
    if dest >= 0:
        return False

    # Exact bear-off.
    if die == point + 1:
        return True

    # Oversized die: legal only if there are no checkers farther from home,
    # i.e. on higher-numbered home points.
    if die > point + 1:
        my_pts = board["my_pts"]
        for j in range(point + 1, 6):
            if my_pts[j] > 0:
                return False
        return True

    return False


def _apply_move(board, src, die):
    nb = {
        "my_pts": list(board["my_pts"]),
        "opp_pts": list(board["opp_pts"]),
        "my_bar": board["my_bar"],
        "opp_bar": board["opp_bar"],
        "my_off": board["my_off"],
        "opp_off": board["opp_off"],
    }

    if src == "P":
        return nb

    if src == "B":
        nb["my_bar"] -= 1
        dest = 24 - die
    else:
        point = int(src[1:])
        nb["my_pts"][point] -= 1
        dest = point - die

    if dest < 0:
        nb["my_off"] += 1
    else:
        if nb["opp_pts"][dest] == 1:
            nb["opp_pts"][dest] = 0
            nb["opp_bar"] += 1
        nb["my_pts"][dest] += 1

    return nb


def _evaluate(board):
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]

    my_pip = _my_pip(board)
    opp_pip = _opp_pip(board)

    score = 0.0

    # Racing equity.
    score += 1.35 * (opp_pip - my_pip)

    # Checkers off and on bar.
    score += 28.0 * board["my_off"]
    score -= 24.0 * board["opp_off"]
    score += 34.0 * board["opp_bar"]
    score -= 42.0 * board["my_bar"]

    # Made points, home-board strength, and primes.
    my_made = [i for i, n in enumerate(my_pts) if n >= 2]
    opp_made = [i for i, n in enumerate(opp_pts) if n >= 2]

    score += 4.0 * len(my_made)
    score -= 3.0 * len(opp_made)

    # Our home is A0..A5; opponent home is A18..A23.
    my_home_made = sum(1 for i in range(6) if my_pts[i] >= 2)
    opp_home_made = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)
    score += 8.0 * my_home_made
    score -= 6.0 * opp_home_made

    score += 2.8 * (_longest_prime(my_pts) ** 2)
    score -= 2.0 * (_longest_prime(opp_pts) ** 2)

    # Blot safety.
    my_blot_pen = _my_blot_danger(board)
    opp_blot_pen = _opp_blot_danger(board)
    score -= my_blot_pen
    score += 0.65 * opp_blot_pen

    # Encourage useful distribution: avoid very tall stacks except on low home
    # points during bear-off.
    for i, n in enumerate(my_pts):
        if n > 3:
            if i <= 5:
                score -= 0.8 * (n - 3)
            else:
                score -= 2.0 * (n - 3)

    # During bear-off, prioritize taking checkers off and clearing high points.
    if _all_in_home(board):
        high_home_load = sum(i * my_pts[i] for i in range(6))
        score -= 1.2 * high_home_load
        score += 10.0 * board["my_off"]

    return score


def _my_pip(board):
    total = 25 * board["my_bar"]
    for i, n in enumerate(board["my_pts"]):
        total += (i + 1) * n
    return total


def _opp_pip(board):
    # Opponent moves from A0 toward A23 and then off.
    total = 25 * board["opp_bar"]
    for i, n in enumerate(board["opp_pts"]):
        total += (24 - i) * n
    return total


def _longest_prime(pts):
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


def _my_blot_danger(board):
    """
    Penalize our single checkers that can be hit by opponent's next roll.
    Opponent moves upward, from low indices to high indices.
    """
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]
    penalty = 0.0

    for p, n in enumerate(my_pts):
        if n != 1:
            continue

        threats = 0

        # Opponent checker behind the blot within one die.
        for d in range(1, 7):
            q = p - d
            if q >= 0 and opp_pts[q] > 0:
                threats += min(2, opp_pts[q])

        # Opponent entering from bar can hit our blot on A0..A5.
        if board["opp_bar"] > 0 and 0 <= p <= 5:
            threats += 3

        # Direct-shot probability approximation.
        if threats:
            danger = min(1.0, threats / 6.0)
            # Blots deeper in opponent's attacking zone are more dangerous.
            zone = 1.0
            if p <= 5:
                zone = 1.45
            elif p <= 11:
                zone = 1.15
            penalty += zone * (10.0 + 34.0 * danger)
        else:
            penalty += 1.2

    return penalty


def _opp_blot_danger(board):
    """
    Estimate how exposed opponent blots are to us.
    We move downward, from high indices to low indices.
    """
    my_pts = board["my_pts"]
    opp_pts = board["opp_pts"]
    value = 0.0

    for p, n in enumerate(opp_pts):
        if n != 1:
            continue

        threats = 0

        for d in range(1, 7):
            q = p + d
            if q < 24 and my_pts[q] > 0:
                threats += min(2, my_pts[q])

        # We can enter from bar onto A18..A23.
        if board["my_bar"] > 0 and 18 <= p <= 23:
            threats += 3

        if threats:
            danger = min(1.0, threats / 6.0)
            value += 8.0 + 28.0 * danger
        else:
            value += 0.8

    return value
