
import numpy as np

def policy(board):
    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1), (0,1),
                  (1,-1), (1,0), (1,1)]

    def get_movable_cells(brd, r, c):
        cells = []
        for dr, dc in directions:
            step = 1
            while True:
                new_r = r + dr * step
                new_c = c + dc * step
                if not (0 <= new_r < 6 and 0 <= new_c < 6):
                    break
                if brd[new_r, new_c] != 0:
                    break
                cells.append((new_r, new_c))
                step += 1
        return cells

    def generate_moves(brd, player):
        all_moves = []
        for fr in range(6):
            for fc in range(6):
                if brd[fr, fc] != player:
                    continue
                movement_cells = get_movable_cells(brd, fr, fc)
                for to_r, to_c in movement_cells:
                    temp_brd = brd.copy()
                    temp_brd[fr, fc] = 0
                    temp_brd[to_r, to_c] = player
                    arrow_cells = get_movable_cells(temp_brd, to_r, to_c)
                    for arrow_r, arrow_c in arrow_cells:
                        all_moves.append(((fr, fc), (to_r, to_c), (arrow_r, arrow_c)))
        return all_moves

    candidates = generate_moves(board, 1)
    if not candidates:
        return ""

    best_score = float('inf')
    best_candidates = []

    for candidate in candidates:
        (fr, fc), (to_r, to_c), (arrow_r, arrow_c) = candidate
        new_brd = board.copy()
        new_brd[fr, fc] = 0
        new_brd[to_r, to_c] = 1  # Already 1, but safe to overwrite
        new_brd[arrow_r, arrow_c] = -1

        opp_moves = generate_moves(new_brd, 2)
        opp_count = len(opp_moves)
        if opp_count < best_score:
            best_score = opp_count
            best_candidates = [candidate]
        elif opp_count == best_score:
            best_candidates.append(candidate)

    def center_distance(r, c):
        return (r - 2.5)**2 + (c - 2.5)**2

    best_choice = best_candidates[0]
    min_distance = center_distance(best_choice[1][0], best_choice[1][1])

    for candidate in best_candidates[1:]:
        cur_to_r, cur_to_c = candidate[1]
        cur_dist = center_distance(cur_to_r, cur_to_c)
        if cur_dist < min_distance:
            best_choice = candidate
            min_distance = cur_dist

    fr, fc = best_choice[0]
    to_r, to_c = best_choice[1]
    arrow_r, arrow_c = best_choice[2]
    return f"{fr},{fc}:{to_r},{to_c}:{arrow_r},{arrow_c}"
