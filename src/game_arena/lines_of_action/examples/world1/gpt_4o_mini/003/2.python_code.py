
import numpy as np

def get_legal_moves(board):
    moves = []
    rows, cols = len(board), len(board[0])
    
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 1:
                # Count our pieces in the row, column and diagonals.
                directions = [
                    (0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)
                ]
                piece_count = sum(board[rr][cc] == 1 for rr in range(8) for cc in range(8))
                
                for dr, dc in directions:
                    distance = 0
                    current_r, current_c = r, c

                    # Move in the direction until out of bounds or blocked
                    while 0 <= current_r < rows and 0 <= current_c < cols:
                        if board[current_r][current_c] == -1:  # Can't jump over opponent pieces
                            break
                        if board[current_r][current_c] == 0 or board[current_r][current_c] == 1:
                            distance += 1
                        current_r += dr
                        current_c += dc
                        
                    # Now create moves by checking all squares within `distance`.
                    for step in range(1, distance + 1):
                        target_r = r + dr * step
                        target_c = c + dc * step
                        if 0 <= target_r < rows and 0 <= target_c < cols:
                            if board[target_r][target_c] == 0 or board[target_r][target_c] == -1:
                                moves.append(f"{r},{c}:{target_r},{target_c}")
    
    return moves

def evaluate_move(board, move):
    # Make a hypothetical move
    src, dst = move.split(':')
    from_row, from_col = map(int, src.split(','))
    to_row, to_col = map(int, dst.split(','))

    # Execute move temporarily
    new_board = np.copy(board)
    new_board[to_row][to_col] = 1  # Move player's piece to the target
    new_board[from_row][from_col] = 0  # Remove piece from from position

    # Evaluation could involve counting the number of groups, pieces captured, etc.
    score = 0
    score += check_connected(new_board)
    score -= opponent_strength(new_board)

    return score

def check_connected(board):
    rows, cols = len(board), len(board[0])
    visited = set()
    
    def dfs(r, c):
        stack = [(r, c)]
        count = 0
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) not in visited:
                visited.add((cr, cc))
                count += 1
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        if abs(dr) != abs(dc):  # Only straight directions
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                                if board[nr][nc] == 1:
                                    stack.append((nr, nc))
        return count
    
    connected_components = 0
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 1 and (r, c) not in visited:
                dfs(r, c)
                connected_components += 1
    
    return connected_components

def opponent_strength(board):
    # Returns the strength of the opponent. Could be number of unconnected pieces, etc.
    return np.sum(board == -1)  # Simplistic: number of opponent pieces as a threat.

def policy(board) -> str:
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return ""
    
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        score = evaluate_move(board, move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
