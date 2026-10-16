
#!/usr/bin/env python3
from typing import List, Tuple, Dict, Optional
import copy

Position = Tuple[int, int]
Move = Tuple[Position, Position]

def policy(my_men: List[Position], my_kings: List[Position],
           opp_men: List[Position], opp_kings: List[Position],
           color: str) -> Move:
    """
    Return a legal move ((from_row, from_col), (to_row, to_col)).
    - Captures are mandatory; multi-jumps are handled.
    - This function finds all legal moves, scores them by heuristics, and returns the best one.
    """
    # Helper utilities
    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def playable(r, c):
        # Only dark squares are playable: assume (r + c) % 2 == 1
        return in_bounds(r, c) and ((r + c) % 2 == 1)

    # Map board positions to piece characters
    # 'b' = black man, 'B' = black king, 'w' = white man, 'W' = white king
    def build_board(my_men, my_kings, opp_men, opp_kings, color):
        board: Dict[Position, str] = {}
        if color == 'b':
            my_man_char, my_king_char = 'b', 'B'
            opp_man_char, opp_king_char = 'w', 'W'
        else:
            my_man_char, my_king_char = 'w', 'W'
            opp_man_char, opp_king_char = 'b', 'B'
        for p in my_men:
            board[p] = my_man_char
        for p in my_kings:
            board[p] = my_king_char
        for p in opp_men:
            board[p] = opp_man_char
        for p in opp_kings:
            board[p] = opp_king_char
        return board

    board = build_board(my_men, my_kings, opp_men, opp_kings, color)

    # Movement directions
    forward = -1 if color == 'b' else 1  # black moves to lower row values, white to higher
    promotion_row = 0 if color == 'b' else 7

    # Opponent info
    opp_color = 'w' if color == 'b' else 'b'
    opp_forward = -1 if opp_color == 'b' else 1
    opp_promotion_row = 0 if opp_color == 'b' else 7

    # Determine whether a piece is one of ours
    def is_my_piece(ch: str) -> bool:
        if color == 'b':
            return ch in ('b', 'B')
        else:
            return ch in ('w', 'W')

    def is_opp_piece(ch: str) -> bool:
        if color == 'b':
            return ch in ('w', 'W')
        else:
            return ch in ('b', 'B')

    def is_king_char(ch: str) -> bool:
        return ch in ('B', 'W')

    # Generate capture sequences for a single piece (multijump), returning list of tuples (final_pos, captured_positions_list)
    def capture_sequences_from(pos: Position, is_king: bool, bd: Dict[Position, str], piece_color: str) -> List[Tuple[Position, List[Position]]]:
        sequences: List[Tuple[Position, List[Position]]] = []

        # For men: in this implementation, men capture only forward (consistent with English/American draughts).
        # They also do not continue capturing after being promoted (promotion ends move).
        # Kings capture in both directions.
        r0, c0 = pos

        def dfs(r, c, board_state: Dict[Position, str], captured: List[Position], became_king: bool) -> None:
            found_any = False
            directions = []
            if is_king or became_king:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            else:
                # man: only forward captures
                directions = [(forward, -1), (forward, 1)]

            for dr, dc in directions:
                ar, ac = r + dr, c + dc  # adjacent square
                lr, lc = r + 2*dr, c + 2*dc  # landing square after jump
                if not (in_bounds(ar, ac) and in_bounds(lr, lc)):
                    continue
                if not playable(lr, lc):
                    continue
                adj_piece = board_state.get((ar, ac))
                land_piece = board_state.get((lr, lc))
                if adj_piece is None:
                    continue
                # must capture opponent piece
                if not is_opp_piece(adj_piece):
                    continue
                if land_piece is not None:
                    continue
                # perform capture
                found_any = True
                # copy board and perform move
                new_board = board_state.copy()
                # remove captured
                del new_board[(ar, ac)]
                # move piece
                del new_board[(r, c)]
                # determine if promotion occurs on landing (promotion takes effect at end of move)
                landing_promotes = (not is_king and ((lr == promotion_row)))
                # we do not allow a man to continue capturing after promotion in this implementation:
                new_is_king = is_king or became_king or landing_promotes
                new_board[(lr, lc)] = ( 'B' if piece_color == 'b' and new_is_king else
                                        'b' if piece_color == 'b' and not new_is_king else
                                        'W' if piece_color == 'w' and new_is_king else
                                        'w' )
                # recursive search: if landing_promotes we stop; else continue
                if landing_promotes:
                    # store sequence and do not continue
                    sequences.append(((lr, lc), captured + [(ar, ac)]))
                else:
                    dfs(lr, lc, new_board, captured + [(ar, ac)], new_is_king)
            if not found_any:
                # no further captures from this node; record current position with captured list (if any)
                if captured:
                    sequences.append(((r, c), captured.copy()))
                # if no captures at all, sequences will be empty (caller will know)
        dfs(r0, c0, bd.copy(), [], is_king)
        return sequences

    # Get all capture moves for our side
    my_positions = [(p, True) for p in my_kings] + [(p, False) for p in my_men]

    all_capture_moves = []  # list of dicts: {'from':pos, 'to':pos, 'captures':[pos], 'captured_kings':int, 'promote':bool}
    for pos, is_king in my_positions:
        # piece color
        piece_color = color
        seqs = capture_sequences_from(pos, is_king, board, piece_color)
        for landing, captured_list in seqs:
            # count captured kings
            captured_kings = 0
            for cp in captured_list:
                ch = board.get(cp)
                if ch and is_king_char(ch):
                    captured_kings += 1
            # check if move results in promotion
            lr, lc = landing
            promote = (not is_king) and (lr == promotion_row)
            all_capture_moves.append({
                'from': pos,
                'to': landing,
                'captures': captured_list,
                'captured_kings': captured_kings,
                'promote': promote
            })

    # If captures exist, captures are mandatory
    moves = []
    if all_capture_moves:
        moves = all_capture_moves
    else:
        # generate simple (non-capture) moves
        simple_moves = []
        for pos, is_king in my_positions:
            r, c = pos
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(forward, -1), (forward, 1)]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if not (in_bounds(nr, nc) and playable(nr, nc)):
                    continue
                if (nr, nc) in board:
                    continue
                promote = (not is_king) and (nr == promotion_row)
                simple_moves.append({
                    'from': pos,
                    'to': (nr, nc),
                    'captures': [],
                    'captured_kings': 0,
                    'promote': promote
                })
        moves = simple_moves

    # Safety evaluation: simulate a move and compute opponent's maximum capture count (we want to minimize that)
    def simulate_board_after_move(move_dict):
        new_board = board.copy()
        frm = move_dict['from']
        to = move_dict['to']
        piece = new_board.get(frm)
        if piece is None:
            # Should not happen; but return current board
            return new_board
        # remove captured pieces if any
        for cp in move_dict['captures']:
            if cp in new_board:
                del new_board[cp]
        # move piece
        del new_board[frm]
        # apply promotion if occurs
        if move_dict['promote']:
            piece = 'B' if color == 'b' else 'W'
        new_board[to] = piece
        return new_board

    # Opponent capture generation for vulnerability measurement
    def opponent_max_captures_from_board(bd: Dict[Position, str]) -> int:
        # Build opponent piece list
        opp_positions = []
        for pos, ch in bd.items():
            if is_opp_piece(ch):
                opp_positions.append((pos, is_king_char(ch)))
        max_capt = 0

        def opp_capture_seqs_from(pos: Position, is_king: bool, board_state: Dict[Position, str], opp_col: str) -> int:
            # return max number of captures starting from pos
            r0, c0 = pos
            best = 0
            found = False
            def dfs_count(r, c, st_board: Dict[Position, str], captured_count: int, became_king: bool) -> None:
                nonlocal best, found
                directions = []
                if is_king or became_king:
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                else:
                    directions = [(opp_forward, -1), (opp_forward, 1)]
                any_jump = False
                for dr, dc in directions:
                    ar, ac = r + dr, c + dc
                    lr, lc = r + 2*dr, c + 2*dc
                    if not (in_bounds(ar, ac) and in_bounds(lr, lc)):
                        continue
                    if not playable(lr, lc):
                        continue
                    adj_piece = st_board.get((ar, ac))
                    land_piece = st_board.get((lr, lc))
                    if adj_piece is None:
                        continue
                    # must capture our piece
                    # check that adj_piece is one of our pieces
                    # our pieces are represented opposite of opponent
                    if color == 'b':
                        our_chars = ('b', 'B')
                        opp_chars = ('w', 'W')
                    else:
                        our_chars = ('w', 'W')
                        opp_chars = ('b', 'B')
                    if adj_piece not in our_chars:
                        continue
                    if land_piece is not None:
                        continue
                    # perform capture
                    any_jump = True
                    new_b = st_board.copy()
                    del new_b[(ar, ac)]
                    del new_b[(r, c)]
                    landing_promotes = (not is_king and ((lr == opp_promotion_row)))
                    new_is_king = is_king or became_king or landing_promotes
                    new_b[(lr, lc)] = ( 'W' if opp_col == 'w' and new_is_king else
                                        'w' if opp_col == 'w' and not new_is_king else
                                        'B' if opp_col == 'b' and new_is_king else
                                        'b' )
                    if landing_promotes:
                        # stop capturing further (promotion ends move)
                        best = max(best, captured_count + 1)
                    else:
                        dfs_count(lr, lc, new_b, captured_count + 1, new_is_king)
                if not any_jump:
                    # no further captures
                    best = max(best, captured_count)
            dfs_count(r0, c0, board_state.copy(), 0, False)
            return best

        for pos, is_k in opp_positions:
            # For each opponent piece compute captures
            cap = opp_capture_seqs_from(pos, is_k, bd, opp_color)
            if cap > max_capt:
                max_capt = cap
        return max_capt

    # Scoring function
    def score_move(mv: Dict) -> Tuple:
        # Higher is better; produce tuple for deterministic comparisons
        base = 0
        # prioritize captures strongly
        num_caps = len(mv['captures'])
        base += num_caps * 1000
        base += mv['captured_kings'] * 500
        if mv['promote']:
            base += 300
        # prefer advancing toward promotion
        fr_r, fr_c = mv['from']
        to_r, to_c = mv['to']
        # advancement: for black (downward), smaller row is better, so advancement = fr_row - to_row
        if color == 'b':
            advancement = fr_r - to_r
        else:
            advancement = to_r - fr_r
        base += advancement * 10
        # simulate board and compute opponent max captures (vulnerability). Lower is better.
        new_board = simulate_board_after_move(mv)
        opp_max_caps = opponent_max_captures_from_board(new_board)
        # Subtract a penalty proportional to opponent capture potential
        base -= opp_max_caps * 200
        # As tie-breaker use fewest resulting opponent pieces (prefer capturing more)
        # Also use deterministic tie-breakers: prefer lower from, then lower to
        tie_breaker = (
            -opp_max_caps,    # minimize opponent capture ability
            -num_caps,        # already in base, but ensure stable ordering
            -mv['captured_kings'],
            mv['from'][0], mv['from'][1], mv['to'][0], mv['to'][1]
        )
        return (base, tie_breaker)

    # Evaluate all moves and pick best
    best_move = None
    best_score = None
    for mv in moves:
        sc = score_move(mv)
        if best_score is None or sc > best_score:
            best_score = sc
            best_move = mv
        elif sc == best_score:
            # deterministic tiebreaker by coordinates
            if (mv['from'], mv['to']) < (best_move['from'], best_move['to']):
                best_move = mv

    # As a fallback if no move found (shouldn't happen), try to return any legal pair
    if best_move is None:
        # Attempt to find any legal simple move (very defensive fallback)
        for pos, is_king in my_positions:
            r, c = pos
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(forward, -1), (forward, 1)]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if playable(nr, nc) and (nr, nc) not in board:
                    return (pos, (nr, nc))
        # If nothing, just return first piece staying put (shouldn't occur)
        if my_men:
            return (my_men[0], my_men[0])
        if my_kings:
            return (my_kings[0], my_kings[0])
        # final fallback
        return ((0,1),(0,1))

    return (best_move['from'], best_move['to'])


# The module exposes only the required policy function.
if __name__ == "__main__":
    # Quick self-test (not exhaustive)
    # Starting simple position: one man can capture
    my_men = [(2, 3)]
    my_kings = []
    opp_men = [(1, 2)]
    opp_kings = []
    print(policy(my_men, my_kings, opp_men, opp_kings, 'b'))  # expect capture from (2,3) to (0,1) if legal
