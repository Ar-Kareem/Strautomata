
import random

BOARD_SIZE = 11
ALL_CELLS = set((r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

def neighbors(cell):
    r, c = cell
    potential = [(r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)]
    return [p for p in potential if 0 <= p[0] < BOARD_SIZE and 0 <= p[1] < BOARD_SIZE]

def is_connected(black_stones, white_stones, color):
    if color == 'b':
        # Black connects top (row 0) to bottom (row BOARD_SIZE-1)
        stones = set(black_stones)
        to_visit = set((0, c) for c in range(BOARD_SIZE) if (0, c) in stones)
        visited = set()
    elif color == 'w':
        # White connects left (col 0) to right (col BOARD_SIZE-1)
        stones = set(white_stones)
        to_visit = set((r, 0) for r in range(BOARD_SIZE) if (r, 0) in stones)
        visited = set()
    else:
        return False
    
    while to_visit:
        curr = to_visit.pop()
        visited.add(curr)
        if color == 'b' and curr[0] == BOARD_SIZE - 1:
            return True
        if color == 'w' and curr[1] == BOARD_SIZE - 1:
            return True
        for neigh in neighbors(curr):
            if tuple(neigh) in stones and tuple(neigh) not in visited:
                to_visit.add(tuple(neigh))
    return False

def simulate_game(black_starts, white_starts, first_player):
    b, w = list(black_starts), list(white_starts)
    occupied = set(b + w)
    player = first_player
    while occupied != ALL_CELLS:
        empty_locs = list(ALL_CELLS - occupied)
        if not empty_locs:
            break
        m = random.choice(empty_locs)
        occupied.add(m)
        if player == 'b':
            b.append(m)
            if is_connected(b, w, 'b'):
                return 'b'
        else:
            w.append(m)
            if is_connected(w, b, 'w'):
                return 'w'
        player = 'w' if player == 'b' else 'b'
    return 'tie'  # Though unlikely in Hex with full board

def policy(me, opp, color):
    occupied = set(me + opp)
    empty = list(ALL_CELLS - occupied)
    # Randomly select up to 20 moves to evaluate to save time
    candidates = random.sample(empty, min(20, len(empty)))
    
    best_move = None
    best_score = -1
    
    for move in candidates:
        if color == 'b':
            new_b, new_w = me + [move], opp[:]
        else:
            new_b, new_w = opp[:], me + [move]
        score = sum(1 for _ in range(5) if simulate_game(new_b, new_w, 'w' if color == 'b' else 'b') == color)
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move:
        return best_move
    # Fallback to random if all scores 0 or none evaluated
    return random.choice(empty)
