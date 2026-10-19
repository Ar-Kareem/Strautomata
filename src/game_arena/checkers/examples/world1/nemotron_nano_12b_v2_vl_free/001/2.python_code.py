
from typing import List, Tuple

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    all_my = my_men + my_kings
    all_opp = opp_men + opp_kings

    def is_valid(row, col):
        return 0 <= row < 8 and 0 <= col < 8

    def is_dark(row, col):
        return (row + col) % 2 == 0

    def get_all_opp(row, col):
        return (row, col) in opp_men or (row, col) in opp_kings

    capture_moves = []

    for piece in all_my:
        x, y = piece
        is_king = piece in my_kings
        jump_dirs = []
        if is_king:
            jump_dirs = [(2, 2), (2, -2), (-2, 2), (-2, -2)]
        else:
            if color == 'w':
                jump_dirs = [(2, 2), (2, -2)]
            else:
                jump_dirs = [(-2, 2), (-2, -2)]
        
        for dr, dc in jump_dirs:
            end_r, end_c = x + dr, y + dc
            if not is_valid(end_r, end_c):
                continue
            if not is_dark(end_r, end_c):
                continue
            if (end_r, end_c) in all_my or (end_r, end_c) in all_opp:
                continue
            mid_r = x + dr // 2
            mid_c = y + dc // 2
            if not is_valid(mid_r, mid_c):
                continue
            if get_all_opp(mid_r, mid_c):
                # Single jump
                temp_moves = [(x, y, end_r, end_c)]
                current_pos = (end_r, end_c)
                while True:
                    mid_r_new = current_pos[0] + dr // 2
                    mid_c_new = current_pos[1] + dc // 2
                    end_r_new = current_pos[0] + dr
                    end_c_new = current_pos[1] + dc
                    if not is_valid(end_r_new, end_c_new) or not is_valid(mid_r_new, mid_c_new):
                        break
                    if not is_dark(end_r_new, end_c_new):
                        break
                    if (end_r_new, end_c_new) in all_my or (end_r_new, end_c_new) in all_opp:
                        break
                    if not get_all_opp(mid_r_new, mid_c_new):
                        break
                    current_pos = (end_r_new, end_c_new)
                    temp_moves.append((current_pos[0], current_pos[1], end_r_new, end_c_new))
                if temp_moves:
                    start = (x, y)
                    end = temp_moves[-1][2:]
                    capture_moves.append((start, (end[0], end[1])))
    
    if capture_moves:
        max_caps = max(len([im for s, e, im in capture_moves if s == (x,y)]) for (x,y) in [(m[0] for m in capture_moves)])
        best_captures = [(s, e) for s, e in capture_moves if len([m for m in capture_moves if m[0] == s]) == max_caps]
        return best_captures[0]
    
    non_capture_moves = []
    for piece in all_my:
        x, y = piece
        is_king = piece in my_kings
        move_dirs = []
        if is_king:
            move_dirs = [(1, 1), (-1, -1), (-1, 1), (1, -1)]
        else:
            if color == 'w':
                move_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            else:
                move_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in move_dirs:
            end_r, end_c = x + dr, y + dc
            if not is_valid(end_r, end_c):
                continue
            if not is_dark(end_r, end_c):
                continue
            if (end_r, end_c) in all_my or (end_r, end_c) in all_opp:
                continue
            non_capture_moves.append(((x, y), (end_r, end_c)))
    
    if non_capture_moves:
        return non_capture_moves[0]
    
    return ((0, 0), (0, 0))  # Fallback
