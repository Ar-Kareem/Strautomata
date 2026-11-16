
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    
    def simulate(you, opp, move):
        you = list(you)
        opp = list(opp)
        seeds = you[move]
        you[move] = 0
        
        pos = move + 1
        side = 0  # 0 = my side, 1 = opp side
        last_side, last_pos = 0, move
        
        while seeds > 0:
            if side == 0:
                if pos <= 6:
                    you[pos] += 1
                    last_side, last_pos = 0, pos
                    seeds -= 1
                    pos += 1
                    if pos > 6:
                        side = 1
                        pos = 0
                else:
                    side = 1
                    pos = 0
            else:
                if pos <= 5:
                    opp[pos] += 1
                    last_side, last_pos = 1, pos
                    seeds -= 1
                    pos += 1
                else:
                    side = 0
                    pos = 0
        
        extra = (last_side == 0 and last_pos == 6)
        
        if last_side == 0 and last_pos < 6 and you[last_pos] == 1:
            opposite = 5 - last_pos
            if opp[opposite] > 0:
                you[6] += 1 + opp[opposite]
                you[last_pos] = 0
                opp[opposite] = 0
        
        return you, opp, extra
    
    def evaluate(you, opp):
        score = (you[6] - opp[6]) * 10
        score += sum(you[:6]) - sum(opp[:6])
        for i in range(6):
            if you[i] == 6 - i:
                score += 3
        return score
    
    def get_moves(board):
        moves = []
        for m in range(6):
            if board[m] > 0:
                if board[m] == 6 - m:
                    moves.insert(0, m)
                else:
                    moves.append(m)
        return moves
    
    def minimax(you, opp, depth, alpha, beta, my_turn):
        you_empty = all(you[i] == 0 for i in range(6))
        opp_empty = all(opp[i] == 0 for i in range(6))
        
        if you_empty or opp_empty:
            final_you = you[6] + sum(you[:6])
            final_opp = opp[6] + sum(opp[:6])
            diff = final_you - final_opp
            if diff > 0:
                return 10000 + diff, None
            elif diff < 0:
                return -10000 + diff, None
            return 0, None
        
        if depth == 0:
            return evaluate(you, opp), None
        
        if my_turn:
            best = float('-inf')
            best_move = None
            for m in get_moves(you):
                ny, no, extra = simulate(you, opp, m)
                if extra:
                    val, _ = minimax(ny, no, depth, alpha, beta, True)
                else:
                    val, _ = minimax(ny, no, depth - 1, alpha, beta, False)
                if val > best:
                    best = val
                    best_move = m
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best, best_move
        else:
            best = float('inf')
            best_move = None
            for m in get_moves(opp):
                no, ny, extra = simulate(opp, you, m)
                if extra:
                    val, _ = minimax(ny, no, depth, alpha, beta, False)
                else:
                    val, _ = minimax(ny, no, depth - 1, alpha, beta, True)
                if val < best:
                    best = val
                    best_move = m
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best, best_move
    
    best_move = None
    for m in range(6):
        if you[m] > 0:
            best_move = m
            break
    
    for d in range(1, 30):
        if time.time() - start_time > 0.85:
            break
        _, move = minimax(list(you), list(opponent), d, float('-inf'), float('inf'), True)
        if move is not None:
            best_move = move
    
    return best_move
