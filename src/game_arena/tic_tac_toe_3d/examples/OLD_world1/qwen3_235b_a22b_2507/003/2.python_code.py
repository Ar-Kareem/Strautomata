import numpy as npfrom typing import List, Tupledef policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
 """
 Returns the next move for3x3x33D Tic Tac Toe using minimax with alpha-beta pruning.
 """
 board_array = np.array(board)
 n =3 # Find all empty cells empty_cells = []
 for i in range(n):
 for j in range(n):
 for k in range(n):
 if board_array[i, j, k] ==0:
 empty_cells.append((i, j, k))
 # If no moves available (shouldn't happen in valid game), return center if not empty_cells:
 return (1,1,1)
 # If first move, take center if len(empty_cells) ==27:
 return (1,1,1)
 # Define functions for game logic def check_winner(board_state):
 # Check all possible lines in3D for i in range(n):
 for j in range(n):
 # Row along x-axis if abs(sum(board_state[i, j, k] for k in range(n))) ==3:
 return board_state[i, j,0]
 # Row along y-axis if abs(sum(board_state[i, k, j] for k in range(n))) ==3:
 return board_state[i,0, j]
 # Row along z-axis if abs(sum(board_state[k, i, j] for k in range(n))) ==3:
 return board_state[0, i, j]
 # Diagonals on xy planes (fixed z)
 for k in range(n):
 if abs(sum(board_state[i, i, k] for i in range(n))) ==3:
 return board_state[0,0, k]
 if abs(sum(board_state[i,2-i, k] for i in range(n))) ==3:
 return board_state[0,2, k]
 # Diagonals on xz planes (fixed y)
 for j in range(n):
 if abs(sum(board_state[i, j, i] for i in range(n))) ==3:
 return board_state[0, j,0]
 if abs(sum(board_state[i, j,2-i] for i in range(n))) ==3:
 return board_state[0, j,2]
 # Diagonals on yz planes (fixed x)
 for i in range(n):
 if abs(sum(board_state[i, j, j] for j in range(n))) ==3:
 return board_state[i,0,0]
 if abs(sum(board_state[i, j,2-j] for j in range(n))) ==3:
 return board_state[i,0,2]
 # Main3D diagonals if abs(sum(board_state[i, i, i] for i in range(n))) ==3:
 return board_state[0,0,0]
 if abs(sum(board_state[i, i,2-i] for i in range(n))) ==3:
 return board_state[0,0,2]
 if abs(sum(board_state[i,2-i, i] for i in range(n))) ==3:
 return board_state[0,2,0]
 if abs(sum(board_state[i,2-i,2-i] for i in range(n))) ==3:
 return board_state[0,2,2]
 return0 # No winner def minimax(board_state, depth, alpha, beta, maximizing_player):
 winner = check_winner(board_state)
 if winner ==1: # AI wins return10 - depth if winner == -1: # Opponent wins return depth -10 if len(np.where(board_state ==0)[0]) ==0: # Board full (tie)
 return0 if maximizing_player:
 max_eval = float('-inf')
 for i in range(n):
 for j in range(n):
 for k in range(n):
 if board_state[i, j, k] ==0:
 board_state[i, j, k] =1 eval_score = minimax(board_state, depth +1, alpha, beta, False)
 board_state[i, j, k] =0 max_eval = max(max_eval, eval_score)
 alpha = max(alpha, eval_score)
 if beta <= alpha:
 break # Beta cutoff return max_eval else:
 min_eval = float('inf')
 for i in range(n):
 for j in range(n):
 for k in range(n):
 if board_state[i, j, k] ==0:
 board_state[i, j, k] = -1 eval_score = minimax(board_state, depth +1, alpha, beta, True)
 board_state[i, j, k] =0 min_eval = min(min_eval, eval_score)
 beta = min(beta, eval_score)
 if beta <= alpha:
 break # Alpha cutoff return min_eval # Try to find a winning move directly for cell in empty_cells:
 i, j, k = cell board_array[i, j, k] =1 if check_winner(board_array) ==1:
 board_array[i, j, k] =0 return cell board_array[i, j, k] =0 # Try to block opponent's winning move for cell in empty_cells:
 i, j, k = cell board_array[i, j, k] = -1 if check_winner(board_array) == -1:
 board_array[i, j, k] =0 return cell board_array[i, j, k] =0 # Use minimax to choose best move best_score = float('-inf')
 best_move = empty_cells[0] # Fallback to first empty cell for cell in empty_cells:
 i, j, k = cell board_array[i, j, k] =1 score = minimax(board_array,0, float('-inf'), float('inf'), False)
 board_array[i, j, k] =0 if score > best_score:
 best_score = score best_move = cell return best_move