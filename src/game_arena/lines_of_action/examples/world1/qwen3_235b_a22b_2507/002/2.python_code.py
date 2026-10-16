
import numpy as np
from collections import deque

def policy(board) -> str:
    board = np.array(board)
    player = 1
    opponent = -1

    # Find all player pieces
    player_pieces = list(zip(*np.where(board == player)))

    if not player_pieces:
        return "0,0:0,0"  # No pieces, though shouldn't happen

    # Directions: 8 directions (dy, dx)
    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1),           (0,1),
                  (1,-1),  (1,0),   (1,1)]

    def count_pieces_along(r, c, dr, dc):
        count = 0
        r, c = r + dr, c + dc
        while 0 <= r < 8 and 0 <= c < 8:
            if board[r, c] != 0:
                count += 1
            r, c = r + dr, c + dc
        return count

    def is_path_clear(r, c, dr, dc, steps, is_capture):
        for step in range(1, steps + 1):
            nr, nc = r + dr * step, c + dc * step
            if not (0 <= nr < 8 and 0 <= nc < 8):
                return False
            # Last step can land on opponent
            if step < steps and board[nr, nc] == opponent:
                return False
        return True

    def get_legal_moves():
        moves = []
        for r, c in player_pieces:
            for dr, dc in directions:
                steps = count_pieces_along(r, c, dr, dc)
                if steps == 0:
                    continue
                nr, nc = r + dr * steps, c + dc * steps
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue
                if not is_path_clear(r, c, dr, dc, steps, board[nr, nc] == opponent):
                    continue
                if board[nr, nc] == player:
                    continue  # can't land on own piece
                moves.append((r, c, nr, nc))
        return moves

    def evaluate_move(r, c, nr, nc):
        # Simulate move
        new_board = board.copy()
        new_board[r, c] = 0
        new_board[nr, nc] = player

        # 1. Evaluate connectivity: number of connected components
        visited = np.zeros((8,8), dtype=bool)
        groups = 0
        queue = deque()
        for i in range(8):
            for j in range(8):
                if new_board[i,j] == player and not visited[i,j]:
                    groups += 1
                    queue.append((i,j))
                    visited[i,j] = True
                    while queue:
                        y, x = queue.popleft()
                        for dy, dx in directions:
                            ny, nx = y+dy, x+dx
                            if (0 <= ny < 8 and 0 <= nx < 8 and
                                new_board[ny,nx] == player and not visited[ny,nx]):
                                visited[ny,nx] = True
                                queue.append((ny,nx))

        # Prefer fewer groups
        score = -groups * 100

        # 2. Capture?
        if board[nr, nc] == opponent:
            score += 20

        # 3. Center control: distance to center
        center_score = 4 - (abs(nr - 3.5) + abs(nc - 3.5))
        score += center_score

        # 4. Bonus if move connects a piece to others (heuristic)
        # Check how many neighbors are yours after move
        neighbors = 0
        for dy, dx in directions:
            ny, nx = nr+dy, nc+dx
            if 0 <= ny < 8 and 0 <= nx < 8 and new_board[ny,nx] == player:
                neighbors += 1
        score += neighbors * 2

        return score

    legal_moves = get_legal_moves()
    if not legal_moves:
        # No legal moves — return a dummy
        return f"{player_pieces[0][0]},{player_pieces[0][1]}:{player_pieces[0][0]},{player_pieces[0][1]}"

    # Evaluate all moves
    best_move = legal_moves[0]
    best_score = float('-inf')

    for move in legal_moves:
        r, c, nr, nc = move
        score = evaluate_move(r, c, nr, nc)
        if score > best_score:
            best_score = score
            best_move = move

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
