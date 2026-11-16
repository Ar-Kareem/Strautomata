
# breakthrough_policy.py
from typing import List, Tuple, Set
import itertools

Position = Tuple[int, int]
Board = Tuple[Set[Position], Set[Position]]  # (my_pieces, opp_pieces)

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Return the chosen move for the current player.

    Args:
        me:   list of (row, col) for our pieces
        opp:  list of (row, col) for opponent pieces
        color: 'w' (white moves up) or 'b' (black moves down)

    Returns:
        ((from_row, from_col), (to_row, to_col))
    """
    my_set = set(me)
    opp_set = set(opp)

    # pre‑compute direction
    forward = 1 if color == 'w' else -1
    goal_row = 7 if color == 'w' else 0
    opp_color = 'b' if color == 'w' else 'w'

    # --------------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------------
    def on_board(r: int, c: int) -> bool:
        return 0 <= r <= 7 and 0 <= c <= 7

    def generate_moves(my: Set[Position], opponent: Set[Position]) -> List[Tuple[Position, Position]]:
        moves = []
        for (r, c) in my:
            # straight forward
            nr = r + forward
            if on_board(nr, c) and (nr, c) not in my and (nr, c) not in opponent:
                moves.append(((r, c), (nr, c)))
            # diagonal captures / moves
            for dc in (-1, 1):
                nc = c + dc
                if not on_board(nr, nc):
                    continue
                target = (nr, nc)
                if target in opponent:          # capture
                    moves.append(((r, c), target))
                elif target not in my:          # ordinary diagonal move
                    moves.append(((r, c), target))
        return moves

    def apply_move(my: Set[Position], opp: Set[Position],
                   move: Tuple[Position, Position]) -> Board:
        frm, to = move
        new_my = set(my)
        new_my.remove(frm)
        new_my.add(to)
        new_opp = set(opp)
        if to in new_opp:          # capture
            new_opp.remove(to)
        return (new_my, new_opp)

    def piece_advance(pos: Position) -> int:
        r, _ = pos
        return r if color == 'w' else (7 - r)

    def opponent_advance(pos: Position) -> int:
        r, _ = pos
        return r if opp_color == 'w' else (7 - r)

    def is_vulnerable(pos: Position, opp: Set[Position]) -> bool:
        """Can opponent capture this piece on their next move?"""
        r, c = pos
        opp_forward = -forward  # opponent moves opposite direction
        nr = r + opp_forward
        for dc in (-1, 1):
            nc = c + dc
            if on_board(nr, nc) and (nr, nc) in opp:
                return True
        return False

    def static_eval(my: Set[Position], opponent: Set[Position]) -> int:
        # win checks
        if any(r == goal_row for (r, _) in my):
            return 1000
        if not opponent:
            return 500

        score = 0
        score += sum(piece_advance(p) for p in my)
        score -= sum(opponent_advance(p) for p in opponent)

        # safety penalty
        for p in my:
            if is_vulnerable(p, opponent):
                score -= 5
        return score

    # --------------------------------------------------------------
    # Immediate win / capture detection
    # --------------------------------------------------------------
    all_my_moves = generate_moves(my_set, opp_set)
    for mv in all_my_moves:
        _, to = mv
        if to[0] == goal_row:
            # moving onto goal row wins immediately
            return mv
    # capture leading to opponent elimination
    for mv in all_my_moves:
        frm, to
        if to in opp_set and len(opp_set) == 1:
            return mv

    # --------------------------------------------------------------
    # Two‑ply minimax (depth = 2)
    # --------------------------------------------------------------
    best_move = None
    best_value = -10**9

    for my_move in all_my_moves:
        my_after, opp_after = apply_move(my_set, opp_set, my_move)

        # opponent's turn: generate their moves
        opp_moves = generate_moves(opp_after, my_after)
        if not opp_moves:
            # opponent has no moves ⇒ we win
            val = 1000
        else:
            # opponent will choose the move that minimises evaluation
            worst_for_us = 10**9
            for opp_move in opp_moves:
                opp_next_my, opp_next_opp = apply_move(opp_after, my_after, opp_move)
                val = static_eval(opp_next_my, opp_next_opp)
                if val < worst_for_us:
                    worst_for_us = val
            val = worst_for_us

        # incorporate immediate capture bonus (encourages captures)
        if my_move[1] in opp_set:
            val += 10

        if val > best_value:
            best_value = val
            best_move = my_move

    # if for any reason no move was selected (should not happen), pick first legal move
    if best_move is None:
        best_move = all_my_moves[0]

    return best_move
