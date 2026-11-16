
def get_moves(player_board, opponent_board):
    moves = []
    for i in range(5):
        for j in range(6):
            if player_board[i][j] == 1:
                # Check all four directions for opponent pieces
                if i > 0 and opponent_board[i-1][j] == 1:
                    moves.append((i, j, 'U'))
                if i < 4 and opponent_board[i+1][j] == 1:
                    moves.append((i, j, 'D'))
                if j > 0 and opponent_board[i][j-1] == 1:
                    moves.append((i, j, 'L'))
                if j < 5 and opponent_board[i][j+1] == 1:
                    moves.append((i, j, 'R'))
    return moves

def simulate_move(you, opponent, move, is_my_move):
    row, col, dir = move
    dest_row, dest_col = row, col
    if dir == 'U':
        dest_row -= 1
    elif dir == 'D':
        dest_row += 1
    elif dir == 'L':
        dest_col -= 1
    elif dir == 'R':
        dest_col += 1
    else:
        raise ValueError("Invalid direction")

    # Create deep copies of the boards
    new_you = [list(r) for r in you]
    new_opponent = [list(r) for r in opponent]

    if is_my_move:
        new_you[row][col] = 0
        new_you[dest_row][dest_col] = 1
        new_opponent[dest_row][dest_col] = 0
    else:
        new_opponent[row][col] = 0
        new_opponent[dest_row][dest_col] = 1
        new_you[dest_row][dest_col] = 0

    return new_you, new_opponent

def heuristic(you, opponent):
    my_moves = len(get_moves(you, opponent))
    opp_moves = len(get_moves(opponent, you))
    my_pieces = sum(sum(row) for row in you)
    opp_pieces = sum(sum(row) for row in opponent)
    return 10 * (my_moves - opp_moves) + (my_pieces - opp_pieces)

def minimax(you, opponent, depth, is_my_turn, alpha, beta):
    if depth == 0:
        return heuristic(you, opponent)
    
    if is_my_turn:
        moves = get_moves(you, opponent)
        if not moves:
            return -1000  # Player loses if no moves
        best = -float('inf')
        for move in moves:
            new_you, new_opponent = simulate_move(you, opponent, move, True)
            score = minimax(new_you, new_opponent, depth-1, False, alpha, beta)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break  # Beta cutoff
        return best
    else:
        moves = get_moves(opponent, you)
        if not moves:
            return 1000  # Opponent loses if no moves
        best = float('inf')
        for move in moves:
            new_you, new_opponent = simulate_move(you, opponent, move, False)
            score = minimax(new_you, new_opponent, depth-1, True, alpha, beta)
            if score < best:
                best = score
            if best < beta:
                beta = best
            if alpha >= beta:
                break  # Alpha cutoff
        return best

def policy(you, opponent):
    moves = get_moves(you, opponent)
    if not moves:
        # Fallback in case no moves are available (should not happen if policy is called correctly)
        return "0,0,U"
    
    best_move = None
    best_score = -float('inf')
    for move in moves:
        new_you, new_opponent = simulate_move(you, opponent, move, True)
        score = minimax(new_you, new_opponent, 2, False, -float('inf'), float('inf'))
        if score > best_score:
            best_score = score
            best_move = move
    
    # Format the move as a string
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
