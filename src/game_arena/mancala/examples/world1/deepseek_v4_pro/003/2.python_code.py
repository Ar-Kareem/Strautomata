
import time

class TimeOutError(Exception):
    pass

def get_legal_moves(board, player):
    if player == 0:
        return [i for i in range(6) if board[i] > 0]
    else:
        return [i for i in range(7, 13) if board[i] > 0]

def simulate_move(board, player, pit):
    new_board = board[:]
    seeds = new_board[pit]
    new_board[pit] = 0
    cur = pit
    while seeds > 0:
        cur = (cur + 1) % 14
        if (player == 0 and cur == 13) or (player == 1 and cur == 6):
            continue
        new_board[cur] += 1
        seeds -= 1
    last = cur
    # capture
    if player == 0:
        if last in range(6) and new_board[last] == 1 and new_board[12-last] > 0:
            new_board[6] += new_board[last] + new_board[12-last]
            new_board[last] = 0
            new_board[12-last] = 0
    else:
        if last in range(7, 13) and new_board[last] == 1 and new_board[12-last] > 0:
            new_board[13] += new_board[last] + new_board[12-last]
            new_board[last] = 0
            new_board[12-last] = 0
    extra = (player == 0 and last == 6) or (player == 1 and last == 13)
    # game over
    if sum(new_board[0:6]) == 0 or sum(new_board[7:13]) == 0:
        new_board[6] += sum(new_board[0:6])
        new_board[13] += sum(new_board[7:13])
        for i in range(6):
            new_board[i] = 0
        for i in range(7, 13):
            new_board[i] = 0
        game_over = True
    else:
        game_over = False
    return new_board, extra, game_over

def evaluate(board, player):
    if player == 0:
        return 2 * (board[6] - board[13]) + sum(board[0:6]) - sum(board[7:13])
    else:
        return 2 * (board[13] - board[6]) + sum(board[7:13]) - sum(board[0:6])

def negamax(board, player, depth, alpha, beta, start_time, time_limit):
    if time.perf_counter() - start_time > time_limit:
        raise TimeOutError()
    legal = get_legal_moves(board, player)
    if not legal:
        if player == 0:
            return board[6] - board[13]
        else:
            return board[13] - board[6]
    if depth == 0:
        return evaluate(board, player)
    
    # move ordering for deeper nodes
    if depth > 1:
        moves_scores = []
        for pit in legal:
            new_board, extra, game_over = simulate_move(board, player, pit)
            if game_over:
                if player == 0:
                    s = new_board[6] - new_board[13]
                else:
                    s = new_board[13] - new_board[6]
            else:
                s = evaluate(new_board, player)
            moves_scores.append((s, pit))
        moves_scores.sort(reverse=True, key=lambda x: x[0])
        legal = [pit for _, pit in moves_scores]
    
    value = -float('inf')
    for pit in legal:
        new_board, extra, game_over = simulate_move(board, player, pit)
        if game_over:
            if player == 0:
                score = new_board[6] - new_board[13]
            else:
                score = new_board[13] - new_board[6]
        else:
            if extra:
                score = negamax(new_board, player, depth-1, alpha, beta, start_time, time_limit)
            else:
                score = -negamax(new_board, 1-player, depth-1, -beta, -alpha, start_time, time_limit)
        value = max(value, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return value

def policy(you, opponent):
    board = you[:6] + [you[6]] + opponent[:6] + [opponent[6]]
    player = 0
    legal_moves = get_legal_moves(board, player)
    if not legal_moves:
        return 0  # fallback (should not happen)
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    start_time = time.perf_counter()
    time_limit = 0.95  # seconds
    
    # root move ordering
    move_scores = []
    for pit in legal_moves:
        new_board, extra, game_over = simulate_move(board, player, pit)
        if game_over:
            s = new_board[6] - new_board[13]
        else:
            s = evaluate(new_board, player)
        move_scores.append((s, pit))
    move_scores.sort(reverse=True, key=lambda x: x[0])
    sorted_moves = [pit for _, pit in move_scores]
    
    best_move = sorted_moves[0]
    depth = 1
    while True:
        current_best = sorted_moves[0]
        alpha = -float('inf')
        beta = float('inf')
        try:
            for pit in sorted_moves:
                new_board, extra, game_over = simulate_move(board, player, pit)
                if game_over:
                    score = new_board[6] - new_board[13]
                else:
                    if extra:
                        score = negamax(new_board, player, depth-1, alpha, beta, start_time, time_limit)
                    else:
                        score = -negamax(new_board, 1, depth-1, -beta, -alpha, start_time, time_limit)
                if score > alpha:
                    alpha = score
                    current_best = pit
            best_move = current_best
            depth += 1
            if time.perf_counter() - start_time > time_limit:
                break
        except TimeOutError:
            break
    return best_move
