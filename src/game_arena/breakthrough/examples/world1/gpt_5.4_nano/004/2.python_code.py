
from __future__ import annotations

from typing import List, Tuple, Optional

# Type aliases
Pos = Tuple[int, int]
Move = Tuple[Pos, Pos]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> Move:
    # Board: 0..7 rows, 0..7 cols
    # color 'b' moves downward (decreasing row), 'w' moves upward (increasing row)
    my: List[Pos] = list(me)
    op: List[Pos] = list(opp)

    my_set = set(my)
    op_set = set(op)

    dir_row = -1 if color == 'b' else 1
    opp_dir_row = -dir_row

    # Terminal checks
    def is_win(my_positions: set[Pos]) -> bool:
        target_row = 0 if color == 'w' else 7
        return any(r == target_row for (r, c) in my_positions)

    def gen_moves(my_positions: set[Pos], op_positions: set[Pos]) -> List[Move]:
        moves: List[Move] = []
        for r, c in my_positions:
            fr = r
            # forward
            tr = r + dir_row
            if 0 <= tr < 8:
                # straight forward
                if (tr, c) not in my_positions and (tr, c) not in op_positions:
                    moves.append(((fr, c), (tr, c)))
                # diagonals forward
                for dc in (-1, 1):
                    tc = c + dc
                    if 0 <= tc < 8 and (tr, tc) in op_positions:
                        moves.append(((fr, c), (tr, tc)))
                    else:
                        # diagonal move allowed only if empty
                        if 0 <= tc < 8 and (tr, tc) not in my_positions and (tr, tc) not in op_positions:
                            moves.append(((fr, c), (tr, tc)))
        # Note: The rules allow diagonal move one step if empty, even without capture.
        # Captures are just diagonals onto occupied squares; can always choose non-capture.
        # However, if we include both capture and empty diagonal, it matches "diagonally forward if target empty".
        # If target contains opponent, only capture move is legal (diagonal forward to occupied by opponent is capture).
        # The above generates both kinds appropriately.
        return moves

    # Apply move
    def apply_move(my_positions: set[Pos], op_positions: set[Pos], mv: Move, for_color: str) -> tuple[set[Pos], set[Pos]]:
        (fr, fc), (tr, tc) = mv
        new_my = set(my_positions)
        new_op = set(op_positions)

        # Remove from origin
        new_my.remove((fr, fc))

        # Determine whether it's a capture (landing on opponent)
        if (tr, tc) in new_op:
            new_op.remove((tr, tc))
        # Place piece
        new_my.add((tr, tc))

        return new_my, new_op

    # Evaluation
    def evaluate(my_positions: set[Pos], op_positions: set[Pos]) -> int:
        # Winning/loss
        if is_win(my_positions):
            return 10_000_000
        if not op_positions:
            return 9_000_000

        # Distance-to-goal heuristic + material
        # For each piece, add progress (how far advanced toward opponent)
        # For black (dir=-1): higher progress = (7 - r); for white (dir=+1): progress = r
        if color == 'b':
            progress = sum(7 - r for (r, _) in my_positions)
            opp_progress = sum(7 - r for (r, _) in op_positions)
        else:
            progress = sum(r for (r, _) in my_positions)
            opp_progress = sum(r for (r, _) in op_positions)

        material = 50 * (len(my_positions) - len(op_positions))

        # Safety: penalize pieces that can be captured next move
        # Approximate by counting for each my piece whether an opponent piece could capture onto it.
        # A capture occurs when opponent is one step behind and diagonally aligned.
        my_safety_penalty = 0
        for r, c in my_positions:
            # opponent would move with opp_dir_row (opposite of my direction)
            from_r = r - opp_dir_row  # because opponent moves opp_dir_row to reach (r,c)
            # Actually opponent's move direction is opp_dir_row, so it comes from (r - opp_dir_row)
            if 0 <= from_r < 8:
                for dc in (-1, 1):
                    from_c = c + dc
                    if 0 <= from_c < 8 and (from_r, from_c) in op_positions:
                        # Ensure diagonal step leads to (r,c)
                        # (r,c) is exactly one step diagonally forward for opponent
                        my_safety_penalty += 10

        # Center control
        center = sum(3 - abs(c - 3.5) for (_, c) in my_positions)

        # Make progress more valuable earlier: normalize by piece count
        prog_score = progress - 0.9 * opp_progress

        return material + int(3 * prog_score) + int(5 * center) - my_safety_penalty

    # Move ordering: prioritize captures and forward moves that increase progress
    def order_moves(mvs: List[Move,]) -> List[Move]:
        def mv_score(mv: Move) -> int:
            (_, _), (tr, tc) = mv
            base = 0
            # capture?
            if (tr, tc) in op_set:
                base += 500
            # forward progress
            base += (5 * (abs(tc - 3.5) < 1.6))  # slight center preference
            if color == 'b':
                base += (7 - tr) * 6
            else:
                base += tr * 6
            # advancement heuristic for safety: prefer not to move into opponent capture if possible
            # (quick check after move)
            # This is approximate: if landed square can be captured by an opponent piece, penalize.
            landing_can_be_captured = 0
            from_r = tr - opp_dir_row
            if 0 <= from_r < 8:
                for dc in (-1, 1):
                    from_c = tc + dc
                    if 0 <= from_c < 8 and (from_r, from_c) in op_set:
                        landing_can_be_captured = 1
            base -= 80 * landing_can_be_captured
            return base

        return sorted(mvs, key=mv_score, reverse=True)

    # Minimax depth-2 with alpha-beta (fast)
    def minimax(my_positions: set[Pos], op_positions: set[Pos], depth: int, alpha: int, beta: int, maximizing: bool) -> int:
        if depth == 0 or is_win(my_positions) or not op_positions:
            return evaluate(my_positions, op_positions)

        if maximizing:
            best = -10**18
            mvs = gen_moves(my_positions, op_positions)
            mvs = order_moves(mvs)
            for mv in mvs:
                nm, no = apply_move(my_positions, op_positions, mv, color)
                val = minimax(nm, no, depth - 1, alpha, beta, False)
                if val > best:
                    best = val
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best
        else:
            # Opponent's turn: they move their pieces downward/upward depending on our color.
            # We'll map by swapping roles in the evaluation: create a minimax from our perspective.
            # For simplicity, implement opponent move generation using actual direction for opponent relative to board.
            # We'll generate legal moves for opponent pieces but still evaluate from our perspective after applying.
            best = 10**18
            # Temporarily treat opponent as "my" moving with opp_dir_row
            saved_dir = dir_row
            # We can't change global dir_row, so inline generation for opponent:
            def gen_moves_opp(op_positions2: set[Pos], my_positions2: set[Pos]) -> List[Move]:
                moves2: List[Move] = []
                for r, c in op_positions2:
                    tr = r + opp_dir_row
                    if 0 <= tr < 8:
                        # straight forward if empty
                        if (tr, c) not in op_positions2 and (tr, c) not in my_positions2:
                            moves2.append(((r, c), (tr, c)))
                        # diagonals
                        for dc in (-1, 1):
                            tc = c + dc
                            if 0 <= tc < 8:
                                if (tr, tc) in my_positions2:
                                    moves2.append(((r, c), (tr, tc)))
                                else:
                                    if (tr, tc) not in op_positions2 and (tr, tc) not in my_positions2:
                                        moves2.append(((r, c), (tr, tc)))
                return moves2

            mvs = gen_moves_opp(op_positions, my_positions)
            # order for opponent: maximize their outcome => from our perspective minimize evaluation.
            def opp_mv_score(mv: Move) -> int:
                (fr, fc), (tr, tc) = mv
                base = 0
                # capture of our piece?
                if (tr, tc) in my_positions:
                    base += 500
                # move their progress
                # For opponent, progress toward their goal is opposite of ours:
                if color == 'b':
                    # opponent is white moves up (dir=+1), their goal row is 0
                    # progress for white = r
                    base += tr * 6
                else:
                    # opponent is black moves down, progress = 7-r
                    base += (7 - tr) * 6
                return base

            mvs = sorted(mvs, key=opp_mv_score, reverse=True)
            for mv in mvs:
                # apply opponent move to our sets
                (fr, fc), (tr, tc) = mv
                new_my = set(my_positions)
                new_op = set(op_positions)
                new_op.remove((fr, fc))
                # capture if landing on our piece
                if (tr, tc) in new_my:
                    new_my.remove((tr, tc))
                new_op.add((tr, tc))

                val = minimax(new_my, new_op, depth - 1, alpha, beta, True)
                if val < best:
                    best = val
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best

    # Immediate win check and "mate in 1" for speed
    legal = gen_moves(my_set, op_set)
    # If no legal moves (shouldn't happen), fallback: any legal move
    if not legal:
        return ((0, 0), (0, 0))

    # If any move reaches opponent home row, take it immediately
    home_row = 0 if color == 'w' else 7
    for mv in legal:
        if mv[1][0] == home_row:
            return mv

    # Depth selection: if we are close to win or have few pieces, go deeper
    max_depth = 2
    # Quick enhancement: if piece count small, allow depth 3
    if len(my_set) + len(op_set) <= 6:
        max_depth = 3

    # Evaluate root moves with minimax
    best_val = -10**18
    best_moves: List[Move] = []
    alpha = -10**18
    beta = 10**18

    # Order root moves for speed
    root_moves = order_moves(legal)

    for mv in root_moves:
        nm, no = apply_move(my_set, op_set, mv, color)
        val = minimax(nm, no, max_depth - 1, alpha, beta, False)
        if val > best_val:
            best_val = val
            best_moves = [mv]
        elif val == best_val:
            best_moves.append(mv)
        alpha = max(alpha, val)

    # Tie-break: prefer moves that advance and/or capture
    def tie_score(mv: Move) -> int:
        (_, _), (tr, tc) = mv
        score = 0
        if (tr, tc) in op_set:
            score += 1000
        if color == 'b':
            score += (7 - tr) * 20
        else:
            score += tr * 20
        score += int(5 * center_bias(tc))
        return score

    def center_bias(c: int) -> float:
        return 1.0 - abs(c - 3.5) / 3.5  # 0..1

    chosen = max(best_moves, key=tie_score) if best_moves else root_moves[0]
    return chosen
