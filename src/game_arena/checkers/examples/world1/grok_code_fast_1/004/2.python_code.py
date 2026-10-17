
from typing import Tuple, List

def is_valid(pos: Tuple[int, int]) -> bool:
    r, c = pos
    return 0 <= r < 8 and 0 <= c < 8 and (r + c) % 2 == 0

def get_moves_for_man(man: Tuple[int, int], color: str, all_my: set, all_opp: set) -> List[Tuple[int, int]]:
    r, c = man
    if color == 'b':
        dirs = [(-1, -1), (-1, 1)]
    else:
        dirs = [(1, -1), (1, 1)]
    moves = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if is_valid((nr, nc)) and (nr, nc) not in all_my and (nr, nc) not in all_opp:
            moves.append((nr, nc))
    return moves

def get_jumps_for_man(man: Tuple[int, int], color: str, all_my: set, all_opp: set) -> List[Tuple[int, int]]:
    r, c = man
    if color == 'b':
        dirs = [(-1, -1), (-1, 1)]
    else:
        dirs = [(1, -1), (1, 1)]
    jumps = []
    for dr, dc in dirs:
        jr, jc = r + dr, c + dc
        if (jr, jc) in all_opp:
            nr, nc = r + 2 * dr, c + 2 * dc
            if is_valid((nr, nc)) and (nr, nc) not in all_my and (nr, nc) not in all_opp:
                jumps.append((nr, nc))
    return jumps

def get_moves_for_king(king: Tuple[int, int], all_my: set, all_opp: set) -> List[Tuple[int, int]]:
    r, c = king
    dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    moves = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        while is_valid((nr, nc)) and (nr, nc) not in all_my and (nr, nc) not in all_opp:
            moves.append((nr, nc))
            nr += dr
            nc += dc
    return moves

def get_jumps_for_king(king: Tuple[int, int], all_my: set, all_opp: set) -> List[Tuple[int, int]]:
    r, c = king
    dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    jumps = []
    for dr, dc in dirs:
        jr, jc = r + dr, c + dc
        if (jr, jc) in all_opp:
            nr, nc = r + 2 * dr, c + 2 * dc
            if is_valid((nr, nc)) and (nr, nc) not in all_my and (nr, nc) not in all_opp:
                jumps.append((nr, nc))
    return jumps

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    all_opp = set(opp_men + opp_kings)
    all_my = set(my_men + my_kings)
    # Check for mandatory jumps
    jump_moves = []
    for man in my_men:
        jumps = get_jumps_for_man(man, color, all_my, all_opp)
        for to in jumps:
            jump_moves.append((man, to))
    for king in my_kings:
        jumps = get_jumps_for_king(king, all_my, all_opp)
        for to in jumps:
            jump_moves.append((king, to))
    if jump_moves:
        return jump_moves[0]
    else:
        # Normal moves
        for man in my_men:
            moves = get_moves_for_man(man, color, all_my, all_opp)
            if moves:
                return (man, moves[0])
        for king in my_kings:
            moves = get_moves_for_king(king, all_my, all_opp)
            if moves:
                return (king, moves[0])
    # If no moves, which shouldn't happen
    raise ValueError("No legal moves")
