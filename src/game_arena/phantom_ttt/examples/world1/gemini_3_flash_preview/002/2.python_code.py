
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    """
    State: board is 3x3. 1 = Mine, 0 = Unknown (Empty or Opponent).
    legal_moves: List of indices 0-8.
    Return: (row, col)
    """
    
    # Weighting for Tic Tac Toe positions (Center, Corners, Edges)
    weights = [
        3, 2, 3,
        2, 4, 2,
        3, 2, 3
    ]
    
    def get_coord(idx):
        return idx // 3, idx % 3

    def get_idx(r, c):
        return r * 3 + c

    # 1. Identify winning moves (if we have 2 in a row and the 3rd is legal)
    winning_lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Cols
        [0, 4, 8], [2, 4, 6]             # Diagonals
    ]
    
    # Check for immediate wins based on confirmed "1"s
    for line in winning_lines:
        mine_in_line = [i for i in line if board[get_coord(i)[0]][get_coord(i)[1]] == 1]
        if len(mine_in_line) == 2:
            potential_win = [i for i in line if i not in mine_in_line][0]
            if potential_win in legal_moves:
                return get_coord(potential_win)

    # 2. Score remaining legal moves
    move_scores = {}
    for move in legal_moves:
        r, c = get_coord(move)
        
        # If we already have a 1 there, it shouldn't be in legal_moves, 
        # but we skip just in case.
        if board[r][c] == 1:
            continue
            
        score = weights[move]
        
        # Add to score if the move helps complete a line where we already have a mark
        for line in winning_lines:
            if move in line:
                mine_count = sum(1 for i in line if board[get_coord(i)[0]][get_coord(i)[1]] == 1)
                score += mine_count * 5
        
        move_scores[move] = score

    if not move_scores:
        # Fallback to random legal move if weights fail
        chosen_idx = random.choice(legal_moves)
        return get_coord(chosen_idx)

    # 3. Choose the move with the highest score
    best_move = max(move_scores, key=move_scores.get)
    return get_coord(best_move)
