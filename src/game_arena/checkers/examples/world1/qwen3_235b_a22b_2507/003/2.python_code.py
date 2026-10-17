
import numpy as np
from typing import List, Tuple, Set

# Directions for diagonal moves
# Lower diagonals: left and right (moving down: row decreases)
# Upper diagonals: left and right (moving up: row increases)
LR = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # (drow, dcol)

def is_valid(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def is_dark(r: int, c: int) -> bool:
    return (r + c) % 2 == 1

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple:
    # Combine all opponent pieces for easy lookup
    opp_pieces = set(opp_men + opp_kings)
    my_pieces = set(my_men + my_kings)
    
    # Determine direction: black moves down (row decreases), white up (row increases)
    direction = -1 if color == 'b' else 1
    
    # Build board state for efficient access
    board = np.zeros((8, 8), dtype=int)  # 0: empty, 1: my man, 2: my king, -1: opp man, -2: opp king
    for r, c in my_men:
        board[r, c] = 1
    for r, c in my_kings:
        board[r, c] = 2
    for r, c in opp_men:
        board[r, c] = -1
    for r, c in opp_kings:
        board[r, c] = -2

    def get_moves(r: int, c: int, is_king: bool) -> List[Tuple[int, int]]:
        moves = []
        dirs = LR
        start_dir = 0
        end_dir = 4
        if not is_king:
            # Regular men can only move forward
            if (color == 'b' and r == 7) or (color == 'w' and r == 0):
                # Should be king but just in case
                pass
            else:
                start_dir = 0 if color == 'b' else 2
                end_dir = 2 if color == 'b' else 4
        for i in range(start_dir, end_dir):
            dr, dc = dirs[i]
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc) and board[nr, nc] == 0:
                moves.append((nr, nc))
        return moves

    def get_jumps(r: int, c: int, is_king: bool, visited: Set[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
        jumps = []
        dirs = LR
        start_dir = 0
        end_dir = 4
        if not is_king:
            start_dir = 0 if color == 'b' else 2
            end_dir = 2 if color == 'b' else 4
        for i in range(start_dir, end_dir):
            dr, dc = dirs[i]
            mr, mc = r + dr, c + dc  # square we jump over
            nr, nc = r + 2*dr, c + 2*dc  # landing square
            if is_valid(mr, mc) and is_valid(nr, nc) and board[mr, mc] < 0 and board[nr, nc] == 0:
                if (nr, nc) in visited:
                    continue
                # Make copy of board
                new_board = board.copy()
                new_board[r, c] = 0
                new_board[mr, mc] = 0
                # Check if becomes king
                becomes_king = (is_king or 
                               (not is_king and 
                                ((color == 'b' and nr == 0) or (color == 'w' and nr == 7))))
                new_board[nr, nc] = 2 if becomes_king else 1
                # Recursively get further jumps
                next_visited = visited | {(nr, nc)}
                next_jumps = get_jumps(nr, nc, becomes_king, next_visited)
                if not next_jumps:
                    jumps.append([(nr, nc)])
                else:
                    for seq in next_jumps:
                        jumps.append([(nr, nc)] + seq)
        return jumps

    def get_all_moves() -> Tuple[List, List]:
        # Returns (captures, non_captures)
        captures = []
        non_captures = []

        # Regular moves
        for r, c in my_men:
            moves = get_moves(r, c)
            for move in moves:
                # Check if it becomes king
                becomes_king = (color == 'b' and move[0] == 0) or (color == 'w' and move[0] == 7)
                non_captures.append(((r, c), [move], becomes_king))
        
        for r, c in my_kings:
            moves = get_moves(r, c, True)
            for move in moves:
                non_captures.append(((r, c), [move], False))  # already king

        # Captures
        for r, c in my_men:
            jumps = get_jumps(r, c, False, {(r, c)})
            for jump_seq in jumps:
                # Determine if becomes king during the sequence
                becomes_king = False
                for (nr, nc) in jump_seq:
                    if (color == 'b' and nr == 0) or (color == 'w' and nc == 7):
                        becomes_king = True
                        break
                captures.append(((r, c), jump_seq, becomes_king))
        
        for r, c in my_kings:
            jumps = get_jumps(r, c, True, {(r, c)})
            for jump_seq in jumps:
                captures.append(((r, c), jump_seq, False))

        return captures, non_captures

    def evaluate() -> float:
        score = 0
        # Material weights
        score += len(my_men) * 1.0
        score += len(my_kings) * 1.5
        score -= len(opp_men) * 1.0
        score -= len(opp_kings) * 1.5

        # Positional weights: encourage advancing
        for r, c in my_men:
            if color == 'b':
                score += r / 7.0  # higher row is better
            else:
                score += (7 - r) / 7.0  # lower row is better
        
        for r, c in opp_men:
            if color == 'b':
                score -= (7 - r) / 7.0
            else:
                score -= r / 7.0

        # Edge control bonus
        for r, c in my_pieces:
            if r == 0 or r == 7 or c == 0 or c == 7:
                score += 0.1
        
        for r, c in opp_pieces:
            if r == 0 or r == 7 or c == 0 or c == 7:
                score -= 0.1

        return score

    def minimax(depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        if depth == 0:
            return evaluate()

        # Get moves for current player or opponent
        if maximizing:
            moves = get_all_moves()[0]  # Only captures if available, but in minimax we assume turn alternation
            # Actually, we are always maximizing for my player, but we need opponent moves when maximizing=False
            # So we have to reframe: when maximizing is True, it's my turn; False, opponent's turn
            # But we are assuming the function is called only for my turn. So we only need to simulate one full move.
            # For efficiency, we only go one level deep for full minimax.
            pass

        # For simplicity, we only do one level of minimax
        # Instead of full minimax, we use greedy with lookahead for captures and evaluate
        # But we must return a move. So we do:
        # If captures exist, choose the longest capture or highest evaluation
        # Otherwise, choose move with highest evaluation

        # Let's instead do one level: evaluate all possible moves and pick best
        # But with minimax we need to simulate opponent response
        # Given time, we do depth 1 minimax: I move, then opponent best response, then evaluate

        # Reimplement inside a helper
        pass

    # Simple greedy with one-step lookahead: if captures, pick best capture
    captures, non_captures = get_all_moves()
    
    if captures:
        # Choose capture with most pieces jumped, then by evaluation
        best_capture = None
        best_score = -np.inf
        for (fr, fc), jumps, becomes_king in captures:
            # Simulate the capture
            new_board = board.copy()
            r, c = fr, fc
            for (nr, nc) in jumps:
                # Remove opponent piece in between
                mr, mc = (r + nr) // 2, (c + nc) // 2
                new_board[mr, mc] = 0
                new_board[r, c] = 0
                new_board[nr, nc] = 2 if becomes_king else 1
                r, c = nr, nc
            # Evaluate
            score = evaluate_board_from_pieces(new_board)
            if score > best_score:
                best_score = score
                best_capture = ((fr, fc), jumps[0])  # return only the first step
        if best_capture:
            return best_capture

    # If no captures, choose non-capture with best eval
    best_move = None
    best_score = -np.inf
    for (fr, fc), moves, becomes_king in non_captures:
        for (tr, tc) in moves:
            new_board = board.copy()
            new_board[fr, fc] = 0
            if becomes_king:
                new_board[tr, tc] = 2
            else:
                new_board[tr, tc] = 1
            score = evaluate_board_from_pieces(new_board)
            if score > best_score:
                best_score = score
                best_move = ((fr, fc), (tr, tc))
    
    # Fallback: if no moves, return (0,0) to (0,0) — should not happen
    if best_move is None:
        # Try to return any valid move
        for r in range(8):
            for c in range(8):
                if board[r, c] > 0:
                    moves = get_moves(r, c, board[r, c] == 2)
                    if moves:
                        return ((r, c), moves[0])
        return ((0,0), (0,0))

    return best_move

def evaluate_board_from_pieces(board: np.ndarray) -> float:
    # Recompute evaluation from board
    my_men_score = 0
    my_kings_score = 0
    opp_men_score = 0
    opp_kings_score = 0
    my_pieces = 0
    opp_pieces = 0
    score = 0.0
    for r in range(8):
        for c in range(8):
            if board[r, c] == 1:
                my_men_score += 1
                my_pieces += 1
                # Positional: encourage center and advancement
                if color == 'b':
                    score += r / 7.0
                else:
                    score += (7 - r) / 7.0
                if r == 0 or r == 7 or c == 0 or c == 7:
                    score += 0.05
            elif board[r, c] == 2:
                my_kings_score += 1.5
                my_pieces += 1
                if r == 0 or r == 7 or c == 0 or c == 7:
                    score += 0.05
            elif board[r, c] == -1:
                opp_men_score += 1
                opp_pieces += 1
                if color == 'b':
                    score -= (7 - r) / 7.0
                else:
                    score -= r / 7.0
                if r == 0 or r == 7 or c == 0 or c == 7:
                    score -= 0.05
            elif board[r, c] == -2:
                opp_kings_score += 1.5
                opp_pieces += 1
                if r == 0 or r == 7 or c == 0 or c == 7:
                    score -= 0.05
    score += my_men_score + my_kings_score - opp_men_score - opp_kings_score
    # Bonus for having more pieces
    if my_pieces > opp_pieces:
        score += 0.2
    elif my_pieces < opp_pieces:
        score -= 0.2
    return score

# Note: The above code has a bug in scope of 'color' in evaluate_board_from_pieces
# Let's fix: pass color to evaluate_board_from_pieces

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple:
    # Combine all opponent pieces for easy lookup
    opp_pieces = set(opp_men + opp_kings)
    my_pieces_set = set(my_men + my_kings)
    
    # Determine direction: black moves down (row decreases), white up (row increases)
    direction = -1 if color == 'b' else 1
    
    # Build board state for efficient access
    board = np.zeros((8, 8), dtype=int)  # 0: empty, 1: my man, 2: my king, -1: opp man, -2: opp king
    for r, c in my_men:
        board[r, c] = 1
    for r, c in my_kings:
        board[r, c] = 2
    for r, c in opp_men:
        board[r, c] = -1
    for r, c in opp_kings:
        board[r, c] = -2

    def get_moves(r: int, c: int, is_king: bool) -> List[Tuple[int, int]]:
        moves = []
        start_dir = 0
        end_dir = 4
        if not is_king:
            # Regular men can only move forward
            if (color == 'b' and r == 7) or (color == 'w' and r == 0):
                # Should be king, but handle just in case
                is_king = True
            else:
                start_dir = 0 if color == 'b' else 2
                end_dir = 2 if color == 'b' else 4
        for i in range(start_dir, end_dir):
            dr, dc = LR[i]
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc) and board[nr, nc] == 0:
                moves.append((nr, nc))
        return moves

    def get_jumps(r: int, c: int, is_king: bool, visited: Set[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
        jumps = []
        start_dir = 0
        end_dir = 4
        if not is_king:
            start_dir = 0 if color == 'b' else 2
            end_dir = 2 if color == 'b' else 4
        for i in range(start_dir, end_dir):
            dr, dc = LR[i]
            mr, mc = r + dr, c + dc  # square we jump over
            nr, nc = r + 2*dr, c + 2*dc  # landing square
            if is_valid(mr, mc) and is_valid(nr, nc) and board[mr, mc] < 0 and board[nr, nc] == 0:
                if (nr, nc) in visited:
                    continue
                # Recursively get further jumps
                next_visited = visited | {(nr, nc)}
                next_jumps = get_jumps(nr, nc, is_king or ((color=='b' and nr==0) or (color=='w' and nr==7)), next_visited)
                if not next_jumps:
                    jumps.append([(nr, nc)])
                else:
                    for seq in next_jumps:
                        jumps.append([(nr, nc)] + seq)
        return jumps

    def get_all_moves() -> Tuple[List, List]:
        captures = []
        non_captures = []

        # Non-capture moves
        for r, c in my_men:
            moves = get_moves(r, c, False)
            for move in moves:
                becomes_king = (color == 'b' and move[0] == 0) or (color == 'w' and move[0] == 7)
                non_captures.append(((r, c), [move], becomes_king))
        
        for r, c in my_kings:
            moves = get_moves(r, c, True)
            for move in moves:
                non_captures.append(((r, c), [move], False))

        # Capture moves
        for r, c in my_men:
            jumps = get_jumps(r, c, False, {(r, c)})
            for jump_seq in jumps:
                becomes_king = any((color=='b' and nr==0) or (color=='w' and nr==7) for (nr, nc) in jump_seq)
                captures.append(((r, c), jump_seq, becomes_king))
        
        for r, c in my_kings:
            jumps = get_jumps(r, c, True, {(r, c)})
            for jump_seq in jumps:
                captures.append(((r, c), jump_seq, False))

        return captures, non_captures

    def evaluate_board(board: np.ndarray) -> float:
        score = 0.0
        my_men_count = 0
        my_king_count = 0
        opp_men_count = 0
        opp_king_count = 0
        for r in range(8):
            for c in range(8):
                piece = board[r, c]
                if piece == 1:  # my man
                    my_men_count += 1
                    if (r == 0 or r == 7 or c == 0 or c == 7):
                        score += 0.05
                elif piece == 2:  # my king
                    my_king_count += 1
                    if (r == 0 or r == 7 or c == 0 or c == 7):
                        score += 0.05
                elif piece == -1:  # opp man
                    opp_men_count += 1
                    if (r == 0 or r == 7 or c == 0 or c == 7):
                        score -= 0.05
                elif piece == -2:  # opp king
                    opp_king_count += 1
                    if (r == 0 or r == 7 or c == 0 or c == 7):
                        score -= 0.05

        # Material
        score += my_men_count * 1.0
        score += my_king_count * 1.5
        score -= opp_men_count * 1.0
        score -= opp_king_count * 1.5

        # Positional: advancement
        for r in range(8):
            weight = (r / 7.0) if color == 'b' else ((7 - r) / 7.0)
            for c in range(8):
                if board[r, c] == 1:  # my man
                    score += weight
                elif board[r, c] == -1:  # opp man
                    score -= (1 - weight)

        # Piece count bonus
        my_total = my_men_count + my_king_count
        opp_total = opp_men_count + opp_king_count
        if my_total > opp_total:
            score += 0.2
        elif my_total < opp_total:
            score -= 0.2

        return score

    # Get available moves
    captures, non_captures = get_all_moves()
    
    if captures:
        best_move = None
        best_score = -np.inf
        for (fr, fc), jump_seq, becomes_king in captures:
            # Simulate capture
            new_board = board.copy()
            r, c = fr, fc
            captured = []
            for (nr, nc) in jump_seq:
                mr, mc = (r + nr) // 2, (c + nc) // 2
                captured.append((mr, mc))
                new_board[mr, mc] = 0
                new_board[r, c] = 0
                new_board[nr, nc] = 2 if (becomes_king or (color=='b' and nr==0) or (color=='w' and nr==7)) else 1
                r, c = nr, nc
            # Evaluate
            score = evaluate_board(new_board)
            if score > best_score:
                best_score = score
                best_move = ((fr, fc), jump_seq[0])
        if best_move:
            return best_move

    # No captures: choose best non-capture
    if non_captures:
        best_move = None
        best_score = -np.inf
        for (fr, fc), moves, becomes_king in non_captures:
            for (tr, tc) in moves:
                new_board = board.copy()
                new_board[fr, fc] = 0
                new_board[tr, tc] = 2 if becomes_king else 1
                score = evaluate_board(new_board)
                if score > best_score:
                    best_score = score
                    best_move = ((fr, fc), (tr, tc))
        if best_move:
            return best_move

    # Fallback: generate any valid move
    for r in range(8):
        for c in range(8):
            if board[r, c] > 0:
                is_king = (board[r, c] == 2)
                moves = get_moves(r, c, is_king)
                for move in moves:
                    return ((r, c), move)
    
    # Last fallback
    return ((0,0), (0,0))
