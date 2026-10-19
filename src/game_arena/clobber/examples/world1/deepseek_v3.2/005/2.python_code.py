
import time
import random

BOARD_ROWS = 5
BOARD_COLS = 6
BOARD_SIZE = BOARD_ROWS * BOARD_COLS

DIRECTIONS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

def list_to_bitboard(board_list):
    bitboard = 0
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board_list[row][col] == 1:
                index = row * BOARD_COLS + col
                bitboard |= (1 << index)
    return bitboard

def generate_moves(player_pieces, opponent_pieces):
    moves = []
    for index in range(BOARD_SIZE):
        if (player_pieces >> index) & 1:
            row = index // BOARD_COLS
            col = index % BOARD_COLS
            for dr, dc, dir_letter in DIRECTIONS:
                new_row = row + dr
                new_col = col + dc
                if 0 <= new_row < BOARD_ROWS and 0 <= new_col < BOARD_COLS:
                    new_index = new_row * BOARD_COLS + new_col
                    if (opponent_pieces >> new_index) & 1:
                        moves.append((row, col, dir_letter))
    return moves

def make_move(player_pieces, opponent_pieces, move):
    row, col, dir_letter = move
    for dr, dc, d in DIRECTIONS:
        if d == dir_letter:
            break
    from_index = row * BOARD_COLS + col
    to_row = row + dr
    to_col = col + dc
    to_index = to_row * BOARD_COLS + to_col
    new_opponent_pieces = opponent_pieces & ~(1 << to_index)
    new_player_pieces = player_pieces & ~(1 << from_index)
    new_player_pieces |= (1 << to_index)
    return new_player_pieces, new_opponent_pieces

def count_bits(x):
    return bin(x).count('1')

def evaluate(player_pieces, opponent_pieces):
    our_material = count_bits(player_pieces)
    opp_material = count_bits(opponent_pieces)
    our_mobility = len(generate_moves(player_pieces, opponent_pieces))
    opp_mobility = len(generate_moves(opponent_pieces, player_pieces))
    return (our_material - opp_material) + 0.1 * (our_mobility - opp_mobility)

class TimeoutException(Exception):
    pass

start_time = 0
time_limit = 0.9
timeout = False
transposition_table = {}

def minimax(player_pieces, opponent_pieces, depth, alpha, beta, maximizing_player):
    global timeout
    if timeout:
        raise TimeoutException()
    
    key = (player_pieces, opponent_pieces)
    if key in transposition_table:
        entry_depth, entry_value, entry_flag = transposition_table[key]
        if entry_depth >= depth:
            if entry_flag == 'EXACT':
                return entry_value
            elif entry_flag == 'LOWER':
                if entry_value >= beta:
                    return entry_value
                else:
                    alpha = max(alpha, entry_value)
            elif entry_flag == 'UPPER':
                if entry_value <= alpha:
                    return entry_value
                else:
                    beta = min(beta, entry_value)
    
    if depth == 0:
        value = evaluate(player_pieces, opponent_pieces)
        transposition_table[key] = (depth, value, 'EXACT')
        return value
    
    moves = generate_moves(player_pieces, opponent_pieces)
    if not moves:
        if maximizing_player:
            value = float('-inf')
        else:
            value = float('inf')
        transposition_table[key] = (depth, value, 'EXACT')
        return value
    
    original_alpha = alpha
    original_beta = beta
    
    if maximizing_player:
        value = float('-inf')
        for move in moves:
            new_player, new_opp = make_move(player_pieces, opponent_pieces, move)
            new_value = minimax(new_opp, new_player, depth-1, alpha, beta, False)
            if new_value > value:
                value = new_value
            alpha = max(alpha, value)
            if value >= beta:
                break
        flag = 'EXACT'
        if value <= original_alpha:
            flag = 'UPPER'
        elif value >= original_beta:
            flag = 'LOWER'
        transposition_table[key] = (depth, value, flag)
        return value
    else:
        value = float('inf')
        for move in moves:
            new_player, new_opp = make_move(player_pieces, opponent_pieces, move)
            new_value = minimax(new_opp, new_player, depth-1, alpha, beta, True)
            if new_value < value:
                value = new_value
            beta = min(beta, value)
            if value <= alpha:
                break
        flag = 'EXACT'
        if value <= original_alpha:
            flag = 'UPPER'
        elif value >= original_beta:
            flag = 'LOWER'
        transposition_table[key] = (depth, value, flag)
        return value

def policy(you, opponent):
    global start_time, timeout, transposition_table
    my_pieces = list_to_bitboard(you)
    opp_pieces = list_to_bitboard(opponent)
    
    moves = generate_moves(my_pieces, opp_pieces)
    if not moves:
        # Should not occur in a valid game state; fallback to a dummy move.
        return "0,0,U"
    
    start_time = time.time()
    time_limit = 0.9
    timeout = False
    transposition_table.clear()
    
    best_move = None
    depth = 1
    
    try:
        while time.time() - start_time < time_limit:
            current_best = None
            best_val = float('-inf')
            for move in moves:
                new_my, new_opp = make_move(my_pieces, opp_pieces, move)
                val = minimax(new_opp, new_my, depth-1, float('-inf'), float('inf'), False)
                if val > best_val:
                    best_val = val
                    current_best = move
            if current_best is not None:
                best_move = current_best
            depth += 1
    except TimeoutException:
        pass
    
    if best_move is None:
        best_move = moves[0]
    
    row, col, dir_letter = best_move
    return f"{row},{col},{dir_letter}"
