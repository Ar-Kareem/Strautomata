
import time
from typing import List, Tuple, Optional, Dict

def policy(
    me: List[Tuple[int, int]],
    opp: List[Tuple[int, int]],
    color: str
) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.82  # Safely within 1.0s limit

    # White moves upwards (+1 row), goal is row 7.
    # Black moves downwards (-1 row), goal is row 0.
    is_white = (color == 'w')
    my_id = 1 if is_white else 2
    opp_id = 2 if is_white else 1

    board = [0] * 64
    my_pieces = set()
    opp_pieces = set()

    for r, c in me:
        sq = (r << 3) | c
        board[sq] = my_id
        my_pieces.add(sq)

    for r, c in opp:
        sq = (r << 3) | c
        board[sq] = opp_id
        opp_pieces.add(sq)

    # Precomputed row bonuses
    white_row_weights = [0, 10, 25, 55, 120, 300, 900, 100000]
    black_row_weights = [100000, 900, 300, 120, 55, 25, 10, 0]

    def generate_moves(is_w: bool):
        moves = []
        pieces = my_pieces if is_w == is_white else opp_pieces
        friendly_id = 1 if is_w else 2
        opp_piece_id = 2 if is_w else 1
        goal_row = 7 if is_w else 0

        if is_w:
            for sq in pieces:
                r = sq >> 3
                c = sq & 7
                to_r = r + 1
                # Forward
                fwd = sq + 8
                if board[fwd] == 0:
                    moves.append((sq, fwd, 1 if to_r == goal_row else 0, False))
                # Diag left
                if c > 0:
                    dl = sq + 7
                    tgt = board[dl]
                    if tgt != friendly_id:
                        moves.append((sq, dl, 2 if to_r == goal_row else (1 if tgt == opp_piece_id else 0), tgt == opp_piece_id))
                # Diag right
                if c < 7:
                    dr = sq + 9
                    tgt = board[dr]
                    if tgt != friendly_id:
                        moves.append((sq, dr, 2 if to_r == goal_row else (1 if tgt == opp_piece_id else 0), tgt == opp_piece_id))
        else:
            for sq in pieces:
                r = sq >> 3
                c = sq & 7
                to_r = r - 1
                # Forward
                fwd = sq - 8
                if board[fwd] == 0:
                    moves.append((sq, fwd, 1 if to_r == goal_row else 0, False))
                # Diag left
                if c > 0:
                    dl = sq - 9
                    tgt = board[dl]
                    if tgt != friendly_id:
                        moves.append((sq, dl, 2 if to_r == goal_row else (1 if tgt == opp_piece_id else 0), tgt == opp_piece_id))
                # Diag right
                if c < 7:
                    dr = sq - 7
                    tgt = board[dr]
                    if tgt != friendly_id:
                        moves.append((sq, dr, 2 if to_r == goal_row else (1 if tgt == opp_piece_id else 0), tgt == opp_piece_id))

        return moves

    # Check for immediate winning move at root
    root_moves = generate_moves(is_white)
    if not root_moves:
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))

    for from_sq, to_sq, win_flag, _ in root_moves:
        if (to_sq >> 3) == (7 if is_white else 0):
            return ((from_sq >> 3, from_sq & 7), (to_sq >> 3, to_sq & 7))

    def evaluate() -> int:
        w_score = 0
        b_score = 0

        w_pieces = my_pieces if is_white else opp_pieces
        b_pieces = opp_pieces if is_white else my_pieces

        if not w_pieces:
            return -999999 if is_white else 999999
        if not b_pieces:
            return 999999 if is_white else -999999

        for sq in w_pieces:
            r = sq >> 3
            c = sq & 7
            w_score += 100 + white_row_weights[r]
            # Center bonus
            if 2 <= c <= 5:
                w_score += 6
            # Protection bonus (defended by a pawn diagonally behind)
            if r > 0:
                if (c > 0 and board[sq - 9] == 1) or (c < 7 and board[sq - 7] == 1):
                    w_score += 15

        for sq in b_pieces:
            r = sq >> 3
            c = sq & 7
            b_score += 100 + black_row_weights[r]
            if 2 <= c <= 5:
                b_score += 6
            if r < 7:
                if (c > 0 and board[sq + 7] == 2) or (c < 7 and board[sq + 9] == 2):
                    b_score += 15

        net = w_score - b_score
        return net if is_white else -net

    tt: Dict[int, Tuple[int, int, Optional[Tuple[int, int]]]] = {}

    def get_state_hash(w_is_turn: bool) -> int:
        h = 0
        for sq in my_pieces:
            h ^= (1 << (sq % 61))
        for sq in opp_pieces:
            h ^= (2 << (sq % 61))
        if w_is_turn:
            h ^= 0x55555555
        return h

    class SearchTimeout(Exception):
        pass

    def alphabeta(depth: int, alpha: int, beta: int, current_is_white: bool) -> int:
        if time.time() - start_time > time_limit:
            raise SearchTimeout()

        is_my_turn = (current_is_white == is_white)
        p_my = my_pieces if is_my_turn else opp_pieces
        p_opp = opp_pieces if is_my_turn else my_pieces

        if not p_my:
            return -900000 - depth
        if not p_opp:
            return 900000 + depth

        state_h = get_state_hash(current_is_white)
        tt_entry = tt.get(state_h)
        best_tt_move = None
        if tt_entry is not None:
            tt_d, tt_val, tt_move = tt_entry
            best_tt_move = tt_move

        if depth <= 0:
            return evaluate() if is_my_turn else -evaluate()

        moves = generate_moves(current_is_white)
        if not moves:
            return -900000 - depth

        # Move ordering
        def score_move(m):
            f_sq, t_sq, win_f, is_cap = m
            if win_f > 0:
                return 1000000
            score = 0
            if (f_sq, t_sq) == best_tt_move:
                score += 500000
            if is_cap:
                score += 10000
            # Advance rank bonus
            t_r = t_sq >> 3
            rank_prog = t_r if current_is_white else (7 - t_r)
            score += rank_prog * 100
            return score

        moves.sort(key=score_move, reverse=True)

        friendly_id = 1 if current_is_white else 2
        active_pieces = my_pieces if is_my_turn else opp_pieces
        inactive_pieces = opp_pieces if is_my_turn else my_pieces
        goal_r = 7 if current_is_white else 0

        best_val = -10000000
        best_move_found = None

        for from_sq, to_sq, win_f, is_cap in moves:
            if (to_sq >> 3) == goal_r:
                return 900000 + depth

            # Make move
            captured = board[to_sq]
            board[from_sq] = 0
            board[to_sq] = friendly_id
            active_pieces.remove(from_sq)
            active_pieces.add(to_sq)
            if captured != 0:
                inactive_pieces.remove(to_sq)

            val = -alphabeta(depth - 1, -beta, -alpha, not current_is_white)

            # Unmake move
            board[from_sq] = friendly_id
            board[to_sq] = captured
            active_pieces.remove(to_sq)
            active_pieces.add(from_sq)
            if captured != 0:
                inactive_pieces.add(to_sq)

            if val > best_val:
                best_val = val
                best_move_found = (from_sq, to_sq)
            alpha = max(alpha, val)
            if alpha >= beta:
                break

        tt[state_h] = (depth, best_val, best_move_found)
        return best_val

    # Iterative deepening
    best_overall_move = (root_moves[0][0], root_moves[0][1])

    for depth in range(1, 10):
        try:
            current_best_val = -10000000
            current_best_move = None
            alpha = -10000000
            beta = 10000000

            # Sort root moves using TT
            def root_score(m):
                f_sq, t_sq, win_f, is_cap = m
                if (f_sq, t_sq) == best_overall_move:
                    return 2000000
                score = 0
                if is_cap:
                    score += 10000
                t_r = t_sq >> 3
                score += (t_r if is_white else (7 - t_r)) * 100
                return score

            root_moves.sort(key=root_score, reverse=True)

            for from_sq, to_sq, win_f, is_cap in root_moves:
                captured = board[to_sq]
                board[from_sq] = 0
                board[to_sq] = my_id
                my_pieces.remove(from_sq)
                my_pieces.add(to_sq)
                if captured != 0:
                    opp_pieces.remove(to_sq)

                val = -alphabeta(depth - 1, -beta, -alpha, not is_white)

                board[from_sq] = my_id
                board[to_sq] = captured
                my_pieces.remove(to_sq)
                my_pieces.add(from_sq)
                if captured != 0:
                    opp_pieces.add(to_sq)

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = (from_sq, to_sq)
                alpha = max(alpha, val)

            if current_best_move is not None:
                best_overall_move = current_best_move

            # If forced win detected, stop searching
            if current_best_val >= 800000:
                break
        except SearchTimeout:
            break

    from_sq, to_sq = best_overall_move
    return ((from_sq >> 3, from_sq & 7), (to_sq >> 3, to_sq & 7))
