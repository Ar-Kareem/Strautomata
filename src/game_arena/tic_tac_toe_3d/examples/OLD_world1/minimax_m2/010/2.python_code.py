
def index(z, y, x):
    return z * 9 + y * 3 + x

def generate_lines():
    lines = []
    for z in range(3):
        for y in range(3):
            line = [index(z, y, x) for x in range(3)]
            lines.append(line)
    for z in range(3):
        for x in range(3):
            line = [index(z, y, x) for y in range(3)]
            lines.append(line)
    for x in range(3):
        for y in range(3):
            line = [index(z, y, x) for z in range(3)]
            lines.append(line)
    for z in range(3):
        line1 = [index(z, x, x) for x in range(3)]
        line2 = [index(z, 2 - x, x) for x in range(3)]
        lines.append(line1)
        lines.append(line2)
    for y in range(3):
        line1 = [index(x, y, x) for x in range(3)]
        line2 = [index(2 - x, y, x) for x in range(3)]
        lines.append(line1)
        lines.append(line2)
    for x in range(3):
        line1 = [index(y, y, x) for y in range(3)]
        line2 = [index(2 - y, y, x) for y in range(3)]
        lines.append(line1)
        lines.append(line2)
    lines.append([index(0,0,0), index(1,1,1), index(2,2,2)])
    lines.append([index(0,0,2), index(1,1,1), index(2,2,0)])
    lines.append([index(0,2,0), index(1,1,1), index(2,0,2)])
    lines.append([index(0,2,2), index(1,1,1), index(2,0,0)])
    return lines

def policy(board):
    flat_board = [board[z][y][x] for z in range(3) for y in range(3) for x in range(3)]
    lines = generate_lines()
    
    def has_won(player):
        for line in lines:
            if all(flat_board[idx] == player for idx in line):
                return True
        return False
    
    def evaluate():
        score = 0
        for line in lines:
            ones = sum(1 for idx in line if flat_board[idx] == 1)
            minus_ones = sum(1 for idx in line if flat_board[idx] == -1)
            if ones > 0 and minus_ones > 0:
                score += (ones - minus_ones) * 0.1
            else:
                if ones == 2:
                    score += 10
                elif ones == 1:
                    score += 1
                elif minus_ones == 2:
                    score -= 10
                elif minus_ones == 1:
                    score -= 1
        return score
    
    for i in range(27):
        if flat_board[i] == 0:
            flat_board[i] = 1
            if has_won(1):
                flat_board[i] = 0
                x = i % 3
                y = (i // 3) % 3
                z = i // 9
                return (x, y, z)
            flat_board[i] = 0
    
    for i in range(27):
        if flat_board[i] == 0:
            flat_board[i] = -1
            if has_won(-1):
                flat_board[i] = 0
                x = i % 3
                y = (i // 3) % 3
                z = i // 9
                return (x, y, z)
            flat_board[i] = 0
    
    best_move = None
    best_score = -10**9
    alpha = -10**9
    beta = 10**9
    
    for i in range(27):
        if flat_board[i] == 0:
            flat_board[i] = 1
            score = minimax(1, alpha, beta)
            flat_board[i] = 0
            if score > best_score:
                best_score = score
                best_move = i
            alpha = max(alpha, score)
            if alpha >= beta:
                break
    
    if best_move is None:
        for i in range(27):
            if flat_board[i] == 0:
                x = i % 3
                y = (i // 3) % 3
                z = i // 9
                return (x, y, z)
        return (0, 0, 0)
    else:
        x = best_move % 3
        y = (best_move // 3) % 3
        z = best_move // 9
        return (x, y, z)
    
    def minimax(depth, alpha, beta):
        if has_won(1):
            return 10000
        if has_won(-1):
            return -10000
        if depth == 3:
            return evaluate()
        
        current_player = 1 if depth % 2 == 0 else -1
        available_moves = [i for i in range(27) if flat_board[i] == 0]
        
        if not available_moves:
            return 0
        
        if current_player == 1:
            best = -10**9
            for i in available_moves:
                flat_board[i] = 1
                score = minimax(depth + 1, alpha, beta)
                flat_board[i] = 0
                best = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = 10**9
            for i in available_moves:
                flat_board[i] = -1
                score = minimax(depth + 1, alpha, beta)
                flat_board[i] = 0
                best = min(best, score)
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best
