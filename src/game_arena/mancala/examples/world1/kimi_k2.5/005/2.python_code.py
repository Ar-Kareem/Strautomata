
import time
from typing import List, Tuple

def policy(you: List[int], opponent: List[int]) -> int:
    # Board layout: 0-5=my houses, 6=my store, 7-12=opp houses, 13=opp store
    board = you[:6] + [you[6]] + opponent[:6] + [opponent[6]]
    
    TIME_LIMIT = 0.9
    start_time = time.time()
    
    # Player 1 (opponent) circle mapping: their store 13 is at circle index 6
    p1_idx_map = {7:0, 8:1, 9:2, 10:3, 11:4, 12:5, 13:6, 0:7, 1:8, 2:9, 3:10, 4:11, 5:12}
    
    def next_pit(pos: int, player: int) -> int:
        """Next pit in sowing order for given player."""
        if player == 0:
            return 0 if pos == 12 else pos + 1
        else:
            if pos == 5:
                return 7
            if pos == 13:
                return 0
            return pos + 1
    
    def make_move(b: List[int], player: int, house: int) -> Tuple[List[int], int]:
        """Execute move and return (new_board, next_player)."""
        nb = b.copy()
        seeds = nb[house]
        nb[house] = 0
        pos = house
        while seeds > 0:
            pos = next_pit(pos, player)
            nb[pos] += 1
            seeds -= 1
        
        # Extra move if landed in own store
        if player == 0 and pos == 6:
            return nb, player
        if player == 1 and pos == 13:
            return nb, player
        
        # Capture rule
        if player == 0:
            if 0 <= pos <= 5 and nb[pos] == 1:
                opp_pos = 12 - pos
                if nb[opp_pos] > 0:
                    nb[6] += nb[opp_pos] + 1
                    nb[opp_pos] = 0
                    nb[pos] = 0
        else:
            if 7 <= pos <= 12 and nb[pos] == 1:
                opp_pos = 12 - pos
                if nb[opp_pos] > 0:
                    nb[13] += nb[opp_pos] + 1
                    nb[opp_pos] = 0
                    nb[pos] = 0
        
        return nb, 1 - player
    
    def is_extra_move(b: List[int], player: int, house: int) -> bool:
        """Check if move results in a free turn."""
        seeds = b[house]
        if player == 0:
            return (house + seeds) % 13 == 6
        else:
            circle_idx = p1_idx_map[house]
            return (circle_idx + seeds) % 13 == 6
    
    def get_legal_moves(b: List[int], player: int) -> List[int]:
        if player == 0:
            return [i for i in range(6) if b[i] > 0]
        else:
            return [i for i in range(7, 13) if b[i] > 0]
    
    def heuristic(b: List[int]) -> int:
        """Static evaluation from perspective of player 0."""
        # Store difference is dominant
        score = (b[6] - b[13]) * 100
        # Seed difference (potential)
        my_seeds = sum(b[0:6])
        opp_seeds = sum(b[7:13])
        score += (my_seeds - opp_seeds) * 5
        # Potential captures (empty houses opposite seeds)
        for i in range(6):
            if b[i] == 0 and b[12-i] > 0:
                score += b[12-i] * 2
        return score
    
    def terminal_value(b: List[int], player: int) -> int:
        """Value when player has no moves (game ends)."""
        if player == 0:
            my_score = b[6]
            opp_score = b[13] + sum(b[7:13])
        else:
            my_score = b[6] + sum(b[0:6])
            opp_score = b[13]
        
        if my_score > opp_score:
            return 100000
        elif my_score < opp_score:
            return -100000
        return 0
    
    # Transposition table
    cache = {}
    best_move = [0]
    current_depth = [0]
    
    def search(b: List[int], player: int, depth: int, alpha: float, beta: float) -> float:
        # Time cutoff
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError()
        
        # Transposition lookup
        key = (tuple(b), player, depth)
        if key in cache:
            return cache[key]
        
        moves = get_legal_moves(b, player)
        if not moves:
            val = terminal_value(b, player)
            cache[key] = val
            return val
        
        if depth == 0:
            val = heuristic(b)
            cache[key] = val
            return val
        
        # Move ordering: extra moves first, then larger seeds
        moves.sort(key=lambda h: (0 if is_extra_move(b, player, h) else 1, -b[h]))
        
        if player == 0:
            value = -float('inf')
            for house in moves:
                nb, next_p = make_move(b, player, house)
                val = search(nb, next_p, depth - 1, alpha, beta)
                if val > value:
                    value = val
                    if depth == current_depth[0]:
                        best_move[0] = house
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            cache[key] = value
            return value
        else:
            value = float('inf')
            for house in moves:
                nb, next_p = make_move(b, player, house)
                val = search(nb, next_p, depth - 1, alpha, beta)
                if val < value:
                    value = val
                beta = min(beta, value)
                if alpha >= beta:
                    break
            cache[key] = value
            return value
    
    legal = get_legal_moves(board, 0)
    if len(legal) == 1:
        return legal[0]
    
    # Iterative deepening
    try:
        for d in range(1, 20):
            current_depth[0] = d
            search(board, 0, d, -float('inf'), float('inf'))
    except TimeoutError:
        pass
    
    return best_move[0]
