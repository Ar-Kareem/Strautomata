
import sys
import random

# Constants
LINES = []
POWERS_OF_2 = [1 << i for i in range(27)]

def init_lines():
    global LINES
    # Rows (k varies)
    for i in range(3):
        for j in range(3):
            mask = 0
            for k in range(3):
                mask |= POWERS_OF_2[i*9 + j*3 + k]
            LINES.append(mask)
    
    # Columns (j varies)
    for i in range(3):
        for k in range(3):
            mask = 0
            for j in range(3):
                mask |= POWERS_OF_2[i*9 + j*3 + k]
            LINES.append(mask)
            
    # Pillars (i varies)
    for j in range(3):
        for k in range(3):
            mask = 0
            for i in range(3):
                mask |= POWERS_OF_2[i*9 + j*3 + k]
            LINES.append(mask)
            
    # Layer Diagonals (i fixed)
    for i in range(3):
        mask = 0
        for x in range(3): mask |= POWERS_OF_2[i*9 + x*3 + x]
        LINES.append(mask)
        mask = 0
        for x in range(3): mask |= POWERS_OF_2[i*9 + x*3 + (2-x)]
        LINES.append(mask)
        
    # Vertical Plane Diagonals (j fixed)
    for j in range(3):
        mask = 0
        for x in range(3): mask |= POWERS_OF_2[x*9 + j*3 + x]
        LINES.append(mask)
        mask = 0
        for x in range(3): mask |= POWERS_OF_2[x*9 + j*3 + (2-x)]
        LINES.append(mask)
        
    # Vertical Plane Diagonals (k fixed)
    for k in range(3):
        mask = 0
        for x in range(3): mask |= POWERS_OF_2[x*9 + x*3 + k]
        LINES.append(mask)
        mask = 0
        for x in range(3): mask |= POWERS_OF_2[x*9 + (2-x)*3 + k]
        LINES.append(mask)
        
    # Main Space Diagonals
    mask = 0
    for x in range(3): mask |= POWERS_OF_2[x*9 + x*3 + x]
    LINES.append(mask)
    mask = 0
    for x in range(3): mask |= POWERS_OF_2[x*9 + x*3 + (2-x)]
    LINES.append(mask)
    mask = 0
    for x in range(3): mask |= POWERS_OF_2[x*9 + (2-x)*3 + x]
    LINES.append(mask)
    mask = 0
    for x in range(3): mask |= POWERS_OF_2[x*9 + (2-x)*3 + (2-x)]
    LINES.append(mask)

init_lines()

def check_win(bits):
    for line in LINES:
        if (bits & line) == line:
            return True
    return False

def evaluate(p1_bits, p2_bits):
    score = 0
    for line in LINES:
        p1_c = (p1_bits & line).bit_count()
        p2_c = (p2_bits & line).bit_count()
        
        if p1_c > 0 and p2_c > 0:
            continue
            
        if p1_c == 2:
            score += 50
        elif p1_c == 1:
            score += 1
            
        if p2_c == 2:
            score -= 50
        elif p2_c == 1:
            score -= 1
    return score

def get_empty_bits(p1_bits, p2_bits):
    occupied = p1_bits | p2_bits
    # 27 bits mask
    return (~occupied) & 0x7FFFFFF

def minimax(p1_bits, p2_bits, depth, alpha, beta, maximizing_player):
    if check_win(p1_bits):
        return 10000 + depth, None
    if check_win(p2_bits):
        return -10000 - depth, None
        
    empty_bits = get_empty_bits(p1_bits, p2_bits)
    if empty_bits == 0:
        return 0, None
    
    if depth == 0:
        return evaluate(p1_bits, p2_bits), None
        
    moves = []
    temp = empty_bits
    while temp:
        lsb = temp & -temp
        moves.append(lsb)
        temp -= lsb
        
    # Move ordering: try center first (bit 13)
    if POWERS_OF_2[13] in moves:
        moves.remove(POWERS_OF_2[13])
        moves.insert(0, POWERS_OF_2[13])
        
    best_move = None
    
    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            p1_new = p1_bits | move
            eval_score, _ = minimax(p1_new, p2_bits, depth-1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            p2_new = p2_bits | move
            eval_score, _ = minimax(p1_bits, p2_new, depth-1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board):
    p1_bits = 0
    p2_bits = 0
    
    for i in range(3):
        for j in range(3):
            for k in range(3):
                idx = i*9 + j*3 + k
                if board[i][j][k] == 1:
                    p1_bits |= POWERS_OF_2[idx]
                elif board[i][j][k] == -1:
                    p2_bits |= POWERS_OF_2[idx]
                    
    empty_bits = get_empty_bits(p1_bits, p2_bits)
    empty_count = empty_bits.bit_count()
    
    # 1. Immediate Win Check
    temp = empty_bits
    while temp:
        lsb = temp & -temp
        if check_win(p1_bits | lsb):
            idx = (lsb.bit_length() - 1)
            return (idx // 9, (idx % 9) // 3, idx % 3)
        temp -= lsb
        
    # 2. Immediate Block Check
    temp = empty_bits
    while temp:
        lsb = temp & -temp
        if check_win(p2_bits | lsb):
            idx = (lsb.bit_length() - 1)
            return (idx // 9, (idx % 9) // 3, idx % 3)
        temp -= lsb

    # 3. Minimax Search
    # Adjust depth based on stage of game
    depth = 3
    if empty_count <= 20: depth = 4
    if empty_count <= 12: depth = 5
    if empty_count <= 6: depth = 6
    
    _, best_move_bits = minimax(p1_bits, p2_bits, depth, -float('inf'), float('inf'), True)
    
    if best_move_bits is None:
        # Fallback: pick random empty
        lsb = empty_bits & -empty_bits
        idx = (lsb.bit_length() - 1)
        return (idx // 9, (idx % 9) // 3, idx % 3)
        
    idx = (best_move_bits.bit_length() - 1)
    return (idx // 9, (idx % 9) // 3, idx % 3)
