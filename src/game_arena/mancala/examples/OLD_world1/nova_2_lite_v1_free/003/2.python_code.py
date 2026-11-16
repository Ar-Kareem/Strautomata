
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Returns a legal move index (0..5) for the Kalah game.
    Uses a greedy evaluation: prefers moves that give an extra turn,
    then captures, then maximize seeds added to own store.
    """
    best_score = -1
    best_move = None
    for i in range(6):
        if you[i] == 0:
            continue
        # simulate the move
        stones = you[i]
        you_sim = you[:]
        opp_sim = opponent[:]
        you_sim[i] = 0
        cur = i + 1
        extra_turn = False
        capture = False
        added_to_store = 0

        while stones > 0:
            if cur == 7:
                # opponent store, skip
                cur = 0
                continue
            # place one stone
            you_sim[cur] += 1
            stones -= 1
            last_pos = cur
            cur += 1
            # if we passed end of array wrap
            if cur > 6:
                cur = 0

        # after drop, check extra turn
        if last_pos == 6:
            extra_turn = True

        # check capture
        if 0 <= last_pos <= 5:
            opp_idx = 5 - last_pos
            if you_sim[last_pos] == 1:  # empty after drop
                if opp_sim[opp_idx] > 0:
                    capture = True
                    cap = opp_sim[opp_idx] + 1
                    you_sim[6] += cap
                    you_sim[last_pos] = 0
                    opp_sim[opp_idx] = 0
                    added_to_store = cap

        # compute simple heuristic: seeds added to our store this turn
        # includes normal store drop and capture
        store_gain = (last_pos == 6)
        score = (100 * extra_turn) + (10 * capture) + added_to_store + store_gain
        if score > best_score:
            best_score = score
            best_move = i

    return best_move
