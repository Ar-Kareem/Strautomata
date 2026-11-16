
import numpy as np
from collections import deque

def policy(board) -> str:
    board = np.array(board)
    player = 1
    opponent = -1
    empty = 0

    directions = [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]  # E, SE, S, SW, W, NW, N, NE

    def count_in_direction(r, c, dr, dc):
        count = 0
        nr, nc = r, c
        while 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr, nc] != empty:
                count += 1
            nr += dr
            nc += dc
        return count

    def get_legal_moves():
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r, c] != player:
                    continue
                for dr, dc in directions:
                    distance = count_in_direction(r, c, dr, dc)
                    if distance == 0:
                        continue
                    # Check if path is blocked by opponent piece (cannot jump over opponent)
                    blocked = False
                    nr, nc = r, c
                    for _ in range(distance):
                        nr += dr
                        nc += dc
                        if not (0 <= nr < 8 and 0 <= nc < 8):
                            blocked = True
                            break
                        if board[nr, nc] == opponent and (_ != distance - 1):  # Can capture on last
                            blocked = True
                            break
                    if blocked:
                        continue
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        if board[nr, nc] != player:  # Can't land on own piece
                            moves.append((r, c, nr, nc))
        return moves

    def count_components(piece_board):
        visited = np.zeros((8,8), dtype=bool)
        comp_count = 0
        max_size = 0
        for i in range(8):
            for j in range(8):
                if piece_board[i,j] and not visited[i,j]:
                    comp_count += 1
                    # BFS
                    queue = deque([(i,j)])
                    visited[i,j] = True
                    size = 0
                    while queue:
                        r, c = queue.popleft()
                        size += 1
                        for dr,dc in directions:
                            nr, nc = r+dr, c+dc
                            if 0<=nr<8 and 0<=nc<8 and piece_board[nr,nc] and not visited[nr,nc]:
                                visited[nr,nc] = True
                                queue.append((nr,nc))
                    max_size = max(max_size, size)
        return comp_count, max_size

    def evaluate_board(board):
        my_pieces = (board == player)
        comp_count, max_comp = count_components(my_pieces)
        opp_pieces = (board == opponent)
        opp_comp_count, _ = count_components(opp_pieces)
        # Less components is better. Larger max component is better.
        # Also, if we have only one component, that's winning.
        if comp_count == 1:
            return 1000  # Winning
        score = -comp_count * 10 + max_comp
        # Encourage reducing opponent connectivity
        score += opp_comp_count * 2
        return score

    # Generate all legal moves
    legal_moves = get_legal_moves()
    if not legal_moves:
        # Should not happen, but fallback
        return "0,0:0,0"

    best_score = -float('inf')
    best_move = legal_moves[0]
    
    current_score = evaluate_board(board)

    for move in legal_moves:
        r1, c1, r2, c2 = move
        # Simulate move
        new_board = board.copy()
        new_board[r1, c1] = empty
        captured = (new_board[r2, c2] == opponent)
        new_board[r2, c2] = player
        score = evaluate_board(new_board)
        # Bonus for capture
        if captured:
            score += 5
        # Small bonus for reducing component count
        # Avoid moves that lead to worse structure
        if score > best_score:
            best_score = score
            best_move = move

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
