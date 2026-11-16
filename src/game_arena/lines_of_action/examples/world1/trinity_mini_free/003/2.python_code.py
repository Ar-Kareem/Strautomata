
def policy(board):
    """
    Returns the optimal move for the current player using minimax with alpha-beta pruning.
    """
    # Helper function to generate all legal moves
    def get_moves(board):
        moves = []
        directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        for i in range(8):
            for j in range(8):
                if board[i][j] == 1:
                    for dx, dy in directions:
                        count = 0
                        step = 1
                        while True:
                            ni, nj = i + dx*step, j + dy*step
                            if not (0 <= ni < 8 and 0 <= nj < 8):
                                break
                            if board[ni][nj] == 0:
                                step += 1
                                continue
                            if board[ni][nj] == 1:
                                count += 1
                                step += 1
                            else:  # Enemy piece
                                # Check if no pieces beyond enemy
                                beyond = False
                                step2 = 1
                                while True:
                                    nni, nnj = ni + dx*step2, nj + dy*step2
                                    if not (0 <= nni < 8 and 0 <= nnj < 8):
                                        break
                                    if board[nni][nnj] != 0:
                                        beyond = True
                                        break
                                    step2 += 1
                                if beyond:
                                    break
                                else:
                                    count += 1
                                    step += 1
                                    break
                        if count > 0:
                            moves.append((i, j, i + dx*count, j + dy*count))
        return moves

    # Helper function to evaluate board state
    def evaluate(board):
        # Check if all pieces are connected
        pieces = [(i, j) for i in range(8) for j in range(8) if board[i][j] == 1]
        if not pieces:
            return -1000  # Loss
        visited = set()
        components = 0
        directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        for piece in pieces:
            if piece not in visited:
                components += 1
                stack = [piece]
                visited.add(piece)
                while stack:
                    x, y = stack.pop()
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == 1 and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            stack.append((nx, ny))
        if components == 1:
            return 1000  # Win
        return 1000 - (components * 100) - (len(pieces) * 10)

    # Minimax with alpha-beta pruning
    def minimax(board, depth, alpha, beta, maximizing):
        if depth == 0 or not get_moves(board):
            return evaluate(board)
        if maximizing:
            max_eval = -1000
            for move in get_moves(board):
                new_board = [row[:] for row in board]
                from_i, from_j, to_i, to_j = move
                new_board[from_i][from_j] = 0
                new_board[to_i][to_j] = 1
                eval_val = minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 1000
            for move in get_moves(board):
                new_board = [row[:] for row in board]
                from_i, from_j, to_i, to_j = move
                new_board[from_i][from_j] = 0
                new_board[to_i][to_j] = 1
                eval_val = minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # Generate moves and choose best
    moves = get_moves(board)
    if not moves:
        return "0,0:0,0"  # Fallback (should not happen)
    best_move = moves[0]
    best_eval = -1000
    alpha = -1000
    beta = 1000
    for move in moves:
        new_board = [row[:] for row in board]
        from_i, from_j, to_i, to_j = move
        new_board[from_i][from_j] = 0
        new_board[to_i][to_j] = 1
        eval_val = minimax(new_board, 2, alpha, beta, False)
        if eval_val > best_eval:
            best_eval = eval_val
            best_move = move
        alpha = max(alpha, best_eval)
        if beta <= alpha:
            break
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
