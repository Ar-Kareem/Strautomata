
# backgammon_policy.py

def policy(state: dict) -> str:
    """
    Backgammon move policy.

    Returns compact engine action:
        <ORDER>:<FROM1>,<FROM2>
    where ORDER is H/L and FROM is A0..A23, B, or P.

    Assumptions from prompt:
    - We are always the player to move.
    - We move from high indices toward low indices.
    - Opponent moves opposite direction.
    """
    dice = list(state.get("dice", []))
    if not dice:
        return "H:P,P"

    # Defensive normalization. Engine says 0,1,2 dice; format still needs two FROM tokens.
    if len(dice) == 1:
        hi = lo = dice[0]
        orders = [("H", [dice[0]])]
    else:
        hi, lo = max(dice[0], dice[1]), min(dice[0], dice[1])
        if hi == lo:
            # The API only encodes up to two checker moves, despite doubles in real BG.
            orders = [("H", [hi, lo])]
        else:
            orders = [("H", [hi, lo]), ("L", [lo, hi])]

    candidates = []
    for order, seq in orders:
        enumerate_order(state, order, seq, candidates)

    if not candidates:
        return "H:P,P"

    # Mandatory rules: if at least one candidate uses both dice, play both.
    max_used = max(c["used"] for c in candidates)
    candidates = [c for c in candidates if c["used"] == max_used]

    # If exactly one die can be played, play the higher die when possible.
    if len(dice) >= 2 and hi != lo and max_used == 1:
        high_candidates = [c for c in candidates if c["dice_used"] and c["dice_used"][0] == hi]
        if high_candidates:
            candidates = high_candidates

    best = max(candidates, key=lambda c: c["score"])
    return best["move"]


def enumerate_order(state, order, dice_seq, candidates):
    """Enumerate legal compact actions for a fixed die order."""
    start_board = (
        tuple(state["my_pts"]),
        tuple(state["opp_pts"]),
        int(state.get("my_bar", 0)),
        int(state.get("opp_bar", 0)),
        int(state.get("my_off", 0)),
        int(state.get("opp_off", 0)),
    )

    partials = [(start_board, [], [])]  # board, from_tokens, dice_used

    for die in dice_seq:
        new_partials = []
        any_legal = False
        for board, toks, used_dice in partials:
            moves = legal_single_moves(board, die)
            if moves:
                any_legal = True
                for token, nb in moves:
                    new_partials.append((nb, toks + [token], used_dice + [die]))
            else:
                # Pass for this die is only retained; final filtering handles legality priorities.
                new_partials.append((board, toks + ["P"], used_dice))
        partials = new_partials

    for board, toks, used_dice in partials:
        while len(toks) < 2:
            toks.append("P")
        move = f"{order}:{toks[0]},{toks[1]}"
        candidates.append({
            "move": move,
            "used": len(used_dice),
            "dice_used": used_dice,
            "score": evaluate_board(board, state, len(used_dice), used_dice),
        })


def legal_single_moves(board, die):
    """
    Legal moves for one die from board state.
    Board tuple:
      my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off
    """
    my_pts_t, opp_pts_t, my_bar, opp_bar, my_off, opp_off = board
    my_pts = list(my_pts_t)
    opp_pts = list(opp_pts_t)

    moves = []

    # If on bar, must enter. Since we move 23 -> 0, bar entry with die d lands on 24-d.
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            nb_my = my_pts[:]
            nb_opp = opp_pts[:]
            nb_bar = my_bar - 1
            nb_opp_bar = opp_bar
            if nb_opp[dest] == 1:
                nb_opp[dest] = 0
                nb_opp_bar += 1
            nb_my[dest] += 1
            moves.append(("B", (tuple(nb_my), tuple(nb_opp), nb_bar, nb_opp_bar, my_off, opp_off)))
        return moves

    all_home = all_my_checkers_home(my_pts)

    for src in range(24):
        if my_pts[src] <= 0:
            continue
        dest = src - die

        if dest >= 0:
            if opp_pts[dest] >= 2:
                continue
            nb_my = my_pts[:]
            nb_opp = opp_pts[:]
            nb_my[src] -= 1
            nb_opp_bar = opp_bar
            if nb_opp[dest] == 1:
                nb_opp[dest] = 0
                nb_opp_bar += 1
            nb_my[dest] += 1
            moves.append((f"A{src}", (tuple(nb_my), tuple(nb_opp), my_bar, nb_opp_bar, my_off, opp_off)))
        else:
            # Bearing off.
            if all_home and can_bear_off_from(my_pts, src, die):
                nb_my = my_pts[:]
                nb_my[src] -= 1
                moves.append((f"A{src}", (tuple(nb_my), tuple(opp_pts), my_bar, opp_bar, my_off + 1, opp_off)))

    return moves


