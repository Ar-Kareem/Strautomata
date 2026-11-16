
import numpy as np
import random
import time

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Chooses the best move for Clobber on a 5x6 grid based on a simple heuristic.
    """
    you = np.array(you).reshape((5, 6))
    opponent = np.array(opponent).reshape((5, 6))

    def get_legal_moves(board, player, opponent):
        """
        Finds all legal moves for the given player on the given board.
        """
        moves = []
        for r in range(5):
            for c in range(6):
                if player[r, c] == 1:
                    # Check up
                    if r > 0 and opponent[r-1, c] == 1:
                        moves.append((r, c, 'U'))
                    # Check down
                    if r < 4 and opponent[r+1, c] == 1:
                        moves.append((r, c, 'D'))
                    # Check left
                    if c > 0 and opponent[r, c-1] == 1:
                        moves.append((r, c, 'L'))
                    # Check right
                    if c < 5 and opponent[r, c+1] == 1:
                        moves.append((r, c, 'R'))
        return moves

    def apply_move(board, player, opponent, move):
        """
        Applies the given move to the board.
        """
        r, c, direction = move
        new_player = np.copy(player)
        new_opponent = np.copy(opponent)

        new_player[r, c] = 0
        if direction == 'U':
            new_player[r-1, c] = 1
            new_opponent[r-1, c] = 0
        elif direction == 'D':
            new_player[r+1, c] = 1
            new_opponent[r+1, c] = 0
        elif direction == 'L':
            new_player[r, c-1] = 1
            new_opponent[r, c-1] = 0
        elif direction == 'R':
            new_player[r, c+1] = 1
            new_opponent[r, c+1] = 0

        return new_player, new_opponent

    def heuristic(player, opponent):
      """
      Simple heuristic to evaluate the board state.
      Counts the number of legal moves for the player minus the number of legal moves for the opponent.
      """
      player_moves = get_legal_moves(board, player, opponent)
      opponent_moves = get_legal_moves(board, opponent, player)
      return len(player_moves) - len(opponent_moves)

    def is_terminal(player, opponent):
      return not get_legal_moves(board, player, opponent)
    
    def minimax(board, player, opponent, depth, maximizing_player, start_time, time_limit=0.9):
      """
      Performs minimax search with limited depth and time.
      """
      if time.time() - start_time > time_limit or depth == 0 or is_terminal(player, opponent):
          return heuristic(player, opponent), None
      
      legal_moves = get_legal_moves(board, player, opponent)
      if not legal_moves:
          return heuristic(player, opponent), None #No legal moves for current player

      if maximizing_player:
          best_score = float('-inf')
          best_move = None
          for move in legal_moves:
              new_player, new_opponent = apply_move(board, player, opponent, move)
              score, _ = minimax(board, new_opponent, new_player, depth - 1, False, start_time, time_limit) #Switch roles and players
              if score > best_score:
                  best_score = score
                  best_move = move
          return best_score, best_move
      else:
          best_score = float('inf')
          best_move = None
          for move in legal_moves:
              new_player, new_opponent = apply_move(board, player, opponent, move)
              score, _ = minimax(board, new_opponent, new_player, depth - 1, True, start_time, time_limit) #Switch roles and players
              if score < best_score:
                  best_score = score
                  best_move = move
          return best_score, best_move

    board = np.zeros((5,6))
    
    # Check for immediate winning moves
    legal_moves = get_legal_moves(board, you, opponent)
    for move in legal_moves:
        new_you, new_opponent = apply_move(board, you, opponent, move)
        if not get_legal_moves(board, new_opponent, new_you):
            return f'{move[0]},{move[1]},{move[2]}'

    start_time = time.time()
    best_move = None
    try:
        _, best_move = minimax(board, you, opponent, depth=3, maximizing_player=True, start_time=start_time)
    except Exception as e:
        print(f"Error during minimax: {e}")
        best_move = None
    
    if best_move:
        return f'{best_move[0]},{best_move[1]},{best_move[2]}'

    # If all else fails, make a random legal move
    if legal_moves:
        move = random.choice(legal_moves)
        return f'{move[0]},{move[1]},{move[2]}'

    # If no legal moves, return a dummy move (shouldn't happen)
    return '0,0,R'  # Indicate no valid move found
