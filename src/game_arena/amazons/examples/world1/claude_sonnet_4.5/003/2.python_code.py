
import numpy as np
from collections import deque

def policy(board) -> str:
    """
    Amazons policy using mobility-based evaluation with territory control.
    """
    moves = generate_all_legal_moves(board, 1)
    
    if not moves:
        # Fallback - should not happen in valid game state
        return "0,0:0,0:0,0"
    
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        score = evaluate_move(board, move, 1)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def generate_all_legal_moves(board, player):
    """Generate all legal moves for the given player."""
    moves = []
    amazons = np.argwhere(board == player)
    
    for amazon in amazons:
        from_r, from_c = amazon
        # Get all reachable positions for this amazon
        reachable = get_reachable_squares(board, from_r, from_c)
        
        for to_r, to_c in reachable:
            # Simulate the move
            temp_board = board.copy()
            temp_board[from_r, from_c] = 0
            temp_board[to_r, to_c] = player
            
            # Get arrow positions from the new location
            arrow_positions = get_reachable_squares(temp_board, to_r, to_c)
            
            for arrow_r, arrow_c in arrow_positions:
                move_str = f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
                moves.append(move_str)
    
    return moves

def get_reachable_squares(board, row, col):
    """Get all squares reachable from (row, col) in queen-like moves."""
    reachable = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 6 and board[r, c] == 0:
            reachable.append((r, c))
            r += dr
            c += dc
    
    return reachable

def evaluate_move(board, move_str, player):
    """Evaluate a move by simulating it and calculating territory control."""
    parts = move_str.split(':')
    from_r, from_c = map(int, parts[0].split(','))
    to_r, to_c = map(int, parts[1].split(','))
    arrow_r, arrow_c = map(int, parts[2].split(','))
    
    # Simulate the move
    sim_board = board.copy()
    sim_board[from_r, from_c] = 0
    sim_board[to_r, to_c] = player
    sim_board[arrow_r, arrow_c] = -1
    
    # Evaluate the resulting position
    my_score = calculate_territory(sim_board, player)
    opp_score = calculate_territory(sim_board, 3 - player)
    
    return my_score - opp_score

def calculate_territory(board, player):
    """Calculate territory control using BFS from all amazons."""
    amazons = np.argwhere(board == player)
    visited = np.zeros((6, 6), dtype=bool)
    total_score = 0
    
    for amazon in amazons:
        start_r, start_c = amazon
        # BFS to find reachable squares with distance weighting
        queue = deque([(start_r, start_c, 0)])
        local_visited = set()
        
        while queue:
            r, c, dist = queue.popleft()
            
            if (r, c) in local_visited:
                continue
            local_visited.add((r, c))
            
            if not visited[r, c]:
                visited[r, c] = True
                # Weight closer squares more heavily
                total_score += max(1, 10 - dist)
            
            # Explore neighbors
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (0 <= nr < 6 and 0 <= nc < 6 and 
                    board[nr, nc] == 0 and 
                    (nr, nc) not in local_visited and
                    dist < 10):  # Limit search depth
                    queue.append((nr, nc, dist + 1))
    
    return total_score
