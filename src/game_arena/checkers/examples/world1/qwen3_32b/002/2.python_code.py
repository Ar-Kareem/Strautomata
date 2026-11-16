
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    def get_captures(start_r, start_c, is_king):
        def helper(current_r, current_c, is_current_king, captured):
            result = []
            if not is_current_king:
                if color == 'b':
                    directions = [(-1, -1), (-1, 1)]
                else:
                    directions = [(1, -1), (1, 1)]
            else:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                mid_r, mid_c = current_r + dr, current_c + dc
                next_r, next_c = current_r + 2 * dr, current_c + 2 * dc
                if not (0 <= mid_r < 8 and 0 <= mid_c < 8 and 0 <= next_r < 8 and 0 <= next_c < 8):
                    continue
                mid_in_opp = (mid_r, mid_c) in opp_men or (mid_r, mid_c) in opp_kings
                mid_not_captured = (mid_r, mid_c) not in captured
                if not (mid_in_opp and mid_not_captured):
                    continue
                is_occupied = False
                if (next_r, next_c) in my_men or (next_r, next_c) in my_kings:
                    if (next_r, next_c) != (start_r, start_c):
                        is_occupied = True
                if not is_occupied:
                    if (next_r, next_c) in opp_men or (next_r, next_c) in opp_kings:
                        if (next_r, next_c) not in captured:
                            is_occupied = True
                if is_occupied:
                    continue
                new_captured = set(captured)
                new_captured.add((mid_r, mid_c))
                new_is_current_king = is_current_king
                if not is_current_king:
                    if (color == 'b' and next_r == 0) or (color == 'w' and next_r == 7):
                        new_is_current_king = True
                result.append(((start_r, start_c), (next_r, next_c), len(new_captured)))
                further_results = helper(next_r, next_c, new_is_current_king, new_captured)
                result.extend(further_results)
            return result
        return helper(start_r, start_c, is_king, set())
    
    def generate_regular_moves():
        moves = []
        for piece in my_men + my_kings:
            r, c = piece
            is_king = piece in my_kings
            if not is_king:
                if color == 'b':
                    directions = [(-1, -1), (-1, 1)]
                else:
                    directions = [(1, -1), (1, 1)]
            else:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                to_r, to_c = r + dr, c + dc
                if not (0 <= to_r < 8 and 0 <= to_c < 8):
                    continue
                is_occupied = False
                if (to_r, to_c) in my_men or (to_r, to_c) in my_kings:
                    is_occupied = True
                if not is_occupied and ((to_r, to_c) in opp_men or (to_r, to_c) in opp_kings):
                    is_occupied = True
                if not is_occupied:
                    moves.append(((r, c), (to_r, to_c)))
        return moves
    
    def select_best_regular_move(moves):
        best_move = None
        best_score = -1
        for move in moves:
            from_r, from_c = move[0]
            to_r, to_c = move[1]
            is_man = (from_r, from_c) in my_men
            if is_man:
                if color == 'b':
                    score = from_r - to_r
                else:
                    score = (7 - to_r) - (7 - from_r)
            else:
                score = 0
            if score > best_score or (score == best_score and best_move is None):
                best_move = move
                best_score = score
        return best_move

    all_captures = []
    for piece in my_men + my_kings:
        r, c = piece
        is_king = piece in my_kings
        captures = get_captures(r, c, is_king)
        all_captures.extend(captures)
    
    if all_captures:
        max_captured = max(c[2] for c in all_captures)
        best_captures = [c for c in all_captures if c[2] == max_captured]
        return best_captures[0][0]
    else:
        regular_moves = generate_regular_moves()
        best_regular = select_best_regular_move(regular_moves)
        return best_regular
