
import copy
import math
import time

def policy(board):
    # We are player 1, opponent is -1
    player = 1
    # Generate all legal moves
    moves = get_all_moves(board, player)
    if not moves:
        # No legal moves (shouldn't happen in normal game)
        return "0,0:0,0"  # dummy
    if len(moves) == 1:
        return format_move(moves[0])
    
    # Set depth based on game stage (early/mid/end)
    piece_count = sum(1 for row in board for cell in row if cell == player)
    if piece_count <= 4:
        depth = 4  # endgame, can search deeper
    elif piece_count <= 8:
        depth = 3
    else:
        depth = 2  # early game, many moves
    
    # Use iterative deepening with time limit
    start_time = time.time()
    best_move = None
    for d in range(1, depth+1):
        move_scores = []
        for move in moves:
            new_board = apply_move(board, move, player)
            # Opponent's turn, so we evaluate from our perspective after opponent's best response
            score = alpha_beta(new_board, d-1, -math.inf, math.inf, False, player)
            move_scores.append((score, move))
            # Check time
            if time.time() - start_time > 0.8:
                break
        if move_scores:
            move_scores.sort(key=lambda x: x[0], reverse=True)
            best_move = move_scores[0][1]
        if time.time() - start_time > 0.8:
            break
    
    if best_move is None:
        best_move = moves[0]
    
    return format_move(best_move)

def format_move(move):
    fr, fc, tr, tc = move
    return f"{fr},{fc}:{tr},{tc}"

def get_all_moves(board, player):
    moves = []
    # Directions: (dr, dc) for 8 directions
    dirs = [(-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1)]
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                # For each direction
                for dr, dc in dirs:
                    # Count pieces in this line (including current)
                    count = 0
                    # Walk along line until board edge
                    rr, cc = r, c
                    while 0 <= rr < 8 and 0 <= cc < 8:
                        if board[rr][cc] != 0:
                            count += 1
                        rr += dr
                        cc += dc
                    # Move distance = count
                    dist = count
                    tr = r + dr * dist
                    tc = c + dc * dist
                    if 0 <= tr < 8 and 0 <= tc < 8:
                        # Check path for enemy pieces in between
                        blocked = False
                        # Check squares from (r,c) exclusive to (tr,tc) exclusive
                        steps = dist
                        for step in range(1, steps):
                            cr = r + dr * step
                            cc = c + dc * step
                            if board[cr][cc] == -player:  # enemy
                                blocked = True
                                break
                        if not blocked:
                            # Landing square can be empty or enemy (capture)
                            if board[tr][tc] != player:  # cannot land on own piece
                                moves.append((r, c, tr, tc))
    return moves

def apply_move(board, move, player):
    # Returns a new board with move applied
    fr, fc, tr, tc = move
    new_board = [row[:] for row in board]
    new_board[fr][fc] = 0
    new_board[tr][tc] = player  # capture automatically handled
    return new_board

def alpha_beta(board, depth, alpha, beta, maximizing_player, player):
    # player is the original player (us)
    if depth == 0:
        return evaluate(board, player)
    
    current = player if maximizing_player else -player
    moves = get_all_moves(board, current)
    if not moves:
        # No moves -> terminal? Could be loss if opponent connects first, but for simplicity evaluate
        return evaluate(board, player)
    
    if maximizing_player:
        value = -math.inf
        for move in moves:
            new_board = apply_move(board, move, current)
            value = max(value, alpha_beta(new_board, depth-1, alpha, beta, False, player))
            alpha = max(alpha, value)
            if value >= beta:
                break
        return value
    else:
        value = math.inf
        for move in moves:
            new_board = apply_move(board, move, current)
            value = min(value, alpha_beta(new_board, depth-1, alpha, beta, True, player))
            beta = min(beta, value)
            if value <= alpha:
                break
        return value

def evaluate(board, player):
    # Score from perspective of player (1 for us)
    opponent = -player
    # Components: we want few components
    our_comp = connected_components(board, player)
    opp_comp = connected_components(board, opponent)
    # Material
    our_pieces = sum(1 for row in board for cell in row if cell == player)
    opp_pieces = sum(1 for row in board for cell in row if cell == opponent)
    # Mobility
    our_moves = len(get_all_moves(board, player))
    opp_moves = len(get_all_moves(board, opponent))
    # Center control: pieces near center
    center_score = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                # distance from center (3.5,3.5)
                d = abs(r - 3.5) + abs(c - 3.5)
                center_score += (14 - d)  # smaller distance -> higher
            elif board[r][c] == opponent:
                d = abs(r - 3.5) + abs(c - 3.5)
                center_score -= (14 - d)
    
    # Weighted sum
    score = 0
    score += (opp_comp - our_comp) * 50  # we want our components lower
    score += (our_pieces - opp_pieces) * 30
    score += (our_moves - opp_moves) * 2
    score += center_score * 0.5
    return score

def connected_components(board, player):
    visited = [[False for _ in range(8)] for _ in range(8)]
    components = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                components += 1
                # BFS
                stack = [(r,c)]
                visited[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    # 8 neighbors
                    for dr in (-1,0,1):
                        for dc in (-1,0,1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr+dr, cc+dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                if board[nr][nc] == player and not visited[nr][nc]:
                                    visited[nr][nc] = True
                                    stack.append((nr,nc))
    return components
