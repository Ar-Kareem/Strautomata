
import numpy as np

def check_win(board):
    """Check if board has 5 in a row."""
    # Horizontal
    for r in range(6):
        for c in range(2):
            if np.sum(board[r, c:c+5]) == 5:
                return True
    # Vertical
    for c in range(6):
        for r in range(2):
            if np.sum(board[r:r+5, c]) == 5:
                return True
    # Diagonal down-right
    for r in range(2):
        for c in range(2):
            s = 0
            for i in range(5):
                s += board[r+i, c+i]
            if s == 5:
                return True
    # Diagonal down-left
    for r in range(2):
        for c in range(4, 6):
            s = 0
            for i in range(5):
                s += board[r+i, c-i]
            if s == 5:
                return True
    return False

def apply_move(you, opp, move, player):
    """Apply a move and return new boards."""
    r, c, quad, d = move
    new_you = you.copy()
    new_opp = opp.copy()
    
    # Place marble
    if player == 1:
        new_you[r, c] = 1
    else:
        new_opp[r, c] = 1
    
    # Rotate quadrant
    qr = (quad // 2) * 3
    qc = (quad % 2) * 3
    
    if d == 'L':
        new_you[qr:qr+3, qc:qc+3] = np.rot90(new_you[qr:qr+3, qc:qc+3], 1)
        new_opp[qr:qr+3, qc:qc+3] = np.rot90(new_opp[qr:qr+3, qc:qc+3], 1)
    else:
        new_you[qr:qr+3, qc:qc+3] = np.rot90(new_you[qr:qr+3, qc:qc+3], -1)
        new_opp[qr:qr+3, qc:qc+3] = np.rot90(new_opp[qr:qr+3, qc:qc+3], -1)
    
    return new_you, new_opp

def generate_moves(you, opp):
    """Generate all legal moves."""
    empty = (you + opp) == 0
    indices = np.argwhere(empty)
    moves = []
    for r, c in indices:
        for q in range(4):
            for d in ['L', 'R']:
                moves.append((r, c, q, d))
    return moves

def evaluate(you, opp):
    """Static evaluation of position."""
    score = 0
    
    def score_line(y_cnt, o_cnt):
        if y_cnt > 0 and o_cnt == 0:
            if y_cnt == 5:
                return 1000000
            return 10 ** (y_cnt + 1)
        elif o_cnt > 0 and y_cnt == 0:
            if o_cnt == 5:
                return -1000000
            return -(10 ** (o_cnt + 1))
        return 0
    
    # Horizontal
    for r in range(6):
        for c in range(2):
            y = int(you[r, c:c+5].sum())
            o = int(opp[r, c:c+5].sum())
            val = score_line(y, o)
            if abs(val) == 1000000:
                return val
            score += val
    
    # Vertical
    for c in range(6):
        for r in range(2):
            y = int(you[r:r+5, c].sum())
            o = int(opp[r:r+5, c].sum())
            val = score_line(y, o)
            if abs(val) == 1000000:
                return val
            score += val
    
    # Diagonal down-right
    for r in range(2):
        for c in range(2):
            y = sum(int(you[r+i, c+i]) for i in range(5))
            o = sum(int(opp[r+i, c+i]) for i in range(5))
            val = score_line(y, o)
            if abs(val) == 1000000:
                return val
            score += val
    
    # Diagonal down-left
    for r in range(2):
        for c in range(4, 6):
            y = sum(int(you[r+i, c-i]) for i in range(5))
            o = sum(int(opp[r+i, c-i]) for i in range(5))
            val = score_line(y, o)
            if abs(val) == 1000000:
                return val
            score += val
    
    return score

def format_move(move):
    r, c, q, d = move
    return f"{r+1},{c+1},{q},{d}"

def policy(you, opponent):
    you = np.array(you, dtype=np.int8)
    opp = np.array(opponent, dtype=np.int8)
    
    moves = generate_moves(you, opp)
    if not moves:
        return "1,1,0,L"  # Should not happen per problem statement
    
    # Check for immediate win
    for move in moves:
        new_you, new_opp = apply_move(you, opp, move, 1)
        if check_win(new_you) and not check_win(new_opp):
            return format_move(move)
    
    # Depth-2 minimax
    best_score = -float('inf')
    best_move = moves[0]
    
    for move in moves:
        new_you, new_opp = apply_move(you, opp, move, 1)
        
        # If this move somehow lets opponent win immediately, skip
        if check_win(new_opp):
            continue
            
        # Simulate opponent's best response
        opp_moves = generate_moves(new_you, new_opp)
        worst_score = float('inf')
        
        for opp_move in opp_moves:
            new_you2, new_opp2 = apply_move(new_you, new_opp, opp_move, 2)
            
            you_win = check_win(new_you2)
            opp_win = check_win(new_opp2)
            
            if opp_win and not you_win:
                worst_score = -1000000
                break  # Opponent can force win
            elif you_win and not opp_win:
                score = 1000000
            elif you_win and opp_win:
                score = 0  # Draw
            else:
                score = evaluate(new_you2, new_opp2)
            
            if score < worst_score:
                worst_score = score
                if worst_score <= -1000000:
                    break
        
        if worst_score > best_score:
            best_score = worst_score
            best_move = move
            if best_score >= 1000000:
                break  # Found forced win
    
    return format_move(best_move)
