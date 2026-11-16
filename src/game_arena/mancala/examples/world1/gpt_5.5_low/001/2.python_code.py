
import time
from math import inf


class _Timeout(Exception):
    pass


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal Kalah move index 0..5.

    The search is from the perspective of `you`, who is always the player to move.
    """
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0  # Should never happen per problem statement.

    # Always have a safe legal fallback.
    best_move = legal[0]

    start = time.perf_counter()
    deadline = start + 0.92  # Stay safely under a 1 second limit.
    nodes = 0

    root_you = tuple(you)
    root_opp = tuple(opponent)

    def check_time():
        if time.perf_counter() > deadline:
            raise _Timeout()

    def terminal_value(a, b):
        sa = sum(a[:6])
        sb = sum(b[:6])
        if sa == 0 or sb == 0:
            return (a[6] + sa) - (b[6] + sb)
        return None

    def simulate(a, b, player, move):
        """
        player == 0: root side moves from a against b.
        player == 1: opponent side moves from b against a.

        Returns: new_a, new_b, next_player
        """
        a = list(a)
        b = list(b)

        if player == 0:
            pits = a
            other = b
        else:
            pits = b
            other = a

        seeds = pits[move]
        pits[move] = 0
        pos = move

        while seeds:
            pos = (pos + 1) % 13
            if pos <= 6:
                pits[pos] += 1
            else:
                other[pos - 7] += 1
            seeds -= 1

        extra_turn = (pos == 6)

        # Capture: last seed in an own empty house, opposite has seeds.
        if 0 <= pos <= 5 and pits[pos] == 1:
            opp_idx = 5 - pos
            if other[opp_idx] > 0:
                pits[6] += other[opp_idx] + 1
                pits[pos] = 0
                other[opp_idx] = 0

        if player == 0:
            na, nb = tuple(pits), tuple(other)
        else:
            nb, na = tuple(pits), tuple(other)

        next_player = player if extra_turn else 1 - player
        return na, nb, next_player

    def static_eval(a, b):
        tv = terminal_value(a, b)
        if tv is not None:
            return 10000.0 + tv if tv > 0 else -10000.0 + tv if tv < 0 else 0.0

        store_diff = a[6] - b[6]
        house_diff = sum(a[:6]) - sum(b[:6])

        # Positional heuristics.
        extra_you = 0
        extra_opp = 0
        cap_you = 0
        cap_opp = 0

        for i in range(6):
            if a[i] > 0:
                # Last seed lands in own store.
                if a[i] == 6 - i:
                    extra_you += 1

                # Approximate direct capture without wrapping.
                landing = i + a[i]
                if landing < 6 and a[landing] == 0 and b[5 - landing] > 0:
                    cap_you += b[5 - landing] + 1

            if b[i] > 0:
                if b[i] == 6 - i:
                    extra_opp += 1

                landing = i + b[i]
                if landing < 6 and b[landing] == 0 and a[5 - landing] > 0:
                    cap_opp += a[5 - landing] + 1

        return (
            4.0 * store_diff
            + 0.20 * house_diff
            + 0.65 * (extra_you - extra_opp)
            + 0.35 * (cap_you - cap_opp)
        )

    def move_score(a, b, player, m):
        na, nb, np = simulate(a, b, player, m)
        val = static_eval(na, nb)
        if np == player:
            val += 2.0 if player == 0 else -2.0
        return val if player == 0 else -val

    def ordered_moves(a, b, player):
        pits = a if player == 0 else b
        ms = [i for i in range(6) if pits[i] > 0]
        ms.sort(key=lambda m: move_score(a, b, player, m), reverse=True)
        return ms

    def search(a, b, player, depth, alpha, beta, table):
        nonlocal nodes
        nodes += 1
        if nodes & 1023 == 0:
            check_time()

        tv = terminal_value(a, b)
        if tv is not None:
            return float(tv)

        if depth <= 0:
            return static_eval(a, b)

        key = (a, b, player, depth)
        cached = table.get(key)
        if cached is not None:
            return cached

        if player == 0:
            value = -inf
            for m in ordered_moves(a, b, player):
                na, nb, np = simulate(a, b, player, m)
                child_depth = depth - 1
                value = max(value, search(na, nb, np, child_depth, alpha, beta, table))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = inf
            for m in ordered_moves(a, b, player):
                na, nb, np = simulate(a, b, player, m)
                child_depth = depth - 1
                value = min(value, search(na, nb, np, child_depth, alpha, beta, table))
                beta = min(beta, value)
                if alpha >= beta:
                    break

        table[key] = value
        return value

    try:
        # A quick tactical preference as initial fallback:
        # prefer an immediate extra turn or large capture if available.
        fallback_scores = []
        for m in legal:
            na, nb, np = simulate(root_you, root_opp, 0, m)
            fallback_scores.append((static_eval(na, nb) + (1.5 if np == 0 else 0.0), m))
        best_move = max(fallback_scores)[1]

        # Iterative deepening. The loop limit is intentionally high; time controls it.
        for depth in range(1, 32):
            check_time()
            table = {}
            current_best = best_move
            current_val = -inf
            alpha = -inf
            beta = inf

            for m in ordered_moves(root_you, root_opp, 0):
                check_time()
                na, nb, np = simulate(root_you, root_opp, 0, m)
                val = search(na, nb, np, depth - 1, alpha, beta, table)

                if val > current_val:
                    current_val = val
                    current_best = m

                alpha = max(alpha, current_val)

            best_move = current_best

    except _Timeout:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        return legal[0]

    if best_move not in legal:
        return legal[0]
    return int(best_move)
