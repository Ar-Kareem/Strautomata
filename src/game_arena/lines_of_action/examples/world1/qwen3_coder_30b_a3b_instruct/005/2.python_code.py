
import numpy as np
from collections import deque

def policy(board):
    # Convert to numpy array for easier handling
    board = np.array(board)
    player = 1  # AI is player 1
    
    def get_all_pieces(board, player):
        """Get all positions of the specified player's pieces"""
        positions = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    positions.append((r, c))
        return positions
    
    def get_legal_moves(board, player):
        """Generate all legal moves for the current player"""
        moves = []
        pieces = get_all_pieces(board, player)
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for r, c in pieces:
            # For each direction, try all possible distances
            for dr, dc in directions:
                # Determine how many pieces are in this line
                line_count = 0
                # Count pieces in the + direction
                nr, nc = r + dr, c + dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc] != 0:
                        line_count += 1
                    nr, nc = nr + dr, nc + dc
                # Count pieces in the - direction
                nr, nc = r - dr, c - dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc] != 0:
                        line_count += 1
                    nr, nc = nr - dr, nc - dc
                line_count += 1  # Add the piece itself
                
                # Try all possible distances up to the line count
                for distance in range(1, line_count + 1):
                    target_r = r + dr * distance
                    target_c = c + dc * distance
                    if 0 <= target_r < 8 and 0 <= target_c < 8:
                        # Check if path is clear
                        is_valid = True
                        temp_r, temp_c = r + dr, c + dc
                        for _ in range(distance - 1):
                            if 0 <= temp_r < 8 and 0 <= temp_c < 8:
                                if board[temp_r][temp_c] == -player:
                                    is_valid = False
                                    break
                            temp_r += dr
                            temp_c += dc
                        if is_valid and board[target_r][target_c] != player:
                            moves.append((r, c, target_r, target_c))
        return moves
    
    def is_connected(board, player):
        """Check if there's only one connected component of player pieces"""
        pieces = get_all_pieces(board, player)
        if len(pieces) <= 1:
            return True
        
        visited = set()
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        def bfs(start_r, start_c):
            queue = deque([(start_r, start_c)])
            visited.add((start_r, start_c))
            count = 1
            
            while queue:
                r, c = queue.popleft()
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < 8 and 0 <= nc < 8 and 
                        (nr, nc) not in visited and 
                        board[nr][nc] == player):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        count += 1
            return count
        
        # Start BFS from first piece
        first_piece = pieces[0]
        connected_count = bfs(first_piece[0], first_piece[1])
        return connected_count == len(pieces)
    
    def evaluate_board(board, player):
        """Evaluate the board state"""
        # Primary objective: maximally connected components (for AI)
        pieces = get_all_pieces(board, player)
        opponent_pieces = get_all_pieces(board, -player)
        
        # Count connected components
        visited = set()
        components = 0
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for r, c in pieces:
            if (r, c) not in visited:
                queue = deque([(r, c)])
                visited.add((r, c))
                components += 1
                while queue:
                    cr, cc = queue.popleft()
                    for dr, dc in directions:
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < 8 and 0 <= nc < 8 and 
                            (nr, nc) not in visited and 
                            board[nr][nc] == player):
                            visited.add((nr, nc))
                            queue.append((nr, nc))
        
        # Evaluate connectivity (higher is better)
        connectivity_score = 0
        if components <= 1:
            connectivity_score = 100  # Perfectly connected
        else:
            connectivity_score = -components * 10  # Non-connected pieces are penalized
            
        # Number of pieces
        piece_count = len(pieces)
        opponent_count = len(opponent_pieces)
        
        # Center control
        center_count = 0
        center_positions = [(3,3), (3,4), (4,3), (4,4)]
        for r, c in center_positions:
            if board[r][c] == player:
                center_count += 1
                
        # Mobility - number of possible moves for player
        possible_moves = len(get_legal_moves(board, player))
        
        # Evaluation function: try to balance connectivity, pieces, mobility
        # Note: This is simplified. A more sophisticated version would use heuristics specific to Lines of Action
        score = 0
        score += connectivity_score
        score += piece_count * 20
        score += center_count * 15
        score += possible_moves * 5
        score -= opponent_count * 10  # Subtract opponent pieces
        
        return score
    
    def make_move(board, from_r, from_c, to_r, to_c):
        """Make a move and return new board"""
        new_board = board.copy()
        new_board[to_r][to_c] = new_board[from_r][from_c]
        new_board[from_r][from_c] = 0
        return new_board
    
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        """Minimax algorithm with alpha-beta pruning"""
        if depth == 0:
            return evaluate_board(board, player)
            
        legal_moves = get_legal_moves(board, player if maximizing_player else -player)
        
        if not legal_moves:
            return evaluate_board(board, player) - 1000 if maximizing_player else evaluate_board(board, player) + 1000
            
        if maximizing_player:
            max_eval = float('-inf')
            for from_r, from_c, to_r, to_c in legal_moves:
                new_board = make_move(board, from_r, from_c, to_r, to_c)
                eval_score = minimax(new_board, depth - 1, alpha, beta, False, player)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for from_r, from_c, to_r, to_c in legal_moves:
                new_board = make_move(board, from_r, from_c, to_r, to_c)
                eval_score = minimax(new_board, depth - 1, alpha, beta, True, player)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_eval
    
    def get_best_move(board, player):
        """Get the best move using minimax"""
        legal_moves = get_legal_moves(board, player)
        if not legal_moves:
            return None
            
        best_move = None
        best_score = float('-inf')
        
        for from_r, from_c, to_r, to_c in legal_moves:
            new_board = make_move(board, from_r, from_c, to_r, to_c)
            # Limit depth based on time constraints - try with depth 2 or 3
            score = minimax(new_board, 3, float('-inf'), float('inf'), False, player)
            if score > best_score:
                best_score = score
                best_move = (from_r, from_c, to_r, to_c)
                
        return best_move
    
    # Try to get the best move
    best_move = get_best_move(board, player)
    
    if best_move:
        from_r, from_c, to_r, to_c = best_move
        return f"{from_r},{from_c}:{to_r},{to_c}"
    else:
        # Fallback - return any valid move if no good options
        legal_moves = get_legal_moves(board, player)
        if legal_moves:
            from_r, from_c, to_r, to_c = legal_moves[0]
            return f"{from_r},{from_c}:{to_r},{to_c}"
        else:
            # No moves possible - illegal state, but just pick something
            for r in range(8):
                for c in range(8):
                    if board[r][c] == player:
                        # Look for any adjacent empty spot
                        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
                        for dr, dc in directions:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 0:
                                return f"{r},{c}:{nr},{nc}"
        return "0,0:1,1"  # At least return a valid result
