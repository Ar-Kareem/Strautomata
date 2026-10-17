
from functools import lru_cache

def policy(board):
    # Convert board to tuple for hashing
    b = tuple(tuple(row) for row in board)

    # Determine current player: 1 for us (always), -1 for opponent
    # Count moves to see whose turn it is; we are always "1"
    # It's assumed policy is called on our turn.
    # Still, minimax will use player variable.
    
    @lru_cache(None)
    def check_winner(state):
        # returns 1 if we win, -1 if opponent wins, 0 if no winner
        # state is tuple of tuples
        # rows, cols, diags
        for i in range(3):
            s = state[i][0] + state[i][1] + state[i][2]
            if s == 3: return 1
            if s == -3: return -1
            s = state[0][i] + state[1][i] + state[2][i]
            if s == 3: return 1
            if s == -3: return -1
        d1 = state[0][0] + state[1][1] + state[2][2]
        d2 = state[0][2] + state[1][1] + state[2][0]
        if d1 == 3 or d2 == 3: return 1
        if d1 == -3 or d2 == -3: return -1
        return 0

    def is_full(state):
        return all(state[i][j] != 0 for i in range(3) for j in range(3))

    @lru_cache(None)
    def minimax(state, player):
        winner = check_winner(state)
        if winner != 0:
            return winner, None
        if is_full(state):
            return 0, None

        # Move ordering: center, corners, edges
        moves = [(1,1),(0,0),(0,2),(2,0),(2,2),(0,1),(1,0),(1,2),(2,1)]

        best_move = None
        if player == 1:
            best_score = -2
            for r, c in moves:
                if state[r][c] == 0:
                    new_state = [list(row) for row in state]
                    new_state[r][c] = 1
                    new_state = tuple(tuple(row) for row in new_state)
                    score, _ = minimax(new_state, -1)
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
                    if best_score == 1:
                        break
            return best_score, best_move
        else:
            best_score = 2
            for r, c in moves:
                if state[r][c] == 0:
                    new_state = [list(row) for row in state]
                    new_state[r][c] = -1
                    new_state = tuple(tuple(row) for row in new_state)
                    score, _ = minimax(new_state, 1)
                    if score < best_score:
                        best_score = score
                        best_move = (r, c)
                    if best_score == -1:
                        break
            return best_score, best_move

    # Choose move
    _, move = minimax(b, 1)

    # Fallback: choose any empty cell if something went wrong
    if move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
    return move
