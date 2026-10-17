
import time
import math

TIME_LIMIT = 0.92


class TimeoutSearch(Exception):
    pass


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal Kalah move index 0..5 for the current player.
    """
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    start = time.perf_counter()
    deadline = start + TIME_LIMIT

    root_you = tuple(you)
    root_opp = tuple(opponent)

    best_move = legal[0]

    # Tactical fast preference: if a move gives an immediate extra turn, use it
    # as initial fallback before deeper search completes.
    for m in legal:
        if you[m] == 6 - m:
            best_move = m
            break

    def check_time():
        if time.perf_counter() >= deadline:
            raise TimeoutSearch

    def make_move(me_t, opp_t, move):
        """
        Apply move from current player's perspective.

        Returns:
            next_me, next_opp, same_turn
        If same_turn is False, next_me/next_opp are swapped so that next_me is
        always the player to move.
        """
        me = list(me_t)
        opp = list(opp_t)

        seeds = me[move]
        me[move] = 0
        pos = move

        while seeds:
            pos = (pos + 1) % 13
            if pos <= 5:
                me[pos] += 1
            elif pos == 6:
                me[6] += 1
            else:
                opp[pos - 7] += 1
            seeds -= 1

        same_turn = pos == 6

        # Capture: last seed in own empty house, opposite has seeds.
        if 0 <= pos <= 5 and me[pos] == 1:
            opposite = 5 - pos
            if opp[opposite] > 0:
                me[6] += opp[opposite] + 1
                me[pos] = 0
                opp[opposite] = 0

        # End game collection.
        me_houses = sum(me[:6])
        opp_houses = sum(opp[:6])
        if me_houses == 0 or opp_houses == 0:
            me[6] += me_houses
            opp[6] += opp_houses
            for i in range(6):
                me[i] = 0
                opp[i] = 0

        me = tuple(me)
        opp = tuple(opp)

        if same_turn:
            return me, opp, True
        else:
            return opp, me, False

    def is_terminal(me, opp):
        return sum(me[:6]) == 0 or sum(opp[:6]) == 0

    def static_eval(me, opp):
        """
        Evaluation from current player's perspective.
        Positive means good for player to move.
        """
        my_store = me[6]
        op_store = opp[6]
        my_houses = sum(me[:6])
        op_houses = sum(opp[:6])

        # Terminal: exact final store difference, heavily weighted.
        if my_houses == 0 or op_houses == 0:
            return 100000 * (my_store - op_store)

        score = 0

        # Stores are the main objective.
        score += 120 * (my_store - op_store)

        # Seeds on our side are slightly more flexible, but stores matter more.
        score += 6 * (my_houses - op_houses)

        # Extra-turn opportunities.
        for i in range(6):
            if me[i] > 0 and me[i] % 13 == 6 - i:
                score += 22
            if opp[i] > 0 and opp[i] % 13 == 6 - i:
                score -= 22

        # Capture threats/opportunities.
        for i in range(6):
            if me[i] == 0 and opp[5 - i] > 0:
                # Empty own pit opposite opponent seeds can become a capture target.
                score += 2 * opp[5 - i]
            if opp[i] == 0 and me[5 - i] > 0:
                score -= 2 * me[5 - i]

        # Prefer keeping legal options.
        score += 3 * sum(1 for x in me[:6] if x > 0)
        score -= 3 * sum(1 for x in opp[:6] if x > 0)

        # Near endgame, side seeds convert soon, so account for likely collection.
        if my_houses + op_houses <= 12:
            score += 12 * (my_houses - op_houses)

        return score

    def immediate_order_score(me, opp, move):
        """
        Larger means search earlier.
        """
        before_store = me[6]
        before_opp = sum(opp[:6])
        nme, nopp, same = make_move(me, opp, move)

        # If turn changed, nopp is the mover after the move because perspective swapped.
        if same:
            after_me = nme
            after_opp = nopp
            store_gain = after_me[6] - before_store
            opp_loss = before_opp - sum(after_opp[:6])
        else:
            # Original mover is now nopp.
            after_me = nopp
            after_opp = nme
            store_gain = after_me[6] - before_store
            opp_loss = before_opp - sum(after_opp[:6])

        s = 0
        s += 1000 if same else 0
        s += 90 * store_gain
        s += 35 * max(0, opp_loss)
        s += static_eval(nme, nopp) // 20
        return s

    def ordered_moves(me, opp):
        moves = [i for i in range(6) if me[i] > 0]
        moves.sort(key=lambda m: immediate_order_score(me, opp, m), reverse=True)
        return moves

    def search(me, opp, depth, alpha, beta, table):
        check_time()

        key = (me, opp, depth)
        got = table.get(key)
        if got is not None:
            return got

        if depth <= 0 or is_terminal(me, opp):
            val = static_eval(me, opp)
            table[key] = val
            return val

        moves = ordered_moves(me, opp)
        if not moves:
            val = static_eval(me, opp)
            table[key] = val
            return val

        best = -10**18

        for m in moves:
            nme, nopp, same = make_move(me, opp, m)
            if same:
                # Same player moves again, so perspective is unchanged.
                val = search(nme, nopp, depth - 1, alpha, beta, table)
            else:
                # Perspective swapped; negate opponent's value.
                val = -search(nme, nopp, depth - 1, -beta, -alpha, table)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        table[key] = best
        return best

    # Dynamic depth target. Iterative deepening ensures we always have a move.
    total_seeds_in_houses = sum(you[:6]) + sum(opponent[:6])
    if total_seeds_in_houses <= 10:
        max_depth = 24
    elif total_seeds_in_houses <= 18:
        max_depth = 18
    elif total_seeds_in_houses <= 28:
        max_depth = 14
    else:
        max_depth = 10

    try:
        for depth in range(1, max_depth + 1):
            table = {}
            alpha = -10**18
            beta = 10**18

            current_best_move = best_move
            current_best_val = -10**18

            moves = ordered_moves(root_you, root_opp)
            for m in moves:
                check_time()
                nme, nopp, same = make_move(root_you, root_opp, m)
                if same:
                    val = search(nme, nopp, depth - 1, alpha, beta, table)
                else:
                    val = -search(nme, nopp, depth - 1, -beta, -alpha, table)

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = m

                if val > alpha:
                    alpha = val

            # Completed this depth, so commit its result.
            if current_best_move in legal:
                best_move = current_best_move

    except TimeoutSearch:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        return legal[0]

    if best_move not in legal or you[best_move] <= 0:
        return legal[0]
    return int(best_move)
