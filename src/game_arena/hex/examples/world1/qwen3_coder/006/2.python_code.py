
import heapq
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board_size = 11
    my_stones = set(me)
    opp_stones = set(opp)
    all_stones = my_stones | opp_stones

    def get_neighbors(r, c):
        # Hexagonal neighbors for a flat-topped hex grid
        # (r-1,c-1) (r-1,c) 
        # (r,c-1)  (r,c)   (r,c+1)
        # (r+1,c)   (r+1,c+1)
        neighbors = [
            (r-1, c-1), (r-1, c),
            (r, c-1), (r, c+1),
            (r+1, c), (r+1, c+1)
        ]
        return [(nr, nc) for nr, nc in neighbors if 0 <= nr < board_size and 0 <= nc < board_size]

    def is_winning_move_for_black(r):
        return r == 0 or r == board_size - 1

    def is_winning_move_for_white(c):
        return c == 0 or c == board_size - 1

    def evaluate_move(r, c):
        # Evaluate a move based on strategic value
        score = 0
        neighbors = get_neighbors(r, c)
        
        # Count adjacent friendly and opponent stones
        friendly_adjacent = sum(1 for nr, nc in neighbors if (nr, nc) in my_stones)
        opponent_adjacent = sum(1 for nr, nc in neighbors if (nr, nc) in opp_stones)
        
        # Prefer moves that connect to our own stones
        score += friendly_adjacent * 2
        
        # Preference for moves that block opponent
        score += opponent_adjacent * 1.5
        
        # Distance-based scoring to goal
        if color == 'b':  # Black wants to connect top and bottom
            # Prefer moves closer to center vertically
            distance_to_center = abs(r - 5)
            score -= distance_to_center * 0.1
            # Bonus for moves near top or bottom if they connect well
            if r == 0 or r == 10:
                score += 3
        else:  # White wants to connect left and right
            # Prefer moves closer to center horizontally
            distance_to_center = abs(c - 5)
            score -= distance_to_center * 0.1
            # Bonus for moves near sides if they connect well
            if c == 0 or c == 10:
                score += 3
                
        # Bonus for moves that connect to multiple groups
        connected_groups = 0
        visited_neighbors = set()
        for nr, nc in neighbors:
            if (nr, nc) in my_stones and (nr, nc) not in visited_neighbors:
                # BFS to find all stones in this group
                group = set()
                q = deque([(nr, nc)])
                while q:
                    gr, gc = q.popleft()
                    if (gr, gc) in group or (gr, gc) not in my_stones:
                        continue
                    group.add((gr, gc))
                    visited_neighbors.add((gr, gc))
                    for gnr, gnc in get_neighbors(gr, gc):
                        if (gnr, gnc) in my_stones and (gnr, gnc) not in group:
                            q.append((gnr, gnc))
                connected_groups += 1
        score += (connected_groups - 1) * 2  # Bonus for connecting groups
        
        return score

    def find_bridge_moves():
        # Look for bridge patterns that can be completed by placing a stone
        bridges = []
        for r, c in my_stones:
            # Bridge templates: patterns that can form a bridge connection
            # Pattern 1: One space away diagonally
            if color == 'b':
                # For black: try to find bridge that helps vertical connection
                candidates = [(r-1, c-2), (r-1, c+1), (r+1, c-1), (r+1, c+2)]
            else:
                # For white: try to find bridge that helps horizontal connection
                candidates = [(r-2, c-1), (r-1, c+1), (r+1, c-1), (r+2, c+1)]
            
            for nr, nc in candidates:
                if 0 <= nr < board_size and 0 <= nc < board_size:
                    if (nr, nc) not in all_stones:
                        bridges.append((nr, nc))
        return bridges

    # Try to find immediate win or block immediate threat
    def check_immediate_threat():
        # Simple heuristic: prioritize moves that could complete a connection quickly
        best_moves = []
        for r in range(board_size):
            for c in range(board_size):
                if (r, c) not in all_stones:
                    score = evaluate_move(r, c)
                    heapq.heappush(best_moves, (-score, (r, c)))
                    if len(best_moves) > 20:  # Keep top 20
                        heapq.heappop(best_moves)
        
        if best_moves:
            return heapq.heappop(best_moves)[1]
        return None

    # Try bridge moves first as they are strategically valuable
    bridge_moves = find_bridge_moves()
    evaluated_bridges = []
    for r, c in bridge_moves:
        if (r, c) not in all_stones:
            score = evaluate_move(r, c)
            heapq.heappush(evaluated_bridges, (-score, (r, c)))
    
    if evaluated_bridges:
        return heapq.heappop(evaluated_bridges)[1]

    # If no special moves found, use standard evaluation
    best_move = None
    best_score = float('-inf')
    
    # Consider center area first for better connectivity
    center_positions = [(r, c) for r in range(3, 8) for c in range(3, 8)]
    all_positions = center_positions + [(r, c) for r in range(board_size) for c in range(board_size) if (r, c) not in center_positions]
    
    for r, c in all_positions:
        if (r, c) not in all_stones:
            score = evaluate_move(r, c)
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    # Fallback: pick any valid move
    if best_move is None:
        for r in range(board_size):
            for c in range(board_size):
                if (r, c) not in all_stones:
                    return (r, c)
    
    return best_move
