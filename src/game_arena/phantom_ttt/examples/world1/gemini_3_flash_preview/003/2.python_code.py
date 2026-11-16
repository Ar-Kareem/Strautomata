
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    # Flatten the board for easier indexing
    flat_board = []
    for row in board:
        flat_board.extend(row)
    
    # Define winning combinations
    winning_combos = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Cols
        [0, 4, 8], [2, 4, 6]             # Diagonals
    ]
    
    # 1. Check for immediate win
    for move in legal_moves:
        for combo in winning_combos:
            if move in combo:
                others = [flat_board[i] for i in combo if i != move]
                if all(val == 1 for val in others):
                    return (move // 3, move % 3)
                    
    # 2. Positional Heuristics
    # Prefer center, then corners, then edges
    weights = {4: 10, 0: 5, 2: 5, 6: 5, 8: 5, 1: 2, 3: 2, 5: 2, 7: 2}
    
    # 3. Line potential: prefer moves that are part of lines we are building
    move_scores = {move: weights.get(move, 0) for move in legal_moves}
    
    for move in legal_moves:
        for combo in winning_combos:
            if move in combo:
                # Count how many pieces we have in this line
                count_ours = sum(1 for i in combo if flat_board[i] == 1)
                # In Phantom Tic Tac Toe, we don't know the opponent's positions,
                # but we prioritize lines where we already have progress.
                move_scores[move] += (count_ours * 3)

    # Find the move with the highest score
    best_move = legal_moves[0]
    max_score = -1
    
    for move in legal_moves:
        if move_scores[move] > max_score:
            max_score = move_scores[move]
            best_move = move
            
    return (best_move // 3, best_move % 3)
