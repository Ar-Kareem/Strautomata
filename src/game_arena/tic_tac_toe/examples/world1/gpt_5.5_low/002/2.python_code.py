
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Perfect-play Tic Tac Toe policy for player 1.

    board:
        0  = empty
        1  = our move
        -1 = opponent move

    returns:
        (row, col) for a legal empty cell
    """

    # Preferred move order improves alpha-beta pruning and tie-breaking.
    MOVE_ORDER = (
        (1, 1),  # center
        (0, 0), (0, 2), (2, 0), (2, 2),  # corners
        (0, 1), (1, 0), (1, 2), (2, 1),  # edges
    )

    def board_to_tuple(b):
        return tuple(tuple(row) for row in b)

    def winner(state):
        lines = []

        # Rows and columns
        for i in range(3):
            lines.append(state[i])
            lines.append((state[0][i], state[1][i], state[2][i]))

        # Diagonals
        lines.append((state[0][0], state[1][1], state[2][2]))
        lines.append((state[0][2], state[1][1], state[2][0]))

        for line in lines:
            s = sum(line)
            if s == 3:
                return 1
            if s == -3:
                return -1

        return 0

    def empty_cells(state):
        return [(r, c) for r, c in MOVE_ORDER if state[r][c] == 0]

    @lru_cache(None)
    def minimax(state, turn, depth, alpha, beta):
        """
        Returns score from player 1's perspective.
        Higher is better for us.
        """
        w = winner(state)
        if w == 1:
            return 10 - depth
        if w == -1:
            return depth - 10

        moves = empty_cells(state)
        if not moves:
            return 0

        if turn == 1:
            best = -100
            for r, c in moves:
                new_state = [list(row) for row in state]
                new_state[r][c] = 1
                score = minimax(board_to_tuple(new_state), -1, depth + 1, alpha, beta)
                if score > best:
                    best = score
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = 100
            for r, c in moves:
                new_state = [list(row) for row in state]
                new_state[r][c] = -1
                score = minimax(board_to_tuple(new_state), 1, depth + 1, alpha, beta)
                if score < best:
                    best = score
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    state = board_to_tuple(board)
    legal_moves = empty_cells(state)

    # Safety fallback: if there is any legal move, return one.
    if not legal_moves:
        return (0, 0)

    # First, choose the move with the best minimax score.
    best_move = legal_moves[0]
    best_score = -100

    for r, c in legal_moves:
        new_board = [list(row) for row in state]
        new_board[r][c] = 1

        score = minimax(board_to_tuple(new_board), -1, 1, -100, 100)

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
