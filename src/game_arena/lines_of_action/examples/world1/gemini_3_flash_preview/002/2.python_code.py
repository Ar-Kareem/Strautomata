import time

def get_moves(board, player):
    moves = []
    pieces = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                pieces.append((r, c))

    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for r, c in pieces:
        for dr, dc in directions:
            # Check the line count in this direction
            count = 0
            # Scan both ways
            for step in range(-7, 8):
                nr, nc = r + dr * step, c + dc * step
                if 0 <= nr <= 7 and 0 <= nc <= 7:
                    if board[nr][nc] != 0:
                        count += 1
            
            # Check two potential target squares
            for direction in [1, -1]:
                tr, tc = r + dr * direction * count, c + dc * direction * count
                if 0 <= tr <= 7 and 0 <= tc <= 7:
                    if board[tr][tc] != player:
                        # Check path for enemy pieces (cannot jump over them)
                        blocked = False
                        for step in range(1, count):
                            mr, mc = r + dr * direction * step, c + dc * direction * step
                            if board[mr][mc] == -player:
                                blocked = True
                                break
                        if not blocked:
                            moves.append(f"{r},{c}:{tr},{tc}")
    return moves

def evaluate(board):
    player_pieces = []
    opponent_pieces = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                player_pieces.append((r, c))
            elif board[r][c] == -1:
                opponent_pieces.append((r, c))
    
    if not player_pieces: return -10000
    if not opponent_pieces: return 10000

    # Connectivity heuristic: minimize average distance between pieces
    def get_score(pieces):
        if len(pieces) <= 1: return 1000
        center_r = sum(p[0] for p in pieces) / len(pieces)
        center_c = sum(p[1] for p in pieces) / len(pieces)
        
        # Center proximity (encourage moving to center)
        dist_to_center = sum((abs(p[0]-3.5) + abs(p[1]-3.5)) for p in pieces)
        # Compactness
        spread = sum((abs(p[0]-center_r) + abs(p[1]-center_c)) for p in pieces)
        
        # Few pieces are easier to connect
        count_bonus = -50 * len(pieces)
        
        return - (spread * 2 + dist_to_center) + count_bonus

    return get_score(player_pieces) - get_score(opponent_pieces)

def apply_move(board, move):
    start, end = move.split(':')
    sr, sc = map(int, start.split(','))
    er, ec = map(int, end.split(','))
    new_board = [row[:] for row in board]
    new_board[er][ec] = new_board[sr][sc]
    new_board[sr][sc] = 0
    return new_board

def flip_board(board):
    return [[-cell for cell in row] for row in board]

def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(board), None
    
    moves = get_moves(board, 1 if maximizing else -1)
    if not moves:
        return evaluate(board), None
    
    best_move = moves[0]
    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            evaluation, _ = minimax(apply_move(board, move), depth - 1, alpha, beta, False)
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            # Note: evaluate is always from '1' perspective
            evaluation, _ = minimax(apply_move(board, move), depth - 1, alpha, beta, True)
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board) -> str:
    # 1 second limit: Depth 2 is safe, depth 3 might be possible depending on branching factor
    # LOA branching factor starts low and increases.
    _, move = minimax(board, 2, -float('inf'), float('inf'), True)
    return move
