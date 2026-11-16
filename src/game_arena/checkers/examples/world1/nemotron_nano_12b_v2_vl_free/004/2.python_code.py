
import sys

def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Selects the best legal move based on an evaluation of the resulting board state.
    Captures are prioritized if available.
    """
    def generate_all_moves():
        moves = []
        occupied = set(my_men).union(my_kings).union(opp_men).union(opp_kings)
        my_pieces = list(my_men) + list(my_kings)

        for piece in my_pieces:
            r, c = piece
            directions = []

            if piece in my_kings:
                directions = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
            else:
                if color == 'w':
                    directions = [(1, 1), (1, -1)]
                else:
                    directions = [(-1, 1), (-1, -1)]

            for dr, dc in directions:
                new_r = r + dr
                new_c = c + dc
                if 0 <= new_r < 8 and 0 <= new_c < 8:
                    if (new_r, new_c) not in occupied:
                        moves.append((piece, (new_r, new_c)))

                # Check for capture move
                mid_r = new_r + dr
                mid_c = new_c + dc
                if 0 <= mid_r < 8 and 0 <= mid_c < 8:
                    mid_pos = (mid_r, mid_c)
                    if mid_pos in opp_men or mid_pos in opp_kings:
                        target_r = mid_r + dr
                        target_c = mid_c + dc
                        if 0 <= target_r < 8 and 0 <= target_c < 8:
                            if (target_r, target_c) not in occupied:
                                moves.append((piece, (target_r, target_c)))

        return moves

    def evaluate_after_move(move):
        from_pos, to_pos = move
        dr = to_pos[0] - from_pos[0]
        dc = to_pos[1] - from_pos[1]
        mid_pos = ((from_pos[0] + to_pos[0]) // 2, (from_pos[1] + to_pos[1]) // 2)

        new_my_men = list(my_men)
        new_my_kings = list(my_kings)
        new_opp_men = list(opp_men)
        new_opp_kings = list(opp_kings)

        # Apply move and promotions
        captured = False
        is_promotion = False

        if from_pos in new_my_men:
            new_my_men.remove(from_pos)
            if (color == 'w' and to_pos[0] == 7) or (color == 'b' and to_pos[0] == 0):
                new_my_kings.append(to_pos)
                is_promotion = True
            else:
                new_my_men.append(to_pos)
        elif from_pos in new_my_kings:
            new_my_kings.remove(from_pos)

        # Apply capture
        if mid_pos in new_opp_men:
            new_opp_men.remove(mid_pos)
            captured = True
        elif mid_pos in new_opp_kings:
            new_opp_kings.remove(mid_pos)
            captured = True

        # Evaluate new state
        my_material = len(new_my_men) + 3 * len(new_my_kings)
        opp_material = len(new_opp_men) + 3 * len(new_opp_kings)
        material_score = my_material - opp_material

        # Positional evaluation
        pos_eval = 0
        for r, _ in new_my_men:
            if color == 'w':
                pos_eval += r * 0.3
            else:
                pos_eval += (7 - r) * 0.3

        for r, _ in new_opp_men:
            if color == 'w':
                pos_eval += (7 - r) * 0.3
            else:
                pos_eval += r * 0.3

        return material_score + pos_eval

    all_moves = generate_all_moves()

    # Separate into captures and non-captures
    captures = []
    non_captures = []
    for move in all_moves:
        from_pos, to_pos = move
        dr = to_pos[0] - from_pos[0]
        dc = to_pos[1] - from_pos[1]
        mid_pos = ((from_pos[0] + to_pos[0]) // 2, (from_pos[1] + to_pos[1]) // 2)
        if mid_pos in opp_men or mid_pos in opp_kings:
            captures.append(move)
        else:
            non_captures.append(move)

    if captures:
        best_move = max(captures, key=lambda m: evaluate_after_move(m))
        return best_move
    elif non_captures:
        best_move = max(non_captures, key=lambda m: evaluate_after_move(m))
        return best_move
    else:
        # No moves available, return None (shouldn't happen per problem statement)
        return None
