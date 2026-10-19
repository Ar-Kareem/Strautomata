
import numpy as np

def policy(board) -> str:
    """
    Main policy function for Amazons game.
    Returns the best move in the required format.
    """
    moves = generate_all_legal_moves(board, 1)
    
    if not moves:
        # Fallback - should not happen in valid game states
        # Return any syntactically valid move
        return "0,0:0,0:0,0"
    
    # Use minimax with alpha-beta pruning
    best_move = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    for move in moves:
        new_board = apply_move(board, move, 1)
        score = minimax(new_board, 1, False, alpha, beta)
        
        if score > best_score:
            best_score = score
            best_move = move
        
        alpha = max(alpha, best_score)
    
    if best_move is None:
        best_move = moves[0]
    
    return format_move(best_move)

def generate_all_legal_moves(board, player):
    """Generate all legal moves for the given player."""
    moves = []
    amazons = np.argwhere(board == player)
    
    for amazon in amazons:
        from_pos = tuple(amazon)
        # Get all valid destinations for this amazon
        destinations = get_valid_moves(board, from_pos)
        
        for to_pos in destinations:
            # Temporarily move the amazon
            temp_board = board.copy()
            temp_board[from_pos] = 0
            temp_board[to_pos] = player
            
            # Get all valid arrow positions
            arrow_positions = get_valid_moves(temp_board, to_pos)
            
            for arrow_pos in arrow_positions:
                moves.append((from_pos, to_pos, arrow_pos))
    
    return moves

def get_valid_moves(board, pos):
    """Get all valid queen-like moves from a position."""
    valid = []
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for dr, dc in directions:
        for dist in range(1, 6):
            nr, nc = pos[0] + dr * dist, pos[1] + dc * dist
            
            if not (0 <= nr < 6 and 0 <= nc < 6):
                break
            
            if board[nr, nc] != 0:
                break
            
            valid.append((nr, nc))
    
    return valid

def apply_move(board, move, player):
    """Apply a move and return the new board state."""
    new_board = board.copy()
    from_pos, to_pos, arrow_pos = move
    
    new_board[from_pos] = 0
    new_board[to_pos] = player
    new_board[arrow_pos] = -1
    
    return new_board

def format_move(move):
    """Format move tuple into required string format."""
    from_pos, to_pos, arrow_pos = move
    return f"{from_pos[0]},{from_pos[1]}:{to_pos[0]},{to_pos[1]}:{arrow_pos[0]},{arrow_pos[1]}"

def evaluate_board(board, player):
    """Evaluate the board position for the given player."""
    opponent = 3 - player
    
    # Count mobility (number of legal moves)
    player_moves = len(generate_all_legal_moves(board, player))
    opponent_moves = len(generate_all_legal_moves(board, opponent))
    
    # If someone has no moves, it's game over
    if player_moves == 0:
        return -10000
    if opponent_moves == 0:
        return 10000
    
    # Territory control using flood fill
    player_territory = count_territory(board, player)
    opponent_territory = count_territory(board, opponent)
    
    # Mobility is key
    mobility_score = (player_moves - opponent_moves) * 10
    territory_score = (player_territory - opponent_territory) * 5
    
    return mobility_score + territory_score

def count_territory(board, player):
    """Count squares reachable by player's amazons."""
    reachable = set()
    amazons = np.argwhere(board == player)
    
    for amazon in amazons:
        pos = tuple(amazon)
        visited = flood_fill(board, pos)
        reachable.update(visited)
    
    return len(reachable)

def flood_fill(board, start):
    """Flood fill to find all reachable squares."""
    visited = set()
    stack = [start]
    
    while stack:
        pos = stack.pop()
        if pos in visited:
            continue
        
        visited.add(pos)
        
        # Check all 8 directions
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                nr, nc = pos[0] + dr, pos[1] + dc
                
                if 0 <= nr < 6 and 0 <= nc < 6:
                    if board[nr, nc] == 0 and (nr, nc) not in visited:
                        stack.append((nr, nc))
    
    return visited

def minimax(board, depth, is_maximizing, alpha, beta):
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate_board(board, 1)
    
    if is_maximizing:
        max_eval = float('-inf')
        moves = generate_all_legal_moves(board, 1)
        
        if not moves:
            return -10000
        
        for move in moves[:20]:  # Limit branching factor
            new_board = apply_move(board, move, 1)
            eval_score = minimax(new_board, depth - 1, False, alpha, beta)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        return max_eval
    else:
        min_eval = float('inf')
        moves = generate_all_legal_moves(board, 2)
        
        if not moves:
            return 10000
        
        for move in moves[:20]:  # Limit branching factor
            new_board = apply_move(board, move, 2)
            eval_score = minimax(new_board, depth - 1, True, alpha, beta)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        return min_eval
