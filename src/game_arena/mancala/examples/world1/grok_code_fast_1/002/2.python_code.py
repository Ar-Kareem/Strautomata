
import math

MAX_DEPTH = 4

def check_terminal(board):
    you_t, opp_t = board
    if all(x == 0 for x in you_t[:6]):
        you_score = you_t[6] + sum(opp_t[:6])
        opp_score = opp_t[6]
        return True, you_score - opp_score
    elif all(x == 0 for x in opp_t[:6]):
        you_score = you_t[6]
        opp_score = opp_t[6] + sum(you_t[:6])
        return True, you_score - opp_score
    return False, 0

def get_legal(board, is_you):
    you_t, _ = board if is_you else (board[1], board[0])
    for i in range(6):
        if you_t[i] > 0:
            yield i

def make_move(board, move, is_you):
    you_t, opp_t = board if is_you else (opp_t, you_t)
    you_t = list(you_t)
    opp_t = list(opp_t)
    seeds = you_t[move]
    you_t[move] -= seeds
    positions = [f'you{i}' for i in range(7)] + [f'opp{i}' for i in range(6)]
    current_idx = (move + 1) % 7
    last_added = None
    for _ in range(seeds):
        if positions[current_idx].startswith('you'):
            slot = int(positions[current_idx][3:])
            you_t[slot] += 1
            last_added = ('you', slot)
        elif positions[current_idx].startswith('opp'):
            slot = int(positions[current_idx][3:])
            opp_t[slot] += 1
            last_added = ('opp', slot)
        current_idx = (current_idx + 1) % 13
    extra_turn = False
    if last_added and last_added[0] == 'you' and last_added[1] == 6:
        extra_turn = True
    if last_added and last_added[0] == 'you' and last_added[1] in range(6):
        slot = last_added[1]
        if you_t[slot] - 1 == 0:
            opp_slot = 5 - slot
            if opp_t[opp_slot] > 0:
                you_t[6] += opp_t[opp_slot] + 1
                opp_t[opp_slot] = 0
                you_t[slot] = 0
    new_you = tuple(you_t)
    new_opp = tuple(opp_t)
    new_board = (new_you, new_opp) if is_you else (new_opp, new_you)
    return new_board, extra_turn

def minimax(board, is_your_turn, depth):
    terminal, score = check_terminal(board)
    if depth == 0 or terminal:
        if terminal:
            return score
        else:
            return board[0][6] - board[1][6]
    if is_your_turn:
        max_val = -math.inf
        for move in get_legal(board, True):
            new_board, extra_turn = make_move(board, move, True)
            next_turn = True if extra_turn else False
            val = minimax(new_board, next_turn, depth - 1)
            max_val = max(max_val, val)
        return max_val
    else:
        min_val = math.inf
        for move in get_legal(board, False):
            new_board, extra_turn = make_move(board, move, False)
            next_turn = False if extra_turn else True
            val = minimax(new_board, next_turn, depth - 1)
            min_val = min(min_val, val)
        return min_val

def policy(you: list[int], opponent: list[int]) -> int:
    you_tuple = tuple(you)
    opp_tuple = tuple(opponent)
    board = (you_tuple, opp_tuple)
    best_move = 0
    best_val = -math.inf
    for move in range(6):
        if you[move] > 0:
            new_board, extra_turn = make_move(board, move, True)
            terminal, _ = check_terminal(new_board)
            if terminal:
                val = you[6] + sum(opponent[:6]) - opponent[6]
            else:
                next_turn = True if extra_turn else False
                val = minimax(new_board, next_turn, MAX_DEPTH - 1 if extra_turn else MAX_DEPTH)
            if val > best_val:
                best_val = val
                best_move = move
    return best_move
