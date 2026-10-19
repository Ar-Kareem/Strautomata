
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Helper function to check if a square is under attack
    def is_attacked(board, square, color):
        for sq, piece in board.items():
            if piece[0] == color:
                if can_move(piece, sq, square, board):
                    return True
        return False

    # Helper function to check if a piece can move to a target square
    def can_move(piece, src, target, board):
        piece_type = piece[1]
        color = piece[0]
        # Handle pawn moves
        if piece_type == 'P':
            if color == 'w':
                # White pawn moves
                if target == (chr(ord(src[0]) + 1), int(src[1]) + 1) and board.get(target) and board[target][0] == 'b':
                    return True
                if target == (chr(ord(src[0]) - 1), int(src[1]) + 1) and board.get(target) and board[target][0] == 'b':
                    return True
                if target == (src[0], int(src[1]) + 1) and not board.get(target):
                    return True
                if src[1] == '2' and target == (src[0], '4') and not board.get(target) and not board.get((src[0], '3')):
                    return True
            else:
                # Black pawn moves
                if target == (chr(ord(src[0]) + 1), int(src[1]) - 1) and board.get(target) and board[target][0] == 'w':
                    return True
                if target == (chr(ord(src[0]) - 1), int(src[1]) - 1) and board.get(target) and board[target][0] == 'w':
                    return True
                if target == (src[0], int(src[1]) - 1) and not board.get(target):
                    return True
                if src[1] == '7' and target == (src[0], '5') and not board.get(target) and not board.get((src[0], '6')):
                    return True
        # Handle other piece types
        elif piece_type in 'RQBN':
            directions = {'R': [(0,1), (0,-1), (1,0), (-1,0)],
                          'Q': [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)],
                          'B': [(1,1), (1,-1), (-1,1), (-1,-1)],
                          'N': [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]}
            for dx, dy in directions[piece_type]:
                x, y = src[0] + dx, int(src[1]) + dy
                while 1 <= x <= 'h' and 1 <= y <= 8:
                    sq = f"{x}{y}"
                    if sq == target:
                        return True
                    if board.get(sq):
                        break
                    x += dx
                    y += dy
        return False

    # Evaluate material balance
    def evaluate_material(board, color):
        values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
        score = 0
        for sq, piece in board.items():
            if piece[0] == color:
                score += values.get(piece[1], 0)
        return score

    # Generate all legal moves
    moves = []
    for sq, piece in pieces.items():
        color = piece[0]
        if color != to_play:
            continue
        piece_type = piece[1]
        if piece_type == 'P':
            # Pawn moves
            if color == 'w':
                # Forward moves
                for dx in [1, 2]:
                    target = (chr(ord(sq[0]) + dx), int(sq[1]) + 1)
                    if 1 <= int(target[1]) <= 8:
                        target_sq = f"{target[0]}{target[1]}"
                        if not board.get(target_sq):
                            moves.append(f"{sq}{target_sq}")
                        elif board[target_sq][0] == 'b':
                            moves.append(f"{sq}{target_sq}")
                # Captures
                for dx in [1, -1]:
                    target = (chr(ord(sq[0]) + dx), int(sq[1]) + 1)
                    if 1 <= int(target[1]) <= 8:
                        target_sq = f"{target[0]}{target[1]}"
                        if board.get(target_sq) and board[target_sq][0] == 'b':
                            moves.append(f"{sq}{target_sq}")
            else:
                # Black pawn moves
                for dx in [1, 2]:
                    target = (chr(ord(sq[0]) + dx), int(sq[1]) - 1)
                    if 1 <= int(target[1]) <= 8:
                        target_sq = f"{target[0]}{target[1]}"
                        if not board.get(target_sq):
                            moves.append(f"{sq}{target_sq}")
                        elif board[target_sq][0] == 'w':
                            moves.append(f"{sq}{target_sq}")
                # Captures
                for dx in [1, -1]:
                    target = (chr(ord(sq[0]) + dx), int(sq[1]) - 1)
                    if 1 <= int(target[1]) <= 8:
                        target_sq = f"{target[0]}{target[1]}"
                        if board.get(target_sq) and board[target_sq][0] == 'w':
                            moves.append(f"{sq}{target_sq}")
        elif piece_type in 'RQBN':
            # Generate moves for other pieces
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                x, y = ord(sq[0]) + dx, int(sq[1]) + dy
                while 1 <= x <= ord('h') and 1 <= y <= 8:
                    target = f"{chr(x)}{y}"
                    if board.get(target):
                        if board[target][0] != color:
                            moves.append(f"{sq}{target}")
                        break
                    moves.append(f"{sq}{target}")
                    x += dx
                    y += dy
            # Knights
            if piece_type == 'N':
                for dx, dy in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
                    x, y = ord(sq[0]) + dx, int(sq[1]) + dy
                    if 1 <= x <= ord('h') and 1 <= y <= 8:
                        target = f"{chr(x)}{y}"
                        if board.get(target) and board[target][0] != color:
                            moves.append(f"{sq}{target}")
    # Filter legal moves and evaluate
    best_move = None
    best_score = -float('inf')
    for move in moves:
        src, target = move[0:2], move[2:4]
        # Simulate move
        new_board = pieces.copy()
        new_board[target] = new_board[src]
        del new_board[src]
        # Check for checks
        if to_play == 'white':
            if is_attacked(new_board, 'e8', 'b'):
                continue
        else:
            if is_attacked(new_board, 'e1', 'w'):
                continue
        # Evaluate material
        material_score = evaluate_material(new_board, to_play)
       