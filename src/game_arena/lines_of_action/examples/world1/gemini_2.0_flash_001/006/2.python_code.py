
import numpy as np

def get_legal_moves(board, player):
    """
    Returns a list of legal moves for the given player on the given board.
    Each move is a string in the format "from_row,from_col:to_row,to_col".
    """
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r, c] == player:
                # Horizontal moves
                count = np.sum(board != 0)
                for dr in [-1, 1]:
                    for i in range(1, 8):
                        nr, nc = r, c + i * dr
                        if 0 <= nc < 8:
                            if i == count :
                                if board[nr, nc] == 0 or board[nr,nc] == -player:
                                    moves.append(f"{r},{c}:{nr},{nc}")
                                break
                            elif board[nr, nc] == -player:
                                break
                        else:
                            break

                # Vertical moves
                for dr in [-1, 1]:
                    for i in range(1, 8):
                        nr, nc = r + i * dr, c
                        if 0 <= nr < 8:
                            if i == count:
                                if board[nr, nc] == 0 or board[nr,nc] == -player:
                                    moves.append(f"{r},{c}:{nr},{nc}")
                                break
                            elif board[nr, nc] == -player:
                                break
                        else:
                            break

                # Diagonal moves
                for dr in [-1, 1]:
                    for dc in [-1, 1]:
                        for i in range(1, 8):
                            nr, nc = r + i * dr, c + i * dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                if i == count:
                                    if board[nr, nc] == 0 or board[nr,nc] == -player:
                                        moves.append(f"{r},{c}:{nr},{nc}")
                                    break
                                elif board[nr, nc] == -player:
                                    break
                            else:
                                break
    return moves


def evaluate_move(board, move, player):
    """
    Evaluates the given move for the given player on the given board.
    The move is a string in the format "from_row,from_col:to_row,to_col".
    Returns a score for the move. Higher scores are better.
    """
    from_row, from_col = map(int, move.split(':')[0].split(','))
    to_row, to_col = map(int, move.split(':')[1].split(','))

    new_board = board.copy()
    new_board[from_row, from_col] = 0
    piece_captured = False
    if new_board[to_row, to_col] == -player:
        piece_captured = True

    new_board[to_row, to_col] = player

    # Connectivity heuristic: count adjacent friendly pieces
    connectivity = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = to_row + dr, to_col + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr, nc] == player:
                connectivity += 1

    # Opponent capture heuristic: prioritize capturing opponent pieces
    capture_score = 0
    if piece_captured:
        capture_score = 5

    # Isolation heuristic: penalize moves that isolate our pieces
    isolation_score = 0
    num_friendly_pieces = np.sum(new_board == player)
    if num_friendly_pieces > 1:
      isolated = True
      for r in range(8):
          for c in range(8):
              if new_board[r,c] == player:
                   connected = False
                   for dr in [-1, 0, 1]:
                      for dc in [-1, 0, 1]:
                          if dr == 0 and dc == 0:
                              continue
                          nr, nc = r + dr, c + dc
                          if 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr, nc] == player:
                              connected = True
                              break
                      if connected:
                          break
                   if not connected:
                       isolation_score = -10

    return connectivity + capture_score + isolation_score


def policy(board) -> str:
    """
    Returns the next move for the given player on the given board.
    """
    board = np.array(board)
    player = 1
    legal_moves = get_legal_moves(board, player)

    if not legal_moves:
        return "0,0:0,1" # Should not happen in a valid game, but return a legal move

    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        score = evaluate_move(board, move, player)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
