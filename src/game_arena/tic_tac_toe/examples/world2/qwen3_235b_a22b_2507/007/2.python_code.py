
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = [row[:] for row in board]  # Copy to avoid mutation
    player = 1
    opponent = -1

    # Helper: check if a player has won
    def has_won(b, p):
        # Check rows
        for r in range(4):
            if all(b[r][c] == p for c in range(4)):
                return True
        # Check cols
        for c in range(4):
            if all(b[r][c] == p for r in range(4)):
                return True
        # Check diagonals
        if all(b[i][i] == p for i in range(4)):
            return True
        if all(b[i][3-i] == p for i in range(4)):
            return True
        return False

    # Check for immediate win
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = player
                if has_won(board, player):
                    return (r, c)
                board[r][c] = 0

    # Check for opponent win and block
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = opponent
                if has_won(board, opponent):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # If no immediate win/block, use minimax with alpha-beta pruning
    def is_terminal(b):
        if has_won(b, player) or has_won(b, opponent):
            return True
        # Check draw
        if all(b[r][c] != 0 for r in range(4) for c in range(4)):
            return True
        return False

    def evaluate(b):
        if has_won(b, player):
            return 10
        if has_won(b, opponent):
            return -10
        # Draw
        if all(b[r][c] != 0 for r in range(4) for c in range(4)):
            return 0
        # Heuristic: count close to winning
        score = 0
        lines = []
        # All rows
        for r in range(4):
            lines.append([(r, c) for c in range(4)])
        # All cols
        for c in range(4):
            lines.append([(r, c) for r in range(4)])
        # Diagonals
        lines.append([(i, i) for i in range(4)])
        lines.append([(i, 3-i) for i in range(4)])
        
        for line in lines:
            my_count = 0
            opp_count = 0
            for (r, c) in line:
                if b[r][c] == player:
                    my_count += 1
                elif b[r][c] == opponent:
                    opp_count += 1
            if opp_count == 0 and my_count > 0:
                score += my_count  # I can win this line
            elif my_count == 0 and opp_count > 0:
                score -= opp_count  # Opponent can win this line
        return score

    def get_moves(b):
        moves = []
        for r in range(4):
            for c in range(4):
                if b[r][c] == 0:
                    moves.append((r, c))
        # Move ordering: center moves first? But more importantly, try moves that are near Xs
        # Simple: prioritize center
        center_moves = []
        edge_moves = []
        for (r, c) in moves:
            if (r,c) in [(1,1), (1,2), (2,1), (2,2)]:
                center_moves.append((r,c))
            else:
                edge_moves.append((r,c))
        return center_moves + edge_moves

    def minimax(b, depth, alpha, beta, maximizing):
        if is_terminal(b) or depth == 0:
            return evaluate(b), None
        
        moves = get_moves(b)
        if not moves:
            return evaluate(b), None

        best_move = moves[0]

        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                r, c = move
                b[r][c] = player
                eval_score, _ = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
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
                r, c = move
                b[r][c] = opponent
                eval_score, _ = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # We can go to max depth 10 which is safe
    _, move = minimax(board, 10, -float('inf'), float('inf'), True)
    if move is None:
        # Fallback: pick first available move
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    return move
