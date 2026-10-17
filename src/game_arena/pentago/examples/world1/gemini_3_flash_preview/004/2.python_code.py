
import numpy as np

def policy(you, opponent):
    you = np.array(you)
    opp = np.array(opp)
    
    def check_win(board):
        # Check rows, cols
        for i in range(6):
            for j in range(2):
                if np.all(board[i, j:j+5] == 1): return True
                if np.all(board[j:j+5, i] == 1): return True
        # Check diagonals
        for r in range(2):
            for c in range(2):
                if all(board[r+k, c+k] == 1 for k in range(5)): return True
                if all(board[r+k, c+4-k] == 1 for k in range(5)): return True
        # Check off-diagonals
        if all(board[i+1, i] == 1 for i in range(5)): return True
        if all(board[i, i+1] == 1 for i in range(5)): return True
        if all(board[i+1, 5-i] == 1 for i in range(5)): return True
        if all(board[i, 4-i] == 1 for i in range(5)): return True
        return False

    def apply_move(y_board, o_board, r, c, q, d):
        ny, no = y_board.copy(), o_board.copy()
        ny[r, c] = 1
        
        def rotate(block, direction):
            return np.rot90(block, k=-1 if direction == 'R' else 1)
        
        rs, cs = (q // 2) * 3, (q % 2) * 3
        ny[rs:rs+3, cs:cs+3] = rotate(ny[rs:rs+3, cs:cs+3], d)
        no[rs:rs+3, cs:cs+3] = rotate(no[rs:rs+3, cs:cs+3], d)
        return ny, no

    # Prioritize moves
    possible_moves = []
    for r in range(6):
        for c in range(6):
            if you[r, c] == 0 and opponent[r, c] == 0:
                for q in range(4):
                    for d in ['L', 'R']:
                        # Winning move?
                        ny, no = apply_move(you, opponent, r, c, q, d)
                        if check_win(ny):
                            return f"{r+1},{c+1},{q},{d}"
                        possible_moves.append((r, c, q, d))

    # Block opponent's winning move
    for r, c, q, d in possible_moves:
        ny, no = apply_move(opponent, you, r, c, q, d)
        if check_win(ny):
            return f"{r+1},{c+1},{q},{d}"

    # Heuristic: Center control and avoiding giving opponent an advantage
    best_move = possible_moves[0]
    best_score = -1
    
    # Simple tactical weights for board positions
    weights = [
        [1, 1, 1, 1, 1, 1],
        [1, 2, 1, 1, 2, 1],
        [1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1],
        [1, 2, 1, 1, 2, 1],
        [1, 1, 1, 1, 1, 1]
    ]

    for r, c, q, d in possible_moves:
        score = weights[r][c]
        # Check if this move helps opponent (naive)
        ny, no = apply_move(you, opponent, r, c, q, d)
        # Avoid rotating into a loss
        if any(check_win(apply_move(no, ny, tr, tc, tq, td)[0]) 
               for tr in range(6) for tc in range(6) if ny[tr,tc]==0 and no[tr,tc]==0
               for tq in range(4) for td in ['L', 'R'] if (tr,tc) != (r,c)):
            score -= 10
        
        if score > best_score:
            best_score = score
            best_move = (r, c, q, d)

    return f"{best_move[0]+1},{best_move[1]+1},{best_move[2]},{best_move[3]}"
