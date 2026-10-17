
import random
import math
import time
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    start_time = time.time()
    # Board size
    N = 19
    # Convert to set for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones
    
    # Track previous move for ko (simple)
    global LAST_BOARD_HASH
    if 'LAST_BOARD_HASH' not in globals():
        LAST_BOARD_HASH = None
    global PREV_MOVE
    if 'PREV_MOVE' not in globals():
        PREV_MOVE = None
        
    # Helper: liberties of a group
    def liberties(group, stones, other_stones):
        lib = set()
        for (r, c) in group:
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= N and 1 <= nc <= N:
                    if (nr, nc) not in stones and (nr, nc) not in other_stones:
                        lib.add((nr, nc))
        return lib
    
    # Helper: find connected group
    def find_group(r, c, stones, other_stones):
        stack = [(r, c)]
        visited = set()
        color = (r, c) in stones
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = cr + dr, cc + dc
                if 1 <= nr <= N and 1 <= nc <= N:
                    if color and (nr, nc) in stones and (nr, nc) not in visited:
                        stack.append((nr, nc))
                    elif not color and (nr, nc) in other_stones and (nr, nc) not in visited:
                        stack.append((nr, nc))
        return visited
    
    # Helper: captures if played at (r, c) by player
    def get_captures(r, c, my_turn, my_stones_set, opp_stones_set):
        # Temporarily add stone
        if my_turn:
            my_stones_set.add((r, c))
        else:
            opp_stones_set.add((r, c))
        captured = set()
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= N and 1 <= nc <= N:
                if (nr, nc) in opp_stones_set if my_turn else (nr, nc) in my_stones_set:
                    group = find_group(nr, nc, opp_stones_set if my_turn else my_stones_set,
                                       my_stones_set if my_turn else opp_stones_set)
                    if not liberties(group, opp_stones_set if my_turn else my_stones_set,
                                     my_stones_set if my_turn else opp_stones_set):
                        captured.update(group)
        # Remove temp stone
        if my_turn:
            my_stones_set.remove((r, c))
        else:
            opp_stones_set.remove((r, c))
        return captured
    
    # Helper: is move legal (no suicide, respects ko)
    def is_legal(r, c, my_stones_set, opp_stones_set, ko_point=None):
        if (r, c) in my_stones_set or (r, c) in opp_stones_set:
            return False
        # Check suicide
        temp_my = set(my_stones_set)
        temp_my.add((r, c))
        captures = get_captures(r, c, True, temp_my, set(opp_stones_set))
        # If captures, always legal
        if captures:
            return True
        # Otherwise, must have liberty
        if liberties({(r, c)}, temp_my, opp_stones_set):
            return True
        return False
    
    # All legal moves
    legal_moves = []
    urgent_moves = []
    for r in range(1, N+1):
        for c in range(1, N+1):
            if is_legal(r, c, my_stones, opp_stones, None):
                legal_moves.append((r, c))
                # Urgent: atari on opponent group
                temp_my = set(my_stones)
                temp_my.add((r, c))
                caps = get_captures(r, c, True, temp_my, set(opp_stones))
                if caps:
                    urgent_moves.append((r, c))
    if not legal_moves:
        return (0, 0)
    
    # If urgent moves exist, pick one capturing largest group
    if urgent_moves and len(my_stones) + len(opp_stones) < N*N*0.7:
        best_cap_size = -1
        best_urgent = urgent_moves[0]
        for (r, c) in urgent_moves:
            temp_my = set(my_stones)
            temp_my.add((r, c))
            caps = get_captures(r, c, True, temp_my, set(opp_stones))
            if len(caps) > best_cap_size:
                best_cap_size = len(caps)
                best_urgent = (r, c)
        return best_urgent
    
    # Early game: prefer corners and sides
    move_count = len(my_stones) + len(opp_stones)
    if move_count < 40:
        corners = [(1,1), (1,19), (19,1), (19,19)]
        for cr, cc in corners:
            if (cr, cc) in legal_moves:
                return (cr, cc)
        side_points = [(1, c) for c in range(2, 19)] + [(19, c) for c in range(2, 19)] + \
                      [(r, 1) for r in range(2, 19)] + [(r, 19) for r in range(2, 19)]
        random.shuffle(side_points)
        for sr, sc in side_points:
            if (sr, sc) in legal_moves:
                return (sr, sc)
    
    # Simple MCTS
    SIM_LIMIT = 50
    wins = defaultdict(int)
    plays = defaultdict(int)
    
    # Playout function
    def playout(board_my, board_opp, move_sequence):
        bmy = set(board_my)
        bopp = set(board_opp)
        turn = True  # True for me
        local_moves = move_sequence[:]
        for _ in range(20):  # limit playout length
            lm = [(r, c) for r in range(1, N+1) for c in range(1, N+1) if is_legal(r, c, bmy, bopp)]
            if not lm:
                break
            mv = random.choice(lm)
            local_moves.append(mv)
            if turn:
                bmy.add(mv)
                caps = get_captures(mv[0], mv[1], True, bmy, bopp)
                for cap in caps:
                    bopp.remove(cap)
            else:
                bopp.add(mv)
                caps = get_captures(mv[0], mv[1], False, bopp, bmy)
                for cap in caps:
                    bmy.remove(cap)
            turn = not turn
        # Score: stone difference
        return len(bmy) - len(bopp)
    
    # Run simulations
    for _ in range(SIM_LIMIT):
        # Pick move by UCB
        log_total = math.log(sum(plays.values()) + 1)
        best_ucb = -float('inf')
        best_move = None
        for mv in legal_moves:
            if plays[mv] == 0:
                ucb = 1e5 + random.random()  # exploration bonus
            else:
                ucb = wins[mv]/plays[mv] + 2.0*math.sqrt(log_total/plays[mv])
            if ucb > best_ucb:
                best_ucb = ucb
                best_move = mv
        if best_move is None:
            best_move = random.choice(legal_moves)
        
        # Simulate
        res = playout(my_stones, opp_stones, [best_move])
        wins[best_move] += (res > 0)
        plays[best_move] += 1
        
        if time.time() - start_time > 0.9:
            break
    
    # Choose move with highest win rate
    if plays:
        best = max(legal_moves, key=lambda m: (wins[m]/(plays[m]+1e-5)))
        return best
    
    # Fallback
    return random.choice(legal_moves)
