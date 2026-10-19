
import numpy as np

def policy(board) -> str:
    """
    Returns the best move for the current player (player 1)
    """
    legal_moves = get_all_legal_moves(board, 1)
    
    if not legal_moves:
        return "0,0:0,0:0,0"
    
    if len(legal_moves) == 1:
        return format_move(legal_moves[0])
    
    best_move = None
    best_score = float('-inf')
    
    use_minimax = len(legal_moves) <= 80
    
    for move in legal_moves:
        new_board = apply_move(board, move, 1)
        
        if use_minimax:
            opp_moves = get_all_legal_moves(new_board, 2)
            
            if not opp_moves:
                return format_move(move)
            
            opp_moves_to_check = opp_moves[:min(40, len(opp_moves))]
            
            worst_score = float('inf')
            for opp_move in opp_moves_to_check:
                opp_board = apply_move(new_board, opp_move, 2)
                score = evaluate_position(opp_board, 1)
                worst_score = min(worst_score, score)
            
            score = worst_score
        else:
            score = evaluate_position(new_board, 1)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move)

def get_all_legal_moves(board, player):
    """Get all legal moves for a player"""
    moves = []
    amazons = np.argwhere(board == player)
    
    for amazon in amazons:
        from_pos = tuple(amazon)
        reachable = get_reachable_positions(board, from_pos)
        
        for to_pos in reachable:
            temp_board = board.copy()
            temp_board[from_pos] = 0
            temp_board[to_pos] = player
            
            arrow_positions = get_reachable_positions(temp_board, to_pos)
            
            for arrow_pos in arrow_positions:
                moves.append((from_pos, to_pos, arrow_pos))
    
    return moves

def get_reachable_positions(board, pos):
    """Get all positions reachable from pos via queen-like moves"""
    positions = []
    row, col = pos
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), 
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 6:
            if board[r, c] != 0:
                break
            positions.append((r, c))
            r += dr
            c += dc
    
    return positions

def apply_move(board, move, player):
    """Apply a move to the board and return a new board"""
    from_pos, to_pos, arrow_pos = move
    new_board = board.copy()
    new_board[from_pos] = 0
    new_board[to_pos] = player
    new_board[arrow_pos] = -1
    return new_board

def format_move(move):
    """Format move tuple as a string"""
    from_pos, to_pos, arrow_pos = move
    return f"{from_pos[0]},{from_pos[1]}:{to_pos[0]},{to_pos[1]}:{arrow_pos[0]},{arrow_pos[1]}"

def evaluate_position(board, player):
    """Evaluate the board position for the given player"""
    opponent = 3 - player
    
    my_mobility = count_mobility(board, player)
    opp_mobility = count_mobility(board, opponent)
    
    if opp_mobility == 0:
        return 1000000
    if my_mobility == 0:
        return -1000000
    
    my_territory = count_territory(board, player)
    opp_territory = count_territory(board, opponent)
    
    mobility_diff = my_mobility - opp_mobility
    territory_diff = my_territory - opp_territory
    
    score = mobility_diff * 10 + territory_diff
    
    return score

def count_mobility(board, player):
    """Count squares directly reachable by player's amazons"""
    amazons = np.argwhere(board == player)
    total = 0
    
    for amazon in amazons:
        pos = tuple(amazon)
        reachable = get_reachable_positions(board, pos)
        total += len(reachable)
    
    return total

def count_territory(board, player):
    """Count unique squares reachable via flood fill"""
    visited = set()
    amazons = np.argwhere(board == player)
    
    for amazon in amazons:
        pos = tuple(amazon)
        flood_fill_set(board, pos, visited)
    
    return len(visited) - len(amazons)

def flood_fill_set(board, start, visited):
    """Flood fill to find connected empty squares"""
    stack = [start]
    
    while stack:
        pos = stack.pop()
        
        if pos in visited:
            continue
        
        row, col = pos
        
        if board[row, col] != 0 and pos != start:
            continue
        
        visited.add(pos)
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), 
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 6 and 0 <= c < 6:
                stack.append((r, c))
