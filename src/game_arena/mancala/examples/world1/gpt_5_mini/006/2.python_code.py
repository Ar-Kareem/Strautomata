
#!/usr/bin/env python3
from typing import List, Tuple, Dict

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Choose a legal move index 0..5 where you[i] > 0.
    Uses minimax with alpha-beta pruning to pick a move.
    """
    # Defensive copy
    you0 = list(you)
    opp0 = list(opponent)

    # Precompute the cycle of pits excluding opponent store:
    # sequence: you houses 0..5, you store (6), opponent houses 0..5
    SEQ = [("you", i) for i in range(6)] + [("you", 6)] + [("opponent", i) for i in range(6)]
    SEQ_LEN = len(SEQ)  # 13

    # Helper: return legal moves indices
    def legal_moves(player_you):
        return [i for i in range(6) if player_you[i] > 0]

    # Simulate a move from perspective of current player being 'you' list and 'opp' list.
    # Returns (new_you, new_opp, extra_turn:bool, terminal:bool)
    def simulate_move(cur_you: List[int], cur_opp: List[int], move_i: int) -> Tuple[List[int], List[int], bool, bool]:
        you_b = cur_you[:]  # copy
        opp_b = cur_opp[:]
        seeds = you_b[move_i]
        you_b[move_i] = 0

        # find start position index in SEQ for the first drop: one position after ("you", move_i)
        start_pos = None
        # locate ("you", move_i) in SEQ
        # It is at index move_i (since you houses 0..5)
        base_idx = move_i  # index of ("you", move_i) in SEQ
        start_pos = (base_idx + 1) % SEQ_LEN

        last_pos = None
        idx = start_pos
        while seeds > 0:
            side, pit = SEQ[idx]
            # place one seed
            if side == "you":
                you_b[pit] += 1
            else:
                # side == "opponent"
                opp_b[pit] += 1
            seeds -= 1
            if seeds == 0:
                last_pos = (side, pit)
            idx = (idx + 1) % SEQ_LEN

        # After sowing, check for capture or extra turn.
        extra_turn = False
        # Capture occurs if last_pos is ("you", j) where j in 0..5 and it was empty before drop,
        # and opposite opponent pit has seeds (>0). We need to know pre-drop value of that you pit.
        # pre-drop value: cur_you[...], but note cur_you had move pit emptied earlier.
        side, pit = last_pos
        if side == "you" and 0 <= pit <= 5:
            # if this pit was empty before the seed was placed
            # pre-drop count = cur_you[pit] (note: cur_you was before any sowing; move pit already zeroed there)
            if cur_you[pit] == 0 and opp_b[5 - pit] > 0:
                # capture the one seed in you_b[pit] and all seeds in opp_b[5-pit]
                captured = you_b[pit] + opp_b[5 - pit]
                you_b[pit] = 0
                opp_b[5 - pit] = 0
                you_b[6] += captured
        # Extra turn if last lands in your store
        if side == "you" and pit == 6:
            extra_turn = True

        # Check end-game: if one side has all houses zero
        you_houses_sum = sum(you_b[0:6])
        opp_houses_sum = sum(opp_b[0:6])
        terminal = False
        if you_houses_sum == 0 or opp_houses_sum == 0:
            # move remaining seeds into respective stores
            you_b[6] += you_houses_sum
            opp_b[6] += opp_houses_sum
            for i in range(6):
                you_b[i] = 0
                opp_b[i] = 0
            terminal = True

        return you_b, opp_b, extra_turn, terminal

    # Evaluation function: positive means good for 'you' (the root player)
    def evaluate(you_s: List[int], opp_s: List[int]) -> float:
        # store difference primary, small weight for seeds on board
        store_diff = you_s[6] - opp_s[6]
        board_diff = sum(you_s[0:6]) - sum(opp_s[0:6])
        return float(store_diff) + 0.1 * float(board_diff)

    # Minimax with alpha-beta and simple transposition table
    from functools import lru_cache

    # Create cache dict since lists are unhashable; use tuples as keys
    transposition: Dict[Tuple[Tuple[int,...], Tuple[int,...], bool, int], float] = {}

    MAX_DEPTH = 8  # search depth in plies

    def minimax(you_s: Tuple[int,...], opp_s: Tuple[int,...], depth: int, maximizing: bool, alpha: float, beta: float) -> float:
        key = (you_s, opp_s, maximizing, depth)
        if key in transposition:
            return transposition[key]

        you_list = list(you_s)
        opp_list = list(opp_s)

        # Terminal check
        if sum(you_list[0:6]) == 0 or sum(opp_list[0:6]) == 0:
            val = float(you_list[6] - opp_list[6]) * 1000.0  # big weight for final result
            transposition[key] = val
            return val

        if depth == 0:
            val = evaluate(you_list, opp_list)
            transposition[key] = val
            return val

        if maximizing:
            best = -1e9
            moves = [i for i in range(6) if you_list[i] > 0]
            if not moves:
                # no move; terminal? gather remaining seeds
                temp_you = you_list[:] 
                temp_opp = opp_list[:]
                temp_opp[6] += sum(temp_opp[0:6])
                temp_you[6] += sum(temp_you[0:6])
                val = float(temp_you[6] - temp_opp[6]) * 1000.0
                transposition[key] = val
                return val

            # Try moves, ordering: prefer extra-turn or capture moves
            ordered_moves = []
            for m in moves:
                ny, no, extra, term = simulate_move(you_list, opp_list, m)
                score_hint = 0
                if extra:
                    score_hint += 100
                # capture hint detection: if last pos was a capture, our simulate_move does capture:
                # detect by sum of stores increased beyond pre move
                store_gain = ny[6] - you_list[6]
                if store_gain > 0:
                    score_hint += 10 * store_gain
                ordered_moves.append(( -score_hint, m, ny, no, extra, term))
            ordered_moves.sort()  # best hints first (negative)
            for _, m, ny, no, extra, term in ordered_moves:
                if term:
                    # terminal result available
                    val = float(ny[6] - no[6]) * 1000.0
                else:
                    if extra:
                        val = minimax(tuple(ny), tuple(no), depth - 1, True, alpha, beta)
                    else:
                        val = minimax(tuple(no), tuple(ny), depth - 1, False, alpha, beta)
                        # Note: when flipping sides for opponent, the parameters are swapped.
                        # Our minimax always treats first tuple as "you" perspective (root player),
                        # but maximizing flag indicates whose turn it is. For consistency, when it's opponent's move
                        # we pass (you_state, opp_state) swapped in recursion above so the function always sees
                        # the 'you' argument as the current player. To keep evaluation consistent we must be careful:
                        # Here we swapped to (no, ny) so the returned value is from that perspective.
                        # To correct we invert the sign? Actually our minimax returns evaluation ALWAYS from root player's
                        # perspective because evaluate uses you_s[6] - opp_s[6] where you_s is the root player.
                        # By swapping tuples (no, ny) we inadvertently changed which side is considered 'you'.
                        # To avoid confusion, we must adopt a consistent approach: always keep the root player's state
                        # as the first tuple. So instead of swapping, we should always call minimax with (you_state, opp_state)
                        # and a flag indicating whose turn it is. To keep this code correct, we'll rework calls below.
                        pass
                if val > best:
                    best = val
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            transposition[key] = best
            return best
        else:
            # minimizing (opponent to move). We will treat the first tuple as still root player's 'you',
            # but moves are made by opponent. So we must simulate using opponent's houses.
            best = 1e9
            moves = [i for i in range(6) if opp_list[i] > 0]
            if not moves:
                # opponent has no move -> game over
                temp_you = you_list[:]
                temp_opp = opp_list[:]
                temp_opp[6] += sum(temp_opp[0:6])
                temp_you[6] += sum(temp_you[0:6])
                val = float(temp_you[6] - temp_opp[6]) * 1000.0
                transposition[key] = val
                return val

            ordered_moves = []
            for m in moves:
                # simulate opponent move: sowing starts from opponent side
                ny_opp = opp_list[:]
                ny_you = you_list[:]
                seeds = ny_opp[m]
                ny_opp[m] = 0
                # starting index in SEQ needs to be after ("opponent", m)
                # find ("opponent", m) index in SEQ:
                base_idx = 7 + m  # because SEQ: 0-5 you houses, 6 you store, 7-12 opponent 0..5
                start_idx = (base_idx + 1) % SEQ_LEN
                idx = start_idx
                last_pos = None
                while seeds > 0:
                    side, pit = SEQ[idx]
                    if side == "you":
                        ny_you[pit] += 1
                    else:
                        ny_opp[pit] += 1
                    seeds -= 1
                    if seeds == 0:
                        last_pos = (side, pit)
                    idx = (idx + 1) % SEQ_LEN
                extra = False
                term = False
                # capture for opponent: if last landed in opponent house that was empty pre-drop and opposite you pit has seeds
                side, pit = last_pos
                if side == "opponent" and 0 <= pit <= 5:
                    if opp_list[pit] == 0 and ny_you[5 - pit] > 0:
                        captured = ny_opp[pit] + ny_you[5 - pit]
                        ny_opp[pit] = 0
                        ny_you[5 - pit] = 0
                        ny_opp[6] += captured
                if side == "opponent" and pit == 6:
                    extra = True
                # check terminal
                if sum(ny_you[0:6]) == 0 or sum(ny_opp[0:6]) == 0:
                    ny_opp[6] += sum(ny_opp[0:6])
                    ny_you[6] += sum(ny_you[0:6])
                    for ii in range(6):
                        ny_opp[ii] = 0
                        ny_you[ii] = 0
                    term = True

                # hint for ordering: prefer opponent extra turns and captures (minimizing wants those)
                score_hint = 0
                if extra:
                    score_hint += 100
                store_gain = ny_opp[6] - opp_list[6]
                if store_gain > 0:
                    score_hint += 10 * store_gain
                ordered_moves.append((score_hint, m, ny_you, ny_opp, extra, term))
            # sort so moves that hurt root player (big score_hint for opponent) are tried first
            ordered_moves.sort(reverse=True)
            for _, m, ny_you, ny_opp, extra, term in ordered_moves:
                if term:
                    val = float(ny_you[6] - ny_opp[6]) * 1000.0
                else:
                    if extra:
                        # opponent moves again -> still minimizing
                        val = minimax(tuple(ny_you), tuple(ny_opp), depth - 1, False, alpha, beta)
                    else:
                        # switch to root player's turn (maximizing), same tuple ordering
                        val = minimax(tuple(ny_you), tuple(ny_opp), depth - 1, True, alpha, beta)
                if val < best:
                    best = val
                beta = min(beta, val)
                if alpha >= beta:
                    break
            transposition[key] = best
            return best

    # At the root: it's our move and 'you0' is root player's you list.
    # We'll enumerate legal moves, simulate them, and pick the move with highest minimax value.
    moves = legal_moves(you0)
    if not moves:
        # should not happen per assumption, but just in case
        for i in range(6):
            if you0[i] > 0:
                return i
        return 0

    best_move = moves[0]
    best_val = -1e9

    # Order root moves by hints too
    root_candidates = []
    for m in moves:
        ny, no, extra, term = simulate_move(you0, opp0, m)
        hint = 0
        if extra:
            hint += 100
        store_gain = ny[6] - you0[6]
        if store_gain > 0:
            hint += 10 * store_gain
        root_candidates.append((-hint, m, ny, no, extra, term))
    root_candidates.sort()

    for _, m, ny, no, extra, term in root_candidates:
        if term:
            val = float(ny[6] - no[6]) * 1000.0
        else:
            if extra:
                val = minimax(tuple(ny), tuple(no), MAX_DEPTH - 1, True, -1e9, 1e9)
            else:
                # opponent to move next: minimizing
                val = minimax(tuple(ny), tuple(no), MAX_DEPTH - 1, False, -1e9, 1e9)
        # choose best (maximize)
        if val > best_val or (val == best_val and m < best_move):
            best_val = val
            best_move = m

    # Ensure legal
    if you0[best_move] == 0:
        for i in range(6):
            if you0[i] > 0:
                return i
    return int(best_move)
