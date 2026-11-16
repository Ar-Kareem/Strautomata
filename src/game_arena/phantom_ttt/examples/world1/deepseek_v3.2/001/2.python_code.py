
import random
from typing import List, Tuple

def policy(board: List[List[int]], legal_moves: List[int]) -> Tuple[int, int]:
    # Convert legal_moves from 0-8 to (r,c) form
    legal_cells = [(move // 3, move % 3) for move in legal_moves]
    
    # Helper: check line for two 1s and one unconfirmed (0) cell
    def winning_move_available():
        lines = [
            # rows
            [(0,0),(0,1),(0,2)],
            [(1,0),(1,1),(1,2)],
            [(2,0),(2,1),(2,2)],
            # cols
            [(0,0),(1,0),(2,0)],
            [(0,1),(1,1),(2,1)],
            [(0,2),(1,2),(2,2)],
            # diags
            [(0,0),(1,1),(2,2)],
            [(0,2),(1,1),(2,0)]
        ]
        for line in lines:
            vals = [board[r][c] for r,c in line]
            if vals.count(1) == 2:
                # Find the unconfirmed cell in this line
                for r,c in line:
                    if board[r][c] == 0 and (r,c) in legal_cells:
                        return (r,c)
        return None
    
    win_move = winning_move_available()
    if win_move:
        return win_move
    
    # Strategy priority: center, corners, edges
    priority_order = [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]
    
    for cell in priority_order:
        if cell in legal_cells and board[cell[0]][cell[1]] == 0:
            return cell
    
    # Fallback: random legal move (should always be reachable)
    return random.choice(legal_cells)
