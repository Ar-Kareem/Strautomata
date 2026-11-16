
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    MY_ID = 1
    OPP_ID = -1

    def get_lines(b):
        lines = []
        # Rows
        for r in range(4):
            lines.append(b[r])
        # Cols
        for c in range(4):
            lines.append([b[r][c] for r in range(4)])
        # Diagonals
        lines.append([b[i][i] for i in range(4)])
        lines.append([b[i][3-i] for i in range(4)])
        return lines

    def evaluate(b):
        lines = get_lines(b)
        score = 0
        for line in lines:
            my_count = line.count(MY_ID)
            opp_count = line.count(OPP_ID)
            
            if my_count == 4: return 100000
            if opp_count == 4: return -100000
            
            if opp_count == 0:
                score += (my_count ** 3)
            if my_count == 0:
                score -= (opp_count ** 3)
        return score

    def get_moves(b):
        moves = []
        # Prioritize center for better branching
        order = [(1,1), (1,2), (2,1), (2,2), (0,0), (0,3), (3,0), (3,3), (0,1), (0,2), (1,0), (1,3), (2,0), (2,3), (3,1), (3,2)]
        for r, c in order:
            if b[r][c] == 0:
                moves.append((r, c))
        return moves

    def minimax(b, depth, alpha, beta, maximizing):
        score = evaluate(b)
        if abs(score) > 50000 or depth == 0:
            return score
        
        moves = get_moves(b)
        if not moves:
            return 0

        if maximizing:
            max_eval = -math.inf
            for r, c in moves:
                b[r][c] = MY_ID
                eval = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in moves:
                b[r][c] = OPP_ID
                eval = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    best_val = -math.inf
    best_move = (0, 0)
    
    # Increase depth slightly if the board is emptier
    empty_cells = sum(row.count(0) for row in board)
    search_depth = 4 if empty_cells > 10 else 6

    for r, c in get_moves(board):
        board[r][c] = MY_ID
        move_val = minimax(board, search_depth, -math.inf, math.inf, False)
        board[r][c] = 0
        if move_val > best_val:
            best_val = move_val
            best_move = (r, c)
            
    return best_move
