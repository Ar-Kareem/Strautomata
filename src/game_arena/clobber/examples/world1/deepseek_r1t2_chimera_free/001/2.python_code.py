
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    dir_map = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}
    
    def count_opponent_moves(my_pieces, opp_pieces):
        count = 0
        rows = len(my_pieces)
        cols = len(my_pieces[0])
        for r in range(rows):
            for c in range(cols):
                if opp_pieces[r][c] == 1:
                    # Check up
                    if r > 0 and my_pieces[r-1][c] == 1:
                        count += 1
                    # Check right
                    if c < cols-1 and my_pieces[r][c+1] == 1:
                        count += 1
                    # Check down
                    if r < rows-1 and my_pieces[r+1][c] == 1:
                        count += 1
                    # Check left
                    if c > 0 and my_pieces[r][c-1] == 1:
                        count += 1
        return count
    
    best_move = None
    best_score = float('inf')
    
    for r in range(5):
        for c in range(6):
            if you[r][c] == 1:
                for dir in ['U', 'R', 'D', 'L']:
                    dr, dc = dir_map[dir]
                    dest_r = r + dr
                    dest_c = c + dc
                    
                    # Check if destination is in bounds
                    if not (0 <= dest_r < 5 and 0 <= dest_c < 6):
                        continue
                    
                    # Check if destination contains opponent piece
                    if opponent[dest_r][dest_c] != 1:
                        continue
                    
                    # Simulate move
                    my_new = [row.copy() for row in you]
                    opp_new = [row.copy() for row in opponent]
                    my_new[r][c] = 0
                    my_new[dest_r][dest_c] = 1
                    opp_new[dest_r][dest_c] = 0
                    
                    # Count opponent's moves in the new state
                    opp_moves = count_opponent_moves(my_new, opp_new)
                    
                    # Immediate win condition
                    if opp_moves == 0:
                        return f"{r},{c},{dir}"
                    
                    # Update best move if this move gives opponent fewer options
                    if opp_moves < best_score:
                        best_score = opp_moves
                        best_move = f"{r},{c},{dir}"
    
    # Return the best move found (at least one legal move exists)
    return best_move
