
import copy
import math

def is_dark_square(r, c):
    return (r + c) % 2 == 1

def generate_moves(my_men, my_kings, opp_men, opp_kings, color):
    board = {
        'b_men': set(my_men) if color == 'b' else set(),
        'b_kings': set(my_kings) if color == 'b' else set(),
        'w_men': set(opp_men) if color == 'b' else set(my_men),
        'w_kings': set(opp_kings) if color == 'b' else set(my_kings)
    }
    # Adjust for current player
    if color == 'w':
        board = {
            'b_men': set(opp_men),
            'b_kings': set(opp_kings),
            'w_men': set(my_men),
            'w_kings': set(my_kings)
        }
    
    moves = []
    capture_moves = []
    
    # Generate capture moves first (mandatory)
    for piece in list(board[color + '_men']) + list(board[color + '_kings']):
        seqs = generate_capture_sequences(piece, board, color, piece in board[color + '_men'])
        for seq in seqs:
            capture_moves.append((seq[0], seq[-1]))
    
    if capture_moves:
        return capture_moves
    
    # Generate non-capture moves
    for piece in list(board[color + '_men']) + list(board[color + '_kings']):
        r, c = piece
        piece_type = 'man' if piece in board[color + '_men'] else 'king'
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if piece_type == 'king' else []
        
        if piece_type == 'man' and color == 'b':
            directions = [(-1, -1), (-1, 1)]
        elif piece_type == 'man' and color == 'w':
            directions = [(1, -1), (1, 1)]
        
        for dr, dc in directions:
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < 8 and 0 <= new_c < 8:
                if (new_r, new_c) not in board['b_men'] and (new_r, new_c) not in board['b_kings'] \
                   and (new_r, new_c) not in board['w_men'] and (new_r, new_c) not in board['w_kings']:
                    moves.append((piece, (new_r, new_c)))
    
    return moves

def generate_capture_sequences(piece_pos, board, color, is_man):
    sequences = []
    current_path = [piece_pos]
    
    def dfs(pos, path, current_board):
        r, c = pos
        directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
        if is_man:
            if color == 'b':
                directions = [(-2, -2), (-2, 2)]
            else:
                directions = [(2, -2), (2, 2)]
        
        found_capture = False
        for dr, dc in directions:
            new_r, new_c = r + dr, c + dc
            if not (0 <= new_r < 8 and 0 <= new_c < 8):
                continue
            if (new_r, new_c) in current_board['b_men'] or (new_r, new_c) in current_board['b_kings'] \
               or (new_r, new_c) in current_board['w_men'] or (new_r, new_c) in current_board['w_kings']:
                continue
            
            mid_r, mid_c = r + dr//2, c + dc//2
            opponent_color = 'w' if color == 'b' else 'b'
            if (mid_r, mid_c) not in current_board[opponent_color + '_men'] and (mid_r, mid_c) not in current_board[opponent_color + '_kings']:
                continue
            
            found_capture = True
            new_board = copy.deepcopy(current_board)
            # Remove the jumped piece
            if (mid_r, mid_c) in new_board[opponent_color + '_men']:
                new_board[opponent_color + '_men'].remove((mid_r, mid_c))
            else:
                new_board[opponent_color + '_kings'].remove((mid_r, mid_c))
            
            # Move the piece
            new_piece_type = 'king'
            if is_man and ((color == 'b' and new_r == 0) or (color == 'w' and new_r == 7)):
                new_board[color + '_men'].remove(piece_pos)
                new_board[color + '_kings'].add((new_r, new_c))
            elif is_man:
                new_board[color + '_men'].remove(piece_pos)
                new_board[color + '_men'].add((new_r, new_c))
            else:
                new_board[color + '_kings'].remove(piece_pos)
                new_board[color + '_kings'].add((new_r, new_c))
            
            dfs((new_r, new_c), path + [(new_r, new_c)], new_board)
        
        if not found_capture:
            sequences.append(path)
    
    dfs(piece_pos, current_path, board)
    return sequences

