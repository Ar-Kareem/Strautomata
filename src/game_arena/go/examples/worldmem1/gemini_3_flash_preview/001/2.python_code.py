
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    BOARD_SIZE = 19
    EMPTY = 0
    BLACK = 1
    WHITE = 2

    # Determine internal board state
    # We'll assume we are BLACK and opponent is WHITE for local logic
    state = {}
    for r, c in me: state[(r, c)] = BLACK
    for r, c in opponent: state[(r, c)] = WHITE

    def get_neighbors(r, c):
        res = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                res.append((nr, nc))
        return res

    def get_liberties(r, c, color, visited=None):
        if visited is None: visited = set()
        visited.add((r, c))
        libs = set()
        group = [(r, c)]
        
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in state:
                libs.add((nr, nc))
            elif state[(nr, nc)] == color and (nr, nc) not in visited:
                nl, ng = get_liberties(nr, nc, color, visited)
                libs.update(nl)
                group.extend(ng)
        return libs, group

    # 1. Defend: Check if any of our groups are in Atari
    my_visited = set()
    for r, c in me:
        if (r, c) not in my_visited:
            libs, group = get_liberties(r, c, BLACK)
            my_visited.update(group)
            if len(libs) == 1:
                move = list(libs)[0]
                if move not in state: # Basic check
                    return move, memory

    # 2. Attack: Check if we can capture opponent stones
    opp_visited = set()
    for r, c in opponent:
        if (r, c) not in opp_visited:
            libs, group = get_liberties(r, c, WHITE)
            opp_visited.update(group)
            if len(libs) == 1:
                move = list(libs)[0]
                if move not in state:
                    return move, memory

    # 3. Fuseki: Play in corners/sides if it's early
    star_points = [(4, 4), (4, 16), (16, 4), (16, 16), (4, 10), (10, 4), (10, 16), (16, 10), (10, 10)]
    for pt in star_points:
        if pt not in state:
            return pt, memory

    # 4. Heuristic: Play near existing stones but keep distance
    # Try to find a legal move that isn't suicide
    all_possible = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in state:
                all_possible.append((r, c))
    
    random.shuffle(all_possible)
    
    for move in all_possible:
        # Simple Suicide Check (simplified)
        # If the move has neighbors that are empty or belong to me with > 1 liberty
        # or it captures an opponent stone, it's likely legal.
        has_liberty = False
        for nr, nc in get_neighbors(move[0], move[1]):
            if (nr, nc) not in state:
                has_liberty = True
                break
            if state[(nr, nc)] == BLACK:
                libs, _ = get_liberties(nr, nc, BLACK)
                if len(libs) > 1:
                    has_liberty = True
                    break
            if state[(nr, nc)] == WHITE:
                libs, _ = get_liberties(nr, nc, WHITE)
                if len(libs) == 1:
                    has_liberty = True
                    break
        
        if has_liberty:
            return move, memory

    # Fallback to Pass
    return (0, 0), memory
