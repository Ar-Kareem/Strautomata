
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    BOARD_SIZE = 19
    occupied = set(me) | set(opponent)
    me_set = set(me)
    opp_set = set(opponent)

    def get_liberties(stone_list):
        liberties_map = {}
        for stone in stone_list:
            r, c = stone
            libs = []
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    if (nr, nc) not in occupied:
                        libs.append((nr, nc))
            liberties_map[stone] = set(libs)
        return liberties_map

    # 1. Capture opponent if they are in Atari
    opp_libs = get_liberties(opponent)
    for stone, libs in opp_libs.items():
        if len(libs) == 1:
            move = list(libs)[0]
            return move

    # 2. Save own stones if in Atari
    my_libs = get_liberties(me)
    for stone, libs in my_libs.items():
        if len(libs) == 1:
            move = list(libs)[0]
            # Simple check to ensure the escape move itself has liberties
            future_occupied = occupied | {move}
            escape_libs = 0
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = move[0] + dr, move[1] + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE and (nr, nc) not in future_occupied:
                    escape_libs += 1
            if escape_libs > 0:
                return move

    # 3. Opening: Take star points
    star_points = [(4, 4), (4, 16), (16, 4), (16, 16), (10, 10), (4, 10), (10, 4), (10, 16), (16, 10)]
    random.shuffle(star_points)
    for sp in star_points:
        if sp not in occupied:
            return sp

    # 4. Proximity move: Play near existing stones
    potential_moves = []
    for r, c in me:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE and (nr, nc) not in occupied:
                potential_moves.append((nr, nc))
    
    if potential_moves:
        return random.choice(potential_moves)

    # 5. Fallback: Any legal move
    all_coords = [(r, c) for r in range(1, 20) for c in range(1, 20)]
    random.shuffle(all_coords)
    for move in all_coords:
        if move not in occupied:
            # Basic suicide prevention (very simple)
            has_liberty = False
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = move[0] + dr, move[1] + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    if (nr, nc) not in occupied or (nr, nc) in me_set:
                        has_liberty = True
                        break
            if has_liberty:
                return move

    return (0, 0)
