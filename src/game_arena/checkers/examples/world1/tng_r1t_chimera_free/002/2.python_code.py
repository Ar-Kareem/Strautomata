
import math

def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_pieces = set(my_men + my_kings)
    opp_all = opp_men + opp_kings
    opp_pieces = set(opp_all)
    king_pieces = set(opp_kings)

    def get_captures(start, is_king, color, my_pieces, opp_current, visited=None):
        if visited is None:
            visited = set()
        visited = visited.copy()
        visited.add(start)
        x, y = start
        captures = []
        directions = []
        if is_king or color == 'b':
            directions.extend([(-1, -1), (-1, 1)])
        if is_king or color == 'w':
            directions.extend([(1, -1), (1, 1)])
        
        for dx, dy in directions:
            mid_x, mid_y = x + dx, y + dy
            end_x, end_y = x + 2*dx, y + 2*dy
            if (mid_x, mid_y) in opp_current and (end_x, end_y) not in my_pieces | set(opp_current) and 0 <= end_x < 8 and 0 <= end_y < 8 and (end_x, end_y) not in visited:
                new_opp = [p for p in opp_current if p != (mid_x, mid_y)]
                sub_captures = get_captures((end_x, end_y), is_king, color, my_pieces, new_opp, visited)
                if sub_captures:
                    for sc in sub_captures:
                        captures.append(((start, sc[1][1]), sc[1][0] + 1, sc[2] + [(mid_x, mid_y)]))
                else:
                    captures.append(((start, (end_x, end_y)), 1, [(mid_x, mid_y)]))
        return captures or []

    capture_moves = []
    for pos in my_men:
        captures = get_captures(pos, False, color, my_pieces, opp_all)
        for c in captures:
            capture_moves.append((c[0], c[1], c[2]))
    for pos in my_kings:
        captures = get_captures(pos, True, color, my_pieces, opp_all)
        for c in captures:
            capture_moves.append((c[0], c[1], c[2]))

    if capture_moves:
        max_captured = max(len(c[2]) for c in capture_moves)
        candidates = [c for c in capture_moves if len(c[2]) == max_captured]
        max_kings = max(sum(1 for p in c[2] if p in king_pieces) for c in candidates)
        king_candidates = [c for c in candidates if sum(1 for p in c[2] if p in king_pieces) == max_kings]
        best_move = None
        min_promo_dist = float('inf')
        for c in king_candidates:
            to_pos = c[0][1]
            promo_row = 0 if color == 'b' else 7
            promo_dist = abs(to_pos[0] - promo_row)
            center_dist = abs(to_pos[0] - 3.5) + abs(to_pos[1] - 3.5)
            if promo_dist < min_promo_dist or (promo_dist == min_promo_dist and center_dist < min_promo_dist):
                min_promo_dist = promo_dist
                best_move = c
        return best_move[0] if best_move else capture_moves[0][0]

    else:
        non_captures = []
        for pos in my_men + my_kings:
            x, y = pos
            is_king = pos in my_kings
            dirs = []
            if is_king or color == 'b':
                dirs += [(-1, -1), (-1, 1)]
            if is_king or color == 'w':
                dirs += [(1, -1), (1, 1)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8 and (nx, ny) not in my_pieces and (nx, ny) not in opp_pieces:
                    non_captures.append(((x, y), (nx, ny)))

        if not non_captures:
            return ((0, 0), (0, 0))

        best_score = -float('inf')
        best_move = non_captures[0]
        promo_row = 0 if color == 'b' else 7
        for move in non_captures:
            to_pos = move[1]
            is_king_move = move[0] in my_kings
            if is_king_move:
                score = (3.5 - abs(to_pos[0] - 3.5)) + (3.5 - abs(to_pos[1] - 3.5))
            else:
                promo_dist = abs(to_pos[0] - promo_row)
                score = (7 - promo_dist) * 2 + (3.5 - abs(to_pos[0] - 3.5)) + (3.5 - abs(to_pos[1] - 3.5))
            if score > best_score or (score == best_score and abs(to_pos[0]-3.5)+abs(to_pos[1]-3.5) < abs(best_move[1][0]-3.5)+abs(best_move[1][1]-3.5)):
                best_score = score
                best_move = move
        return best_move
