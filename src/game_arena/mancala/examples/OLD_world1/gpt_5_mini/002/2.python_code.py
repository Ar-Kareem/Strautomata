
from typing import List, Tuple

# Kalah policy implementation.
# The policy performs a shallow lookahead:
# - For each legal initial move, it simulates the move (including captures and extra moves).
# - If the mover gets extra moves, it resolves the chain by assuming the mover will choose moves
#   that maximize (for you) or minimize (for opponent) the final heuristic.
# - After your turn (including any extra moves), it simulates opponent replies similarly (opponent
#   resolves their extra moves to minimize your heuristic).
# - The policy chooses the initial move that maximizes your worst-case resulting heuristic.
#
# This is a lightweight adversarial 2-ply search with full handling of Kalah sowing, stores,
# captures, extra moves, and endgame seed sweep.

# Position mapping: indices 0..12 correspond to:
# 0..5 -> your houses 0..5
# 6    -> your store
# 7..12-> opponent houses 0..5 (in that order)
_POS_LEN = 13  # 6 you houses + your store + 6 opponent houses

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Choose a legal move index (0..5) such that you[i] > 0.
    """
    # Defensive copies
    you0 = list(you)
    opp0 = list(opponent)

    # Precompute legal moves
    legal_moves = [i for i in range(6) if you0[i] > 0]
    if not legal_moves:
        # As per problem statement, this should not happen.
        return 0

    # Heuristic function: store difference plus small weight for seeds in houses.
    def eval_board(y: List[int], o: List[int]) -> float:
        return float(y[6] - o[6]) + 0.05 * (sum(y[0:6]) - sum(o[0:6]))

    # Helper to check if side has no houses
    def side_empty(houses: List[int]) -> bool:
        for x in houses[0:6]:
            if x != 0:
                return False
        return True

    # Convert position index to (player, idx) where player is 'you' or 'opp' and idx 0..6 (6=store for you).
    def pos_to_loc(pos: int) -> Tuple[str, int]:
        if 0 <= pos <= 5:
            return ('you', pos)
        if pos == 6:
            return ('you', 6)
        # 7..12 => opponent houses 0..5
        return ('opp', pos - 7)

    # Get value at pos from arrays
    def get_at(pos: int, y: List[int], o: List[int]) -> int:
        loc, idx = pos_to_loc(pos)
        if loc == 'you':
            return y[idx]
        else:
            return o[idx]

    # Set value at pos
    def set_at(pos: int, val: int, y: List[int], o: List[int]) -> None:
        loc, idx = pos_to_loc(pos)
        if loc == 'you':
            y[idx] = val
        else:
            o[idx] = val

    # Add delta at pos
    def add_at(pos: int, delta: int, y: List[int], o: List[int]) -> None:
        loc, idx = pos_to_loc(pos)
        if loc == 'you':
            y[idx] += delta
        else:
            o[idx] += delta

    # Simulate a single move by the player represented by (y_side, o_side) where y_side moves from house idx (0..5).
    # Returns (new_you, new_opp, next_is_you, game_over)
    def simulate_move(y_side: List[int], o_side: List[int], house_idx: int) -> Tuple[List[int], List[int], bool, bool]:
        # work on copies
        y = list(y_side)
        o = list(o_side)
        seeds = y[house_idx]
        if seeds == 0:
            raise ValueError("simulate_move called on empty house")
        # pick up seeds
        y[house_idx] = 0
        # start position in our 0..12 mapping is house_idx, next seed goes to house_idx+1
        start = house_idx + 1  # integer
        last_pos = None
        # sow seeds one by one
        for s in range(seeds):
            pos = (start + s) % _POS_LEN
            # place one seed at pos
            add_at(pos, 1, y, o)
            last_pos = pos

        # After sowing, check for capture or extra move
        # Extra move if last_pos is your store (pos 6)
        next_is_you = True if last_pos == 6 else False

        # Capture rule: if last_pos is one of your houses 0..5 AND it was empty before that last seed was put
        # AND opposite opponent house (5 - i) has seeds, capture them into your store.
        # We need to know the value before placing last seed at last_pos.
        # To determine that, simulate again quickly: compute how many seeds were placed at last_pos during sowing before final placement.
        # But simpler: recompute by simulating counts: we can compute 'before' as current - 1 (since we just added one).
        loc, idx = pos_to_loc(last_pos)
        if loc == 'you' and 0 <= idx <= 5:
            before = get_at(last_pos, y, o) - 1
            opp_pos = 7 + (5 - idx)  # opponent position corresponding
            opp_seeds = get_at(opp_pos, y, o)
            if before == 0 and opp_seeds > 0:
                # capture: move the seed at last_pos and all seeds from opp_pos into your store (pos 6)
                # remove them
                set_at(last_pos, 0, y, o)
                set_at(opp_pos, 0, y, o)
                add_at(6, 1 + opp_seeds, y, o)

        # After move (and potential capture), check game end: if either side houses all zero, sweep remaining to other store.
        if side_empty(y):
            # opponent collects their houses to opp store
            remaining = sum(o[0:6])
            o = list(o)
            for i in range(6):
                o[i] = 0
            o[6] += remaining
            # fix y's houses already zero
            return y, o, False, True
        if side_empty(o):
            # you collect your remaining houses
            remaining = sum(y[0:6])
            y = list(y)
            for i in range(6):
                y[i] = 0
            y[6] += remaining
            return y, o, False, True

        return y, o, next_is_you, False

    # Resolve extra-move chains for the player whose turn it currently is.
    # The player will choose moves that optimize their objective:
    # - If is_you True, choose moves that maximize eval_board.
    # - If is_you False (opponent), choose moves that minimize eval_board (i.e., best for opponent).
    # The function returns a final (you, opp, game_over) board where the turn has passed to the other player
    # (or the game is over). Depth limit prevents pathological recursion.
    def resolve_extras(y: List[int], o: List[int], is_you_turn: bool, depth: int = 12) -> Tuple[List[int], List[int], bool]:
        if depth <= 0:
            # depth cutoff: return current position as-is (no further moves)
            # but we must not leave the current player with pending moves; treat as turn passing.
            return y, o, False

        # Get legal moves for current player
        if is_you_turn:
            moves = [i for i in range(6) if y[i] > 0]
        else:
            moves = [i for i in range(6) if o[i] > 0]

        # If no legal moves, game should end (handled in simulate_move normally). But guard:
        if not moves:
            # End the game by sweeping other side
            if is_you_turn:
                # you cannot move -> opponent collects
                o2 = list(o)
                rem = sum(o2[0:6])
                for i in range(6):
                    o2[i] = 0
                o2[6] += rem
                return y, o2, True
            else:
                y2 = list(y)
                rem = sum(y2[0:6])
                for i in range(6):
                    y2[i] = 0
                y2[6] += rem
                return y2, o, True

        # For each possible move, simulate and if extra persists, recurse.
        best_board = None
        best_val = None

        for m in moves:
            if is_you_turn:
                ny, no, next_is_you, game_over = simulate_move(y, o, m)
            else:
                # simulate opponent moving: swap roles in simulate_move by passing opponent arrays as 'y_side'
                # and your arrays as 'o_side', then swap back results.
                opp_after, you_after, next_is_opp, game_over = simulate_move(o, y, m)
                # After simulate_move where 'opp' acted as 'you', we mapped:
                # opp_after -> new opponent arrays
                # you_after -> new your arrays
                ny = you_after
                no = opp_after
                # next_is_opp indicates whether the moving player (opp) has extra move
                next_is_you = not next_is_opp  # True if it's your turn now
            if game_over:
                # terminal board; evaluate immediately.
                val = eval_board(ny, no)
                # For terminal, we consider this final board.
                if best_board is None:
                    best_board = (ny, no, True)
                    best_val = val
                else:
                    if is_you_turn:
                        if val > best_val:
                            best_board = (ny, no, True)
                            best_val = val
                    else:
                        if val < best_val:
                            best_board = (ny, no, True)
                            best_val = val
                # No need to continue deeper for this move
                continue

            if next_is_you == is_you_turn:
                # The same player continues (extra move). Recurse to resolve further.
                final_y, final_o, final_game_over = resolve_extras(ny, no, is_you_turn, depth - 1)
            else:
                # Turn passes to opponent; this is the final board after this player's chain.
                final_y, final_o, final_game_over = ny, no, False

            val = eval_board(final_y, final_o)
            if best_board is None:
                best_board = (final_y, final_o, final_game_over)
                best_val = val
            else:
                if is_you_turn:
                    if val > best_val:
                        best_board = (final_y, final_o, final_game_over)
                        best_val = val
                else:
                    if val < best_val:
                        best_board = (final_y, final_o, final_game_over)
                        best_val = val

        # best_board should be set
        if best_board is None:
            # fallback: return current
            return y, o, False
        return best_board

    # Top-level selection: for each legal initial move, simulate and then consider opponent replies.
    best_move = legal_moves[0]
    best_move_val = float("-inf")

    for mv in legal_moves:
        # simulate our initial move mv (you is mover)
        ny, no, next_is_you, game_over = simulate_move(you0, opp0, mv)
        if game_over:
            val = eval_board(ny, no)
            # immediate terminal; treat as final
            if val > best_move_val or (val == best_move_val and (mv < best_move)):
                best_move_val = val
                best_move = mv
            continue

        # If we still have the turn (extra move), resolve our extra-move chain choosing best for us
        if next_is_you:
            final_y, final_o, final_game_over = resolve_extras(ny, no, True)
        else:
            # turn passes to opponent; final_y, final_o are the board prior to opponent move
            final_y, final_o, final_game_over = ny, no, False

        if final_game_over:
            val = eval_board(final_y, final_o)
            if val > best_move_val or (val == best_move_val and (mv < best_move)):
                best_move_val = val
                best_move = mv
            continue

        # Now it's opponent's turn on board (final_y, final_o). Simulate their best reply (they minimize our eval).
        opp_moves = [i for i in range(6) if final_o[i] > 0]
        if not opp_moves:
            # Opponent has no moves -> game would end; sweep our side
            tmp_y = list(final_y)
            rem = sum(tmp_y[0:6])
            for i in range(6):
                tmp_y[i] = 0
            tmp_y[6] += rem
            val = eval_board(tmp_y, final_o)
            if val > best_move_val or (val == best_move_val and (mv < best_move)):
                best_move_val = val
                best_move = mv
            continue

        worst_for_us = float("inf")
        # Opponent tries to minimize our eval.
        for om in opp_moves:
            # simulate opponent move: pass their arrays as mover to simulate_move then swap back
            opp_after, you_after, next_is_opp, game_over2 = simulate_move(final_o, final_y, om)
            if game_over2:
                val_opp = eval_board(you_after, opp_after)
                if val_opp < worst_for_us:
                    worst_for_us = val_opp
                # early prune: if opponent can force extremely bad for us, break
                continue

            if next_is_opp:
                # resolve their extra-move chain; opponent tries to minimize our eval
                res_y, res_o, res_game_over = resolve_extras(you_after, opp_after, False)
            else:
                res_y, res_o, res_game_over = you_after, opp_after, False

            val_opp = eval_board(res_y, res_o)
            if val_opp < worst_for_us:
                worst_for_us = val_opp

        # Now worst_for_us is our value after opponent best reply. Choose move maximizing this.
        if worst_for_us > best_move_val or (worst_for_us == best_move_val and mv < best_move):
            best_move_val = worst_for_us
            best_move = mv

    return int(best_move)
