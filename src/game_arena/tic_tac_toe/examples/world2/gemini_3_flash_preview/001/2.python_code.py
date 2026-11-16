
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    my_id = 1
    opp_id = -1
    size = 4

    def get_winner(b):
        # Rows and Columns
        for i in range(size):
            if abs(sum(b[i])) == size:
                return b[i][0]
            col_sum = sum(b[j][i] for j in range(size))
            if abs(col_sum) == size:
                return b[0][i]
        
        # Diagonals
        diag1 = sum(b[i][i] for i in range(size))
        if abs(diag1) == size:
            return b[0][0]
        diag2 = sum(b[i][size - 1 - i] for i in range(size))
        if abs(diag2) == size:
            return b[0][size - 1]
        
        return 0

    def evaluate(b):
        winner = get_winner(b)
        if winner == my_id: return 1000
        if winner == opp_id: return -1000
        
        score = 0
        lines = []
        # Rows
        for r in range(size): lines.append(b[r])
        # Cols
        for c in range(size): lines.append([b[r][c] for r in range(size)])
        # Diagonals
        lines.append([b[i][i] for i in range(size)])
        lines.append([b[i][size-1-i] for i in range(size)])
        
        for line in lines:
            my_count = line.count(my_id)
            opp_count = line.count(opp_id)
            if my_count > 0 and opp_count == 0:
                score += (10 ** (my_count - 1))
            elif opp_count > 0 and my_count == 0:
                score -= (10 ** (opp_count - 1))
        return score

    def alpha_beta(b, depth, alpha, beta, is_maximizing):
        winner = get_winner(b)
        if winner != 0 or depth == 0:
            return evaluate(b)
        
        empty_cells = [(r, c) for r in range(size) for c in range(size) if b[r][c] == 0]
        if not empty_cells:
            return 0

        # Heuristic move ordering: prioritize center
        empty_cells.sort(key=lambda x: abs(1.5-x[0]) + abs(1.5-x[1]))

        if is_maximizing:
            max_eval = -math.inf
            for r, c in empty_cells:
                b[r][c] = my_id
                eval = alpha_beta(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in empty_cells:
                b[r][c] = opp_id
                eval = alpha_beta(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    best_val = -math.inf
    best_move = (0, 0)
    
    # Increase depth depending on pieces on board to stay under 1s
    filled = sum(1 for r in range(size) for c in range(size) if board[r][c] != 0)
    search_depth = 4 if filled < 4 else 5

    possible_moves = [(r, c) for r in range(size) for c in range(size) if board[r][c] == 0]
    if not possible_moves: return (0,0)
    
    # Sort moves to check promising ones first
    possible_moves.sort(key=lambda x: abs(1.5-x[0]) + abs(1.5-x[1]))

    for r, c in possible_moves:
        board[r][c] = my_id
        move_val = alpha_beta(board, search_depth, -math.inf, math.inf, False)
        board[r][c] = 0
        if move_val > best_val:
            best_val = move_val
            best_move = (r, c)
            
    return best_move
