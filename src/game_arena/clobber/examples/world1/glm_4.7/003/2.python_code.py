
import random

# Board Constants
ROWS = 5
COLS = 6
SEARCH_DEPTH = 4

def list_to_mask(board):
    """
    Converts the input board (list of lists or flat list) to an integer bitmask.
    Bit i (0-29) corresponds to cell (row, col) where i = row * 6 + col.
    """
    mask = 0
    # Handle both 2D lists and flat lists based on type checking
    if isinstance(board[0], list):
        # 2D list
        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c] == 1:
                    mask |= 1 << (r * COLS + c)
    else:
        # Flat list of length 30
        for i in range(len(board)):
            if board[i] == 1:
                mask |= 1 << i
    return mask

def count_moves(mask, opp_mask):
    """
    Counts the number of legal moves for 'mask' against 'opp_mask'.
    """
    cnt = 0
    pieces = mask
    while pieces:
        p = pieces & -pieces
        pos = (p.bit_length() - 1)
        r, c = divmod(pos, COLS)
        
        # Check 4 orthogonal directions for adjacent opponent pieces
        if r > 0 and (opp_mask & (1 << (pos - COLS))): cnt += 1
        if r < ROWS - 1 and (opp_mask & (1 << (pos + COLS))): cnt += 1
        if c > 0 and (opp_mask & (1 << (pos - 1))): cnt += 1
        if c < COLS - 1 and (opp_mask & (1 << (pos + 1))): cnt += 1
            
        pieces -= p
    return cnt

def get_moves(mask, opp_mask):
    """
    Generates a list of legal moves: [(from_pos, to_pos), ...].
    """
    moves = []
    pieces = mask
    while pieces:
        p = pieces & -pieces
        pos = (p.bit_length() - 1)
        r, c = divmod(pos, COLS)
        
        if r > 0:
            t = pos - COLS
            if opp_mask & (1 << t): moves.append((pos, t))
        if r < ROWS - 1:
            t = pos + COLS
            if opp_mask & (1 << t): moves.append((pos, t))
        if c > 0:
            t = pos - 1
            if opp_mask & (1 << t): moves.append((pos, t))
        if c < COLS - 1:
            t = pos + 1
            if opp_mask & (1 << t): moves.append((pos, t))
            
        pieces -= p
    return moves

def alphabeta(you, opp, depth, alpha, beta, maximizing):
    """
    Minimax algorithm with Alpha-Beta pruning.
    'you' and 'opp' are the current bitmasks for the original AI and original Opponent.
    """
    # Leaf node evaluation
    if depth == 0:
        my_mobility = count_moves(you, opp)
        opp_mobility = count_moves(opp, you)
        return my_mobility - opp_mobility

    current_mask = you if maximizing else opp
    target_mask = opp if maximizing else you
    moves = get_moves(current_mask, target_mask)

    # Terminal state check (no legal moves)
    if not moves:
        return -100000 if maximizing else 100000

    if maximizing:
        value = -float('inf')
        for fr, to in moves:
            # Make move: AI moves 'you' piece to capture 'opp' piece
            new_you = you ^ (1 << fr) | (1 << to)
            new_opp = opp ^ (1 << to)
            
            score = alphabeta(new_you, new_opp, depth - 1, alpha, beta, False)
            
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if value >= beta:
                break
        return value
    else:
        value = float('inf')
        for fr, to in moves:
            # Make move: Opponent moves 'opp' piece to capture 'you' piece
            new_opp = opp ^ (1 << fr) | (1 << to)
            new_you = you ^ (1 << to)
            
            score = alphabeta(new_you, new_opp, depth - 1, alpha, beta, True)
            
            if score < value:
                value = score
            if value < beta:
                beta = value
            if value <= alpha:
                break
        return value

def policy(you, opponent):
    # 1. Convert inputs to bitmasks
    you_mask = list_to_mask(you)
    opp_mask = list_to_mask(opponent)
    
    # 2. Generate all legal moves for the current state
    legal_moves = get_moves(you_mask, opp_mask)
    
    # Fail-safe: if no moves (should not happen if game is valid), return a dummy move
    if not legal_moves:
        return "0,0,U"
        
    # 3. Search for the best move
    random.shuffle(legal_moves)
    
    best_score = -float('inf')
    best_move = legal_moves[0]
    
    for fr, to in legal_moves:
        # Simulate move
        new_you = you_mask ^ (1 << fr) | (1 << to)
        new_opp = opp_mask ^ (1 << to)
        
        # Evaluate resulting state using Alpha-Beta search
        # We subtract 1 from depth because we made one move already
        score = alphabeta(new_you, new_opp, SEARCH_DEPTH - 1, -float('inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = (fr, to)
            
    # 4. Convert best move back to string format 'row,col,dir'
    r, c = divmod(best_move[0], COLS)
    tr, tc = divmod(best_move[1], COLS)
    
    dr, dc = tr - r, tc - c
    
    direction = ''
    if dr == -1: direction = 'U'
    elif dr == 1: direction = 'D'
    elif dc == -1: direction = 'L'
    elif dc == 1: direction = 'R'
    
    return f"{r},{c},{direction}"
