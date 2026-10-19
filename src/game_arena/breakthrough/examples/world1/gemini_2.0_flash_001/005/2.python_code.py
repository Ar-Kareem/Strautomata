
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    A policy for Breakthrough on an 8x8 board.
    """

    board_size = 8

    def get_legal_moves(piece: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Returns a list of legal moves for a given piece.
        """
        row, col = piece
        moves = []

        if color == 'b':
            forward = row - 1
            direction = -1
            home_row = 0
        else:
            forward = row + 1
            direction = 1
            home_row = 7

        # Move forward
        if 0 <= forward < board_size:
            if (forward, col) not in me and (forward, col) not in opp:
                moves.append((forward, col))

            # Capture diagonally
            if col > 0 and (forward, col - 1) in opp:
                moves.append((forward, col - 1))
            if col < board_size - 1 and (forward, col + 1) in opp:
                moves.append((forward, col + 1))

        return moves

    def evaluate_move(to_row) -> int:
          if color == 'b':
              return 7 - to_row
          else:
              return to_row


    # 1. Check for winning moves
    for piece in me:
        for move in get_legal_moves(piece):
            if color == 'b' and move[0] == 0:
                return (piece, move)
            if color == 'w' and move[0] == 7:
                return (piece, move)
    # 2. Check for capturing moves
    capturing_moves = []
    for piece in me:
        for move in get_legal_moves(piece):
            if move in opp:
                capturing_moves.append((piece, move))

    if capturing_moves:
        best_capture_move = capturing_moves[0]
        best_capture_score = evaluate_move(best_capture_move[1][0])
        for move in capturing_moves[1:]:
            score = evaluate_move(move[1][0])
            if score > best_capture_score:
                best_capture_move = move
                best_capture_score = score
        return best_capture_move

    # 3. If no captures, advance piece that is closest to target row
    advancing_moves = []
    for piece in me:
        for move in get_legal_moves(piece):
          if move not in opp:
            advancing_moves.append((piece, move))
    
    if advancing_moves:
        best_advancing_move = advancing_moves[0]
        best_advancing_score = evaluate_move(best_advancing_move[1][0])
        for move in advancing_moves[1:]:
            score = evaluate_move(move[1][0])
            if score > best_advancing_score:
                best_advancing_move = move
                best_advancing_score = score
        return best_advancing_move

    # If no moves possible (should not happen, but included for safety), return a random valid move
    # This prevents disqualification
    if me:
        start_piece = me[0]
        possible_moves = get_legal_moves(start_piece)
        if possible_moves:
            return (start_piece, random.choice(possible_moves))
    
    # Return a default move that won't break the code in the worst case, though this is unlikely.
    # Prevents disqualification even if 'me' is empty.
    return ((0, 0), (0, 0))