def all_my_checkers_home(my_pts):
    # Home board for player moving 23 -> 0 is points 0..5.
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True


def can_bear_off_from(my_pts, src, die):
    # Exact bearoff is always legal.
    if src - die == -1:
        return True
    # Oversized die may bear off only from highest occupied point among home checkers.
    if src - die < -1:
        for higher in range(src + 1, 6):
            if my_pts[higher] > 0:
                return False
        return True
    return False


def evaluate_board(board, orig_state, used_count, used_dice):
    my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off = board
    my_pts = list(my_pts)
    opp_pts = list(opp_pts)

    score = 0.0

    # Winning / race fundamentals.
    score += 150.0 * my_off
    score -= 120.0 * opp_off
    score -= 4.0 * my_bar
    score += 7.0 * opp_bar

    my_pips = pip_count_my(my_pts, my_bar)
    opp_pips = pip_count_opp(opp_pts, opp_bar)
    score += 1.6 * (opp_pips - my_pips)

    # Prefer using dice, especially both.
    score += 18.0 * used_count
    score += 0.15 * sum(used_dice)

    # Made points / primes.
    made = [i for i, n in enumerate(my_pts) if n >= 2]
    for i in made:
        # Points nearer home are valuable; opponent home anchors are also valuable.
        score += 5.0
        if i <= 5:
            score += 4.0
        if i >= 18:
            score += 3.0

    # Longest prime bonus.
    longest = 0
    cur = 0
    for i in range(24):
        if my_pts[i] >= 2:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    score += 5.0 * max(0, longest - 2) ** 2

    # Blot safety and flexibility.
    for i, n in enumerate(my_pts):
        if n == 1:
            danger = blot_danger(i, opp_pts, opp_bar)
            score -= danger
            if i >= 18:
                score -= 6.0  # blots in opponent board are painful
            if i <= 5:
                score -= 2.0
        elif n >= 4:
            score -= 1.5 * (n - 3)  # avoid overstacking

    # Attack opponent blots and contain opponent bar.
    for i, n in enumerate(opp_pts):
        if n == 1:
            score += 0.7 * opp_blot_pressure(i, my_pts, my_bar)

    if opp_bar > 0:
        # Closed/made home points block re-entry.
        closed_home = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)
        # Wait: opponent enters our home from their perspective onto our points 0..5 mirrored by engine.
        # For our board, our made points 0..5 hinder opponent's reentry.
        closed_home = sum(1 for i in range(0, 6) if my_pts[i] >= 2)
        score += 12.0 * closed_home * opp_bar

    # Contact/race phase adjustment: when far ahead in race, reduce blots.
    if my_pips + 15 < opp_pips:
        for i, n in enumerate(my_pts):
            if n == 1:
                score -= 3.0

    # Reward improvement from original: hits.
    score += 20.0 * (opp_bar - int(orig_state.get("opp_bar", 0)))
    score -= 16.0 * (my_bar - int(orig_state.get("my_bar", 0)))

    return score


def pip_count_my(my_pts, my_bar):
    # Distance to bear off: point i needs i+1 pips; bar approx 25.
    return sum((i + 1) * n for i, n in enumerate(my_pts)) + 25 * my_bar


def pip_count_opp(opp_pts, opp_bar):
    # Opponent moves 0 -> 23, distance to bear off from point i is 24-i.
    return sum((24 - i) * n for i, n in enumerate(opp_pts)) + 25 * opp_bar


def blot_danger(my_index, opp_pts, opp_bar):
    """
    Approximate immediate hit danger on our blot.
    Opponent moves upward, so opponent checkers below us can hit with distance my_index-j.
    Opponent bar can enter around low indices; approximated.
    """
    danger = 0.0
    for d in range(1, 7):
        j = my_index - d
        if 0 <= j < 24 and opp_pts[j] > 0:
            danger += 2.0 if opp_pts[j] == 1 else 3.0
    # Bar threats to our low/home points.
    if opp_bar > 0 and 0 <= my_index <= 5:
        danger += 4.0
    # More dangerous in opponent's attacking board.
    if my_index >= 18:
        danger *= 1.6
    return danger


def opp_blot_pressure(opp_index, my_pts, my_bar):
    """
    Approximate our ability to hit an opponent blot.
    We move downward, so our checkers above it can hit.
    """
    pressure = 0.0
    for d in range(1, 7):
        j = opp_index + d
        if 0 <= j < 24 and my_pts[j] > 0:
            pressure += 1.0
    if my_bar > 0 and opp_index >= 18:
        pressure += 1.0
    return pressure