def evaluate_board(board):
    # Material count
    score = (2 * len(board['b_kings']) + len(board['b_men'])) - (2 * len(board['w_kings']) + len(board['w_men']))
    
    # Positional bonuses
    for pos in board['b_men']:
        score += (7 - pos[0])  # Encourage black men to advance
    for pos in board['w_men']:
        score += pos[0]  # Encourage white men to advance
    
    # Center control for kings
    for pos in board['b_kings'] + board['w_kings']:
        if (pos[0], pos[1]) in [(3, 3), (4, 4)]:
            score += 1
    
    return score

def minimax(board, depth, alpha, beta, player, moves_cache, cache_key):
    if depth == 0 or not board:
        return None, evaluate_board(board)
    
    key = (player, depth, tuple(sorted(board.items())), cache_key)
    if key in moves_cache:
        return moves_cache[key]
    
    moves = generate_moves_for_player(board, player)
    if not moves:
        moves_cache[key] = (None, -10000 if player == 'b' else 10000)
        return None, -10000 if player == 'b' else 10000
    
    best_move = None
    if player == 'b':
        max_eval = -10000
        for move in moves:
            new_board = apply_move(board, move, player)
            _, eval_score = minimax(new_board, depth - 1, alpha, beta, 'w', moves_cache, cache_key + str(move))
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        moves_cache[key] = (best_move, max_eval)
        return best_move, max_eval
    else:
        min_eval = 10000
        for move in moves:
            new_board = apply_move(board, move, player)
            _, eval_score = minimax(new_board, depth - 1, alpha, beta, 'b', moves_cache, cache_key + str(move))
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        moves_cache[key] = (best_move, min_eval)
        return best_move, min_eval

def apply_move(board, move, player):
    start, end = move
    new_board = copy.deepcopy(board)
    
    piece_type = 'man' if start in new_board[player + '_men'] else 'king'
    if piece_type == 'man':
        new_board[player + '_men'].remove(start)
        if (player == 'b' and end[0] == 0) or (player == 'w' and end[0] == 7):
            new_board[player + '_kings'].add(end)
        else:
            new_board[player + '_men'].add(end)
    else:
        new_board[player + '_kings'].remove(start)
        new_board[player + '_kings'].add(end)
    
    # Check for captures
    if abs(start[0] - end[0]) > 1 or abs(start[1] - end[1]) > 1:
        seqs = generate_capture_sequences(start, new_board, player, piece_type == 'man')
        for seq in seqs:
            if seq[-1] == end:
                for i in range(len(seq) - 1):
                    mid_r = (seq[i][0] + seq[i+1][0]) // 2
                    mid_c = (seq[i][1] + seq[i+1][1]) // 2
                    opponent = 'w' if player == 'b' else 'b'
                    if (mid_r, mid_c) in new_board[opponent + '_men']:
                        new_board[opponent + '_men'].remove((mid_r, mid_c))
                    else:
                        new_board[opponent + '_kings'].remove((mid_r, mid_c))
                break
    
    return new_board

def generate_moves_for_player(board, player):
    if player == 'b':
        return generate_moves(list(board['b_men']), list(board['b_kings']), list(board['w_men']), list(board['w_kings']), 'b')
    else:
        return generate_moves(list(board['w_men']), list(board['w_kings']), list(board['b_men']), list(board['b_kings']), 'w')

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Convert to sets for easier manipulation
    board = {
        'b_men': set(opp_men),
        'b_kings': set(opp_kings),
        'w_men': set(my_men),
        'w_kings': set(my_kings)
    } if color == 'b' else {
        'b_men': set(my_men),
        'b_kings': set(my_kings),
        'w_men': set(opp_men),
        'w_kings': set(opp_kings)
    }
    
    # Use iterative deepening to find the best move
    best_move = None
    moves_cache = {}
    for depth in range(1, 4):  # Iteratively increase depth up to 3
        move, _ = minimax(board, depth, -10000, 10000, color, moves_cache, str(depth))
        if move:
            best_move = move
        else:
            break
    
    # Fallback to any legal move if minimax fails
    if not best_move:
        moves = generate_moves_for_player(board, color)
        if moves:
            best_move = moves[0]
        else:
            # This should not happen in a legal game state
            return ((0, 0), (0, 1))
    
    return best_move
