
import numpy as np
from collections import deque

def policy(board) -> str:
    """
    Strategy:
    1. Check if any move connects all our pieces (win condition).
    2. If opponent has a contiguous group, disrupt it by capturing or isolating.
    3. Otherwise, prioritize moves that reduce fragmentation of our pieces.
    4. Fallback to a random legal move if no clear strategy is found.
    """
    board = np.array(board)
    our_pieces = np.where(board == 1)
    opponent_pieces = np.where(board == -1)

    # Step 1: Check if any move connects all our pieces
    for (from_row, from_col) in zip(our_pieces[0], our_pieces[1]):
        for (to_row, to_col) in get_legal_moves(board, from_row, from_col):
            new_board = make_move(board, from_row, from_col, to_row, to_col)
            if is_our_group_connected(new_board):
                return f"{from_row},{from_col}:{to_row},{to_col}"

    # Step 2: Check if opponent has a contiguous group and disrupt it
    if is_opponent_group_connected(board):
        # Find opponent's weakest link (e.g., a piece that can be captured)
        for (from_row, from_col) in zip(our_pieces[0], our_pieces[1]):
            for (to_row, to_col) in get_legal_moves(board, from_row, from_col):
                new_board = make_move(board, from_row, from_col, to_row, to_col)
                if not is_opponent_group_connected(new_board):
                    return f"{from_row},{from_col}:{to_row},{to_col}"

    # Step 3: Prioritize moves that reduce our fragmentation
    best_move = None
    best_score = -float('inf')

    for (from_row, from_col) in zip(our_pieces[0], our_pieces[1]):
        for (to_row, to_col) in get_legal_moves(board, from_row, from_col):
            new_board = make_move(board, from_row, from_col, to_row, to_col)
            score = evaluate_move(new_board)
            if score > best_score:
                best_score = score
                best_move = f"{from_row},{from_col}:{to_row},{to_col}"

    if best_move is not None:
        return best_move

    # Step 4: Fallback to a random legal move
    all_legal_moves = []
    for (from_row, from_col) in zip(our_pieces[0], our_pieces[1]):
        for (to_row, to_col) in get_legal_moves(board, from_row, from_col):
            all_legal_moves.append(f"{from_row},{from_col}:{to_row},{to_col}")

    return np.random.choice(all_legal_moves) if all_legal_moves else "0,0:0,0"  # Default if no moves (shouldn't happen)

def get_legal_moves(board, from_row, from_col):
    """Return all legal moves for a piece at (from_row, from_col)."""
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    legal_moves = []
    for dr, dc in directions:
        to_row, to_col = from_row + dr, from_col + dc
        distance = 1
        while 0 <= to_row < 8 and 0 <= to_col < 8:
            if board[to_row, to_col] == -1:  # Can capture opponent
                legal_moves.append((to_row, to_col))
                break
            elif board[to_row, to_col] == 0:  # Can land here
                if distance == count_pieces_in_line(board, from_row, from_col, dr, dc):
                    legal_moves.append((to_row, to_col))
                break
            distance += 1
            to_row += dr
            to_col += dc
    return legal_moves

def count_pieces_in_line(board, from_row, from_col, dr, dc):
    """Count the number of pieces (ours + opponent) in the line of movement."""
    count = 0
    to_row, to_col = from_row, from_col
    while 0 <= to_row < 8 and 0 <= to_col < 8:
        if board[to_row, to_col] != 0:
            count += 1
        to_row += dr
        to_col += dc
    return count

def make_move(board, from_row, from_col, to_row, to_col):
    """Return a new board after making a move from (from_row, from_col) to (to_row, to_col)."""
    new_board = board.copy()
    new_board[from_row, from_col] = 0
    new_board[to_row, to_col] = 1
    return new_board

def is_our_group_connected(board):
    """Check if all our pieces are connected in 8 directions."""
    our_pieces = np.where(board == 1)
    if len(our_pieces[0]) == 0:
        return False
    visited = set()
    queue = deque([(our_pieces[0][0], our_pieces[1][0])])
    visited.add((our_pieces[0][0], our_pieces[1][0]))
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    while queue:
        r, c = queue.popleft()
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in visited and board[nr, nc] == 1:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return len(visited) == len(our_pieces[0])

def is_opponent_group_connected(board):
    """Check if all opponent's pieces are connected in 8 directions."""
    opponent_pieces = np.where(board == -1)
    if len(opponent_pieces[0]) == 0:
        return False
    visited = set()
    queue = deque([(opponent_pieces[0][0], opponent_pieces[1][0])])
    visited.add((opponent_pieces[0][0], opponent_pieces[1][0]))
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    while queue:
        r, c = queue.popleft()
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in visited and board[nr, nc] == -1:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return len(visited) == len(opponent_pieces[0])

def evaluate_move(new_board):
    """Evaluate a move based on heuristics (lower fragmentation score is better)."""
    our_pieces = np.where(new_board == 1)
    if len(our_pieces[0]) == 0:
        return -float('inf')
    # Calculate fragmentation: number of connected groups we have
    visited = set()
    groups = 0
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    for r, c in zip(our_pieces[0], our_pieces[1]):
        if (r, c) not in visited:
            groups += 1
            queue = deque([(r, c)])
            visited.add((r, c))
            while queue:
                nr, nc = queue.popleft()
                for dr, dc in directions:
                    nnr, nnc = nr + dr, nc + dc
                    if 0 <= nnr < 8 and 0 <= nnc < 8 and (nnr, nnc) not in visited and new_board[nnr, nnc] == 1:
                        visited.add((nnr, nnc))
                        queue.append((nnr, nnc))
    return -groups  # More groups = worse score
