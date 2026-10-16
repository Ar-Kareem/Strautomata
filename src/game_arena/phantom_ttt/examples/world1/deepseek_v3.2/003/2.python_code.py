
import random
import math
import time
from collections import defaultdict

# Global timing for move selection
START_TIME = None
TIME_LIMIT = 0.95  # Use 95% of available time

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    global START_TIME
    START_TIME = time.time()
    
    # Convert board to tuple for hashing
    board_tuple = tuple(tuple(row) for row in board)
    
    # Filter moves to avoid known occupied cells (where we have 1)
    candidate_moves = []
    for move in legal_moves:
        r, c = move // 3, move % 3
        if board[r][c] != 1:  # Don't try cells we already own
            candidate_moves.append((r, c))
    
    if not candidate_moves:
        # Fallback: pick first legal move
        move = legal_moves[0]
        return (move // 3, move % 3)
    
    # Quick wins: if we can complete a line, do it
    winning_move = find_winning_move(board_tuple, candidate_moves)
    if winning_move:
        return winning_move
    
    # Early game: use opening book
    if sum(row.count(1) for row in board) <= 2:
        best_move = opening_move(board_tuple, candidate_moves)
        if best_move:
            return best_move
    
    # Main search with belief state
    best_move = None
    best_score = -float('inf')
    
    # Generate possible opponent boards based on our observations
    possible_boards = generate_possible_boards(board_tuple)
    
    # Progressive deepening
    depth = 2
    while time_left():
        move_scores = {}
        
        for move in candidate_moves:
            # Quick prune: if this move is clearly bad, skip
            if not is_promising_move(board_tuple, move):
                continue
                
            score = evaluate_move(board_tuple, move, possible_boards, depth)
            move_scores[move] = score
            
            if score > best_score:
                best_score = score
                best_move = move
        
        depth += 1
        if depth > 5 or not time_left():
            break
    
    # If search didn't find anything (shouldn't happen), use heuristic
    if best_move is None:
        best_move = heuristic_best_move(board_tuple, candidate_moves)
    
    return best_move

def time_left():
    """Check if we have time left for more computation."""
    global START_TIME
    return (time.time() - START_TIME) < TIME_LIMIT

def find_winning_move(board, candidate_moves):
    """Check if any move immediately wins."""
    for r, c in candidate_moves:
        # Test if placing at (r, c) would complete a line
        test_board = [list(row) for row in board]
        test_board[r][c] = 1
        
        # Check rows
        for row in test_board:
            if row.count(1) == 3:
                return (r, c)
        
        # Check columns
        for col in range(3):
            if test_board[0][col] == 1 and test_board[1][col] == 1 and test_board[2][col] == 1:
                return (r, c)
        
        # Check diagonals
        if test_board[0][0] == 1 and test_board[1][1] == 1 and test_board[2][2] == 1:
            return (r, c)
        if test_board[0][2] == 1 and test_board[1][1] == 1 and test_board[2][0] == 1:
            return (r, c)
    
    return None

def opening_move(board, candidate_moves):
    """Select good opening moves."""
    # Center is best
    if (1, 1) in candidate_moves and board[1][1] == 0:
        return (1, 1)
    
    # Then corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if corner in candidate_moves and board[corner[0]][corner[1]] == 0:
            return corner
    
    # Then edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for edge in edges:
        if edge in candidate_moves and board[edge[0]][edge[1]] == 0:
            return edge
    
    return None

def generate_possible_boards(board):
    """Generate boards consistent with observations."""
    possible = [board]
    
    # For each 0 cell, it could actually contain opponent mark
    # We generate variations where some 0s become -1 (opponent)
    zeros = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                zeros.append((r, c))
    
    # Limit number of variations to avoid explosion
    max_variations = min(20, 2 ** len(zeros))
    for _ in range(max_variations - 1):
        new_board = [list(row) for row in board]
        # Randomly assign some zeros to opponent
        for r, c in zeros:
            if random.random() < 0.3:  # 30% chance to be opponent
                new_board[r][c] = -1
        possible.append(tuple(tuple(row) for row in new_board))
    
    return list(set(possible))  # Remove duplicates

def is_promising_move(board, move):
    """Quick check if a move is worth exploring."""
    r, c = move
    
    # Check if move creates or extends a line
    # Check row
    row = board[r]
    if row.count(1) > 0:
        return True
    
    # Check column
    col = [board[i][c] for i in range(3)]
    if col.count(1) > 0:
        return True
    
    # Check diagonals if applicable
    if r == c:  # Main diagonal
        diag = [board[i][i] for i in range(3)]
        if diag.count(1) > 0:
            return True
    
    if r + c == 2:  # Anti-diagonal
        adiag = [board[i][2-i] for i in range(3)]
        if adiag.count(1) > 0:
            return True
    
    # Otherwise not promising
    return False

def evaluate_move(board, move, possible_boards, depth):
    """Evaluate a move using minimax over possible boards."""
    r, c = move
    scores = []
    
    for opp_board in possible_boards:
        # If cell is actually occupied by opponent in this scenario, skip
        if opp_board[r][c] == -1:
            scores.append(-10)  # Very bad outcome
            continue
        
        # Create new board state
        new_board = [list(row) for row in board]
        new_board[r][c] = 1
        new_board_tuple = tuple(tuple(row) for row in new_board)
        
        # Evaluate recursively
        score = minimax(new_board_tuple, depth-1, False, opp_board, -float('inf'), float('inf'))
        scores.append(score)
    
    # Return worst-case (maximin) or average score
    return min(scores)  # Conservative: maximize worst-case

def minimax(board, depth, is_maximizing, opp_board, alpha, beta):
    """Minimax search with alpha-beta pruning."""
    if depth == 0 or game_over(board, opp_board):
        return evaluate_position(board, opp_board)
    
    if is_maximizing:
        max_eval = -float('inf')
        # Our possible moves
        moves = []
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0 and (opp_board is None or opp_board[r][c] != -1):
                    moves.append((r, c))
        
        if not moves:
            return evaluate_position(board, opp_board)
        
        for r, c in moves:
            new_board = [list(row) for row in board]
            new_board[r][c] = 1
            eval_score = minimax(tuple(tuple(row) for row in new_board), 
                               depth-1, False, opp_board, alpha, beta)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        # Opponent's turn - they try to minimize our score
        min_eval = float('inf')
        # Opponent's possible moves (in their board view)
        moves = []
        for r in range(3):
            for c in range(3):
                if opp_board[r][c] == 0:  # Empty in opponent's view
                    moves.append((r, c))
        
        if not moves:
            return evaluate_position(board, opp_board)
        
        for r, c in moves:
            # Opponent places their mark
            new_opp_board = [list(row) for row in opp_board]
            new_opp_board[r][c] = -1
            # Update our board if opponent claimed a cell we thought was empty
            new_board = [list(row) for row in board]
            if new_board[r][c] == 0:
                new_board[r][c] = -1  # Now we know opponent is there
            
            eval_score = minimax(tuple(tuple(row) for row in new_board), 
                               depth-1, True, 
                               tuple(tuple(row) for row in new_opp_board), 
                               alpha, beta)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def game_over(board, opp_board):
    """Check if game is over in any scenario."""
    # Check if we won
    for i in range(3):
        if board[i][0] == 1 and board[i][1] == 1 and board[i][2] == 1:
            return True
        if board[0][i] == 1 and board[1][i] == 1 and board[2][i] == 1:
            return True
    
    if board[0][0] == 1 and board[1][1] == 1 and board[2][2] == 1:
        return True
    if board[0][2] == 1 and board[1][1] == 1 and board[2][0] == 1:
        return True
    
    # Check if opponent won (worst case)
    if opp_board:
        for i in range(3):
            if opp_board[i][0] == -1 and opp_board[i][1] == -1 and opp_board[i][2] == -1:
                return True
            if opp_board[0][i] == -1 and opp_board[1][i] == -1 and opp_board[2][i] == -1:
                return True
        
        if opp_board[0][0] == -1 and opp_board[1][1] == -1 and opp_board[2][2] == -1:
            return True
        if opp_board[0][2] == -1 and opp_board[1][1] == -1 and opp_board[2][0] == -1:
            return True
    
    # Check if board is full
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return False
    
    return True

def evaluate_position(board, opp_board):
    """Heuristic evaluation of board position."""
    score = 0
    
    # Points for our lines
    for i in range(3):
        # Rows
        row = board[i]
        ours = row.count(1)
        if ours == 3:
            return 1000  # Winning position
        elif ours == 2:
            score += 10
        elif ours == 1:
            score += 1
        
        # Columns
        col = [board[j][i] for j in range(3)]
        ours = col.count(1)
        if ours == 3:
            return 1000
        elif ours == 2:
            score += 10
        elif ours == 1:
            score += 1
    
    # Diagonals
    diag1 = [board[i][i] for i in range(3)]
    diag2 = [board[i][2-i] for i in range(3)]
    
    for diag in [diag1, diag2]:
        ours = diag.count(1)
        if ours == 3:
            return 1000
        elif ours == 2:
            score += 10
        elif ours == 1:
            score += 1
    
    # Penalize opponent's potential lines (worst case)
    if opp_board:
        for i in range(3):
            row = opp_board[i]
            if row.count(-1) == 2 and row.count(0) == 1:
                score -= 8
            elif row.count(-1) == 1:
                score -= 1
            
            col = [opp_board[j][i] for j in range(3)]
            if col.count(-1) == 2 and col.count(0) == 1:
                score -= 8
            elif col.count(-1) == 1:
                score -= 1
        
        diag1 = [opp_board[i][i] for i in range(3)]
        diag2 = [opp_board[i][2-i] for i in range(3)]
        
        for diag in [diag1, diag2]:
            if diag.count(-1) == 2 and diag.count(0) == 1:
                score -= 8
            elif diag.count(-1) == 1:
                score -= 1
    
    # Center control
    if board[1][1] == 1:
        score += 3
    
    # Corner control
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for r, c in corners:
        if board[r][c] == 1:
            score += 2
    
    return score

def heuristic_best_move(board, candidate_moves):
    """Fallback heuristic when search fails."""
    # Prioritize center
    if (1, 1) in candidate_moves:
        return (1, 1)
    
    # Then corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if corner in candidate_moves:
            return corner
    
    # Then edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for edge in edges:
        if edge in candidate_moves:
            return edge
    
    # Last resort
    return candidate_moves[0]
