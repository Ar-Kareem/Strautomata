
import time

class TimeOutError(Exception):
    pass

DIRS = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]

def parse_board(you, opponent):
    """Convert input to a 5x6 board: 0 empty, 1 our piece, 2 opponent piece."""
    board = [[0] * 6 for _ in range(5)]
    if isinstance(you[0], list):
        for i in range(5):
            for j in range(6):
                if you[i][j] == 1:
                    board[i][j] = 1
                elif opponent[i][j] == 1:
                    board[i][j] = 2
    else:
        for i in range(5):
            for j in range(6):
                idx = i * 6 + j
                if you[idx] == 1:
                    board[i][j] = 1
                elif opponent[idx] == 1:
                    board[i][j] = 2
    return board

def get_moves(board, player):
    """Return all legal moves for the player as (r, c, dir_char)."""
    moves = []
    opp = 3 - player
    for r in range(5):
        for c in range(6):
            if board[r][c] == player:
                for dr, dc, d in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and board[nr][nc] == opp:
                        moves.append((r, c, d))
    return moves

def apply_move(board, move):
    """Return a new board after applying the move."""
    r, c, d = move
    dr, dc = 0, 0
    if d == 'U': dr, dc = -1, 0
    elif d == 'D': dr, dc = 1, 0
    elif d == 'L': dr, dc = 0, -1
    elif d == 'R': dr, dc = 0, 1
    nr, nc = r + dr, c + dc
    new_board = [row[:] for row in board]
    player = new_board[r][c]
    new_board[r][c] = 0
    new_board[nr][nc] = player
    return new_board

def order_moves(board, player, moves):
    """Sort moves by the number of opponent moves after the move (ascending)."""
    opp = 3 - player
    def move_score(move):
        new_board = apply_move(board, move)
        return len(get_moves(new_board, opp))
    return sorted(moves, key=move_score)

def evaluate(board, player):
    """Evaluate the board from the perspective of the player to move."""
    my_moves = len(get_moves(board, player))
    opp_moves = len(get_moves(board, 3 - player))
    if my_moves == 0:
        return -1000
    if opp_moves == 0:
        return 1000
    my_pieces = sum(row.count(player) for row in board)
    opp_pieces = sum(row.count(3 - player) for row in board)
    return my_moves - opp_moves + 0.1 * (my_pieces - opp_pieces)

def max_value(board, player, depth, alpha, beta, time_limit):
    """Maximize value for the current player."""
    if time.time() >= time_limit:
        raise TimeOutError()
    moves = get_moves(board, player)
    if not moves:
        return -1000 + depth, None
    if depth == 0:
        return evaluate(board, player), None
    moves = order_moves(board, player, moves)
    best_move = None
    value = -float('inf')
    for move in moves:
        if time.time() >= time_limit:
            raise TimeOutError()
        new_board = apply_move(board, move)
        v, _ = min_value(new_board, 3 - player, depth - 1, alpha, beta, time_limit)
        if v > value:
            value = v
            best_move = move
        alpha = max(alpha, value)
        if alpha >= beta:
            break
    return value, best_move

def min_value(board, player, depth, alpha, beta, time_limit):
    """Minimize value for the opponent."""
    if time.time() >= time_limit:
        raise TimeOutError()
    moves = get_moves(board, player)
    if not moves:
        return 1000 - depth, None
    if depth == 0:
        return evaluate(board, player), None
    moves = order_moves(board, player, moves)
    best_move = None
    value = float('inf')
    for move in moves:
        if time.time() >= time_limit:
            raise TimeOutError()
        new_board = apply_move(board, move)
        v, _ = max_value(new_board, 3 - player, depth - 1, alpha, beta, time_limit)
        if v < value:
            value = v
            best_move = move
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value, best_move

def policy(you: list[int], opponent: list[int]) -> str:
    board = parse_board(you, opponent)
    moves = get_moves(board, 1)
    if not moves:
        return "0,0,U"  # fallback (should not happen)
    
    time_limit = time.time() + 0.95
    best_move = moves[0]
    best_move_str = f"{best_move[0]},{best_move[1]},{best_move[2]}"
    depth = 1
    try:
        while True:
            if time.time() >= time_limit:
                break
            score, move = max_value(board, 1, depth, -float('inf'), float('inf'), time_limit)
            if move is not None:
                best_move = move
                best_move_str = f"{move[0]},{move[1]},{move[2]}"
            depth += 1
    except TimeOutError:
        pass
    return best_move_str
