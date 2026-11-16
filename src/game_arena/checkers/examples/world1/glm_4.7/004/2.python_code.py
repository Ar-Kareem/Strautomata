
import random

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Returns the best move for the current player using Minimax with Alpha-Beta pruning.
    """
    # Board representation: 8x8 list
    # 0: Empty
    # 1: My Man, 2: My King
    # 3: Opp Man, 4: Opp King
    board = [[0] * 8 for _ in range(8)]
    for r, c in my_men: board[r][c] = 1
    for r, c in my_kings: board[r][c] = 2
    for r, c in opp_men: board[r][c] = 3
    for r, c in opp_kings: board[r][c] = 4

    # Generate all legal moves for the current state
    moves = generate_moves(board, color, {1, 2}, {3, 4})
    
    if not moves:
        # No legal moves available (game over likely), return a default move or handle gracefully
        return ((0, 0), (0, 0))

    # Shuffle moves to ensure variety if scores are equal
    random.shuffle(moves)

    best_move = None
    best_score = float('-inf')
    
    # Search depth: 3 (adjustable, 3 is safe for 1s limit in Python)
    SEARCH_DEPTH = 3

    for move in moves:
        # Apply the move to get the next board state
        next_board = make_move(board, move, color)
        
        # Perform minimax search from the opponent's perspective
        score = minimax(next_board, SEARCH_DEPTH - 1, float('-inf'), float('inf'), False, color)
        
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def generate_moves(board, turn_color, my_pieces, opp_pieces):
    """
    Generates all legal moves. Enforces mandatory captures.
    """
    simple_moves = []
    jumps = []

    # Movement directions based on piece type and color
    # 'b' (Black) moves down (row - 1), 'w' (White) moves up (row + 1)
    if turn_color == 'b':
        man_dirs = [(-1, -1), (-1, 1)]
    else:
        man_dirs = [(1, -1), (1, 1)]
    
    king_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece not in my_pieces:
                continue

            # Determine if piece is a Man or King (regardless of owner)
            # 1 and 3 are Men, 2 and 4 are Kings
            piece_type = 1 if piece in [1, 3] else 2
            directions = king_dirs if piece_type == 2 else man_dirs

            for dr, dc in directions:
                nr, nc = r + dr, c + dc

                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = board[nr][nc]
                    if target == 0:
                        # Simple move
                        simple_moves.append(((r, c), (nr, nc)))
                    elif target in opp_pieces:
                        # Potential jump
                        jr, jc = r + 2 * dr, c + 2 * dc
                        if 0 <= jr < 8 and 0 <= jc < 8 and board[jr][jc] == 0:
                            jumps.append(((r, c), (jr, jc)))

    # Mandatory capture rule
    return jumps if jumps else simple_moves

def make_move(board, move, color):
    """
    Applies a move to the board and returns a new board state.
    Handles promotion and captures.
    """
    new_board = [row[:] for row in board]
    (r1, c1), (r2, c2) = move
    
    piece = new_board[r1][c1]
    new_board[r1][c1] = 0

    # Check promotion
    # A piece promotes if it is a Man (1 or 3) and reaches the opposite end
    is_man = (piece == 1 or piece == 3)
    if is_man:
        promoted = False
        if color == 'w' and r2 == 7: promoted = True
        if color == 'b' and r2 == 0: promoted = True
        
        if promoted:
            piece += 1 # 1->2 (My King), 3->4 (Opp King)
            
    new_board[r2][c2] = piece

    # Check capture
    # If move distance is 2, a piece was captured
    if abs(r1 - r2) == 2:
        mr, mc = (r1 + r2) // 2, (c1 + c2) // 2
        new_board[mr][mc] = 0

    return new_board

def minimax(board, depth, alpha, beta, maximizing, my_color):
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    if depth == 0:
        return evaluate(board, my_color)

    # Define piece sets based on whose turn it is
    my_codes = {1, 2} if maximizing else {3, 4}
    opp_codes = {3, 4} if maximizing else {1, 2}
    
    # Determine the color of the player currently moving
    turn_color = my_color if maximizing else ('b' if my_color == 'w' else 'w')
    
    moves = generate_moves(board, turn_color, my_codes, opp_codes)

    if not moves:
        # No moves means loss for the player whose turn it is
        return 10000 if not maximizing else -10000

    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            next_board = make_move(board, move, turn_color)
            eval_score = minimax(next_board, depth - 1, alpha, beta, False, my_color)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            next_board = make_move(board, move, turn_color)
            eval_score = minimax(next_board, depth - 1, alpha, beta, True, my_color)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate(board, my_color):
    """
    Heuristic evaluation function.
    Scores material and position.
    """
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == 0:
                continue
            
            val = 0
            # Positional bonus: Center control is valuable
            pos_bonus = 0
            if 3 <= c <= 4: 
                pos_bonus += 5

            if piece == 1: # My Man
                val = 100
                # Advancement bonus
                if my_color == 'w': val += r * 10
                else: val += (7 - r) * 10
            elif piece == 2: # My King
                val = 150
            elif piece == 3: # Opp Man
                val = -100
                opp_color = 'b' if my_color == 'w' else 'w'
                if opp_color == 'w': val -= r * 10
                else: val -= (7 - r) * 10
            elif piece == 4: # Opp King
                val = -150
            
            if piece in [1, 2]:
                score += val + pos_bonus
            else:
                score += val - pos_bonus
                
    return score
