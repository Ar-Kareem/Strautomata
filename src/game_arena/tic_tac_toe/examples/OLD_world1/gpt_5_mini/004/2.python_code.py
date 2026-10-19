
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the next move for player 1 on a 3x3 Tic Tac Toe board.
    board: 3x3 list of lists with values {0: empty, 1: us, -1: opponent}
    Returns: (row, col) with 0 <= row, col <= 2
    """

    # helpers
    def winner(b: List[List[int]]) -> Optional[int]:
        # returns 1 if we win, -1 if opponent wins, None otherwise
        lines = []
        # rows and cols
        for i in range(3):
            lines.append((b[i][0], b[i][1], b[i][2]))
            lines.append((b[0][i], b[1][i], b[2][i]))
        # diagonals
        lines.append((b[0][0], b[1][1], b[2][2]))
        lines.append((b[0][2], b[1][1], b[2][0]))
        for a, c, d in lines:
            if a == c == d and a != 0:
                return a
        return None

    def empty_cells(b: List[List[int]]):
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    yield (i, j)

    # determine counts and whose turn it is
    ones = sum(1 for i in range(3) for j in range(3) if board[i][j] == 1)
    minusones = sum(1 for i in range(3) for j in range(3) if board[i][j] == -1)
    # assume it's our turn when called; but compute current player anyway
    current_player = 1 if ones == minusones else -1

    # We'll run minimax from the perspective of player 1 (us).
    # score is from our perspective: larger is better for us.
    def minimax(b: List[List[int]], player: int, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[Tuple[int,int]]]:
        w = winner(b)
        if w is not None:
            # sooner wins are better: scale by remaining depth
            return (w * (10 - depth), None)
        # no empty cells -> draw
        empties = [(i, j) for i, j in empty_cells(b)]
        if not empties:
            return (0, None)

        # move ordering: center, corners, edges
        preferred = []
        if b[1][1] == 0:
            preferred.append((1,1))
        for (i,j) in [(0,0),(0,2),(2,0),(2,2)]:
            if b[i][j] == 0:
                preferred.append((i,j))
        for (i,j) in [(0,1),(1,0),(1,2),(2,1)]:
            if b[i][j] == 0:
                preferred.append((i,j))

        best_move: Optional[Tuple[int,int]] = None
        if player == 1:
            # maximize
            best_score = -10**9
            for (i,j) in preferred:
                b[i][j] = player
                score, _ = minimax(b, -player, depth+1, alpha, beta)
                b[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i,j)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move
        else:
            # minimize (opponent)
            best_score = 10**9
            for (i,j) in preferred:
                b[i][j] = player
                score, _ = minimax(b, -player, depth+1, alpha, beta)
                b[i][j] = 0
                if score < best_score:
                    best_score = score
                    best_move = (i,j)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move

    # If somehow the board is already terminal or has no empties, pick a valid empty or (0,0)
    if winner(board) is not None:
        # board terminal; return any empty cell (or (0,0) if none)
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i,j)
        return (0,0)

    # Run minimax from current player. We want the move for player 1 (us).
    # If it's not our turn (current_player == -1), run minimax anyways but pick the best response for us,
    # so we simulate until it's our move. To be safe, always request minimax starting with player=1 if it's our turn;
    # otherwise start with current_player and then pick the move that results in us moving next. Simpler: if it's not our turn,
    # still compute as if we are to move now (i.e., set player=1). This function is expected to be called when it's our turn.
    start_player = 1

    _, move = minimax([row[:] for row in board], start_player, 0, -10**9, 10**9)

    # If minimax didn't find a move (shouldn't happen), pick first empty
    if move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i,j)
        return (0,0)

    return move
