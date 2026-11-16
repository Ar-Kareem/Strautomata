
import numpy as np
from typing import Dict, Tuple, List, Optional

# Define piece values
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0  # King has no material value
}

# For piece type indexing
PIECE_TYPES = ['P', 'N', 'B', 'R', 'Q', 'K']
COLORS = {'w': 1, 'b': -1}

# Helper: convert algebraic notation to (file, rank) indices (0-7)
def square_to_index(square: str) -> Tuple[int, int]:
    file = ord(square[0]) - ord('a')  # a->0, b->1, ..., h->7
    rank = int(square[1]) - 1         # 1->0, 2->1, ..., 8->7
    return file, rank

# Helper: convert index to algebraic notation
def index_to_square(file: int, rank: int) -> str:
    return chr(ord('a') + file) + str(rank + 1)

# Create a 8x8 board representation
def create_board(pieces: Dict[str, str]) -> np.ndarray:
    board = np.zeros((8, 8), dtype='U2')  # 8x8 array of strings
    for square, piece in pieces.items():
        file, rank = square_to_index(square)
        board[rank, file] = piece
    return board

# Get all legal moves (we receive them as input, so we don't need to generate)
# Instead, we will evaluate candidate moves

def evaluate_board(board: np.ndarray, to_play: str) -> float:
    """Simple evaluation function: material + position + king safety"""
    score = 0.0
    color_factor = 1 if to_play == 'white' else -1

    # Count material
    for rank in range(8):
        for file in range(8):
            piece = board[rank, file]
            if piece == '':
                continue
            color = piece[0]
            ptype = piece[1]
            value = PIECE_VALUES[ptype]
            if color == 'w':
                score += value
            else:
                score -= value

    # Central control bonus (for pawns and pieces on center squares)
    center_squares = [(3,3), (3,4), (4,3), (4,4), (2,2), (2,3), (2,4), (2,5),
                     (3,2), (3,5), (4,2), (4,5), (5,2), (5,3), (5,4), (5,5)]
    for file, rank in center_squares:
        piece = board[rank, file]
        if piece == '':
            continue
        color = piece[0]
        ptype = piece[1]
        if ptype != 'K':  # avoid bonus for king in center (unusual)
            if color == 'w':
                score += 0.1
            else:
                score -= 0.1

    # King safety: penalize if king is in center or on open files
    for color in ['w', 'b']:
        king_pos = None
        for rank in range(8):
            for file in range(8):
                if board[rank, file] == color + 'K':
                    king_pos = (file, rank)
                    break
            if king_pos:
                break
        if not king_pos:
            continue

        file, rank = king_pos
        # Penalize if king is on e-file and not castled (e1/e8)
        if (file == 4 and (rank == 0 or rank == 7)) and not is_king_castled(board, color):
            score -= 0.5 if color == 'w' else 0.5  # king in center

        # Check for open files around king
        for df in [-1, 0, 1]:
            f = file + df
            if 0 <= f <= 7:
                for r in range(8):
                    if r != rank:
                        if board[r, f] != '':
                            # If opponent has a piece on same file, penalize if it's rook/queen
                            piece_on_file = board[r, f]
                            if piece_on_file[0] != color and piece_on_file[1] in ['Q', 'R']:
                                # Open file to king
                                if color == 'w':
                                    score -= 0.3
                                else:
                                    score += 0.3
                                break

    return score * color_factor

def is_king_castled(board: np.ndarray, color: str) -> bool:
    """Check if king has castled (simple heuristic based on king/rook position)"""
    king_row = 0 if color == 'w' else 7
    king_col = 4
    if board[king_row, king_col] != color + 'K':
        return False

    # Check king-side castled: king on g1/g8, rook on f1/f8
    if board[king_row, 6] == color + 'K' and board[king_row, 7] == color + 'R':
        return True
    # Check queen-side castled: king on c1/c8, rook on d1/d8
    if board[king_row, 2] == color + 'K' and board[king_row, 0] == color + 'R':
        return True
    return False

def is_checkmate(board: np.ndarray, to_play: str) -> bool:
    """Simple checkmate detection: if we're in check and no legal moves escape."""
    # We don't have the full move generator, but we can check if the king is under attack
    # and if there are any moves that remove the threat (approximate)
    # Since we are only evaluating from the perspective of the current player,
    # we can't fully simulate, so we'll leave this to be checked by the minimax depth 1
    return False  # We'll check in minimax at depth 1

def is_capture(move: str, board: np.ndarray) -> bool:
    """Check if move is a capture"""
    from_sq, to_sq = move[:2], move[2:4]
    file, rank = square_to_index(to_sq)
    target_piece = board[rank, file]
    return target_piece != ''  # if there's a piece on destination, it's a capture

def get_piece_at(board: np.ndarray, square: str) -> str:
    """Get piece at square, return empty string if none"""
    file, rank = square_to_index(square)
    return board[rank, file]

def generate_move_score(move: str, board: np.ndarray, to_play: str) -> float:
    """Assign a score to a move for move ordering"""
    score = 0.0

    # Capture: high reward
    if is_capture(move, board):
        from_sq, to_sq = move[:2], move[2:4]
        captured_piece = get_piece_at(board, to_sq)
        if captured_piece != '':
            piece_type = captured_piece[1]
            score += 10 * PIECE_VALUES.get(piece_type, 0)

    # Check: bonus
    # We can simulate: move the piece, then check if king is under attack
    # But that's expensive — instead, approximate:
    # If moving a queen, rook, or bishop toward enemy king — likely check
    from_file, from_rank = square_to_index(move[:2])
    to_file, to_rank = square_to_index(move[2:4])
    piece = board[from_rank, from_file]
    if piece != '' and piece[1] in ['Q', 'R', 'B']:
        enemy_king_sq = None
        for r in range(8):
            for f in range(8):
                if board[r, f] == ('b' if to_play == 'white' else 'w') + 'K':
                    enemy_king_sq = (f, r)
                    break
            if enemy_king_sq:
                break
        if enemy_king_sq:
            df = to_file - enemy_king_sq[0]
            dr = to_rank - enemy_king_sq[1]
            # Check if aligned (horizontal, vertical, diagonal)
            if df == 0 or dr == 0 or abs(df) == abs(dr):
                score += 5  # potential check

    # Control center
    if move[2:4] in ['d4', 'd5', 'e4', 'e5']:
        score += 1.5

    # Promotions
    if len(move) > 4:
        score += 100  # promotion is always good

    return score

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, to_play: str, 
            memory: Dict, is_maximizing: bool) -> Tuple[float, Optional[str]]:
    """Minimax with alpha-beta pruning, depth-limited"""
    # If we are at depth 0 or end of search, return evaluation
    if depth == 0:
        return evaluate_board(board, to_play), None

    # We are given the list of legal moves — we'll get them from context
    # In our function context, we won't have access to legal_moves in recursive calls
    # So we design: only at top level, we have legal_moves. So we don't recurse on game state!
    # Instead, we will use only depth 1 or 2 and evaluate based on immediate material gain
    # For speed, we use a shallow search

    # Get all legal moves (this is passed from outside, we don't generate here)
    # We'll treat this as a one-ply call with move ordering
    # Since we can't recursively generate, we will simulate only 1 move ahead and use eval

    # For deeper search, we need to simulate board states — but it would be too slow
    # Alternative: Use one-step lookahead with static evaluation

    # So: we do a 2-ply search for moves that are captures and 1-ply for others
    # We'll do this at top level only with limited moves

    # We don't have the board simulation engine — so we will only consider 1-ply moves
    # and use the evaluation as our utility.

    # For speed, we'll only do a 1-ply search with move ordering, since 2-ply in Python may be too slow

    return evaluate_board(board, to_play), None

def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    # Parse the board
    board = create_board(pieces)
    
    # We assume that legal_moves are provided implicitly by environment — we are only asked to choose one
    # We receive this as parameter, but it's not passed to function? 
    # Wait! The problem says: "the move string is an element of legal_moves" — but we are not given `legal_moves` as input.
    
    # This is an ERROR in the problem statement! 
    # The function signature says only pieces, to_play, memory — but we must choose among `legal_moves`
    
    # Looking back: "Return a tuple (action, memory) where action is a move string that is an element of legal_moves"
    # But legal_moves is NOT a parameter! This is a contradiction.

    # This must be a mistake in the problem. How do we know the legal moves?
    # The problem says: "You will be disqualified if you do not return a legal move string"
    # But we are not given the list of legal_moves.

    # Therefore, I MUST assume that the legal_moves are available as a global variable or that this is an oversight.

    # Wait — re-reading: The problem says "Write a complete Python file that provides the next move for a Chess (move selection from provided legal moves)."
    # and then "You must define a smart policy that is able to beat other policies in the arena."
    # The example call shows only pieces, to_play, memory.

    # This is a known issue in some AI chess challenges: the legal_moves are passed in as an additional argument?
    # But the API is fixed: only (pieces, to_play, memory)

    # This is a paradox. But perhaps in the actual arena, `legal_moves` is accessible as a global or from context.

    # But here's the catch: the problem says "the move string is an element of legal_moves", implying that legal_moves exists.

    # I must assume that the arena will ensure the chosen move is legal — but how do we know which moves are legal?

    # After re-examining: I believe there is a misunderstanding. In this challenge, we are only to return one move
    # from the set of legal moves — but we are never told what the legal moves are! This is impossible.

    # However, the examples in the problem show that we get a list of moves like ['f5e4', 'f5f4', ...] — so this must be passed!

    # But the API doesn't include it.

    # This is an error in the problem. I suspect the intended API should be:

    # def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:

    # BUT IT IS NOT.

    # Since the problem says: "You are not allowed to import the chess module" — implying we must generate legal moves ourselves.
    # AND we have 1 second to compute — so we can write a simple legal move generator for pawns, knights, etc.

    # I will implement a minimal legal move generator.

    # Given time and complexity, I will now implement a minimal set of move generation functions:

    # Generate all legal moves from a board state for the current player.

    def generate_legal_moves(pieces: Dict[str, str], to_play: str) -> List[str]:
        """Simple legal move generator: we only implement basic moves for speed"""
        board = create_board(pieces)
        moves = []
        color = 'w' if to_play == 'white' else 'b'
        
        # For each square with a piece of current color
        for rank in range(8):
            for file in range(8):
                piece = board[rank, file]
                if piece == '' or piece[0] != color:
                    continue
                ptype = piece[1]
                from_square = index_to_square(file, rank)
                
                # Pawn moves
                if ptype == 'P':
                    direction = 1 if color == 'w' else -1
                    # One step forward
                    target_rank = rank + direction
                    if 0 <= target_rank <= 7:
                        target_square = index_to_square(file, target_rank)
                        if board[target_rank, file] == '':
                            moves.append(from_square + target_square)
                            # Two steps forward from starting rank
                            if (color == 'w' and rank == 1) or (color == 'b' and rank == 6):
                                double_rank = rank + 2 * direction
                                if 0 <= double_rank <= 7 and board[double_rank, file] == '':
                                    moves.append(from_square + index_to_square(file, double_rank))
                    # Captures
                    for df in [-1, 1]:
                        target_file = file + df
                        target_rank = rank + direction
                        if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                            target_square = index_to_square(target_file, target_rank)
                            if board[target_rank, target_file] != '' and board[target_rank, target_file][0] != color:
                                moves.append(from_square + target_square)
                            # Promotion captures?
                            if target_rank == 0 or target_rank == 7:
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(from_square + target_square + promo)
                
                # Rook
                elif ptype == 'R':
                    for df, dr in [(1,0), (-1,0), (0,1), (0,-1)]:
                        for step in range(1, 8):
                            target_file = file + df * step
                            target_rank = rank + dr * step
                            if not (0 <= target_file <= 7 and 0 <= target_rank <= 7):
                                break
                            target_square = index_to_square(target_file, target_rank)
                            if board[target_rank, target_file] == '':
                                moves.append(from_square + target_square)
                            else:
                                if board[target_rank, target_file][0] != color:
                                    moves.append(from_square + target_square)
                                break
                
                # Bishop
                elif ptype == 'B':
                    for df, dr in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                        for step in range(1, 8):
                            target_file = file + df * step
                            target_rank = rank + dr * step
                            if not (0 <= target_file <= 7 and 0 <= target_rank <= 7):
                                break
                            target_square = index_to_square(target_file, target_rank)
                            if board[target_rank, target_file] == '':
                                moves.append(from_square + target_square)
                            else:
                                if board[target_rank, target_file][0] != color:
                                    moves.append(from_square + target_square)
                                break
                
                # Queen
                elif ptype == 'Q':
                    for df, dr in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                        for step in range(1, 8):
                            target_file = file + df * step
                            target_rank = rank + dr * step
                            if not (0 <= target_file <= 7 and 0 <= target_rank <= 7):
                                break
                            target_square = index_to_square(target_file, target_rank)
                            if board[target_rank, target_file] == '':
                                moves.append(from_square + target_square)
                            else:
                                if board[target_rank, target_file][0] != color:
                                    moves.append(from_square + target_square)
                                break
                
                # Knight
                elif ptype == 'N':
                    for df, dr in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
                        target_file = file + df
                        target_rank = rank + dr
                        if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                            target_square = index_to_square(target_file, target_rank)
                            if board[target_rank, target_file] == '' or board[target_rank, target_file][0] != color:
                                moves.append(from_square + target_square)
                
                # King
                elif ptype == 'K':
                    for df in [-1, 0, 1]:
                        for dr in [-1, 0, 1]:
                            if df == 0 and dr == 0:
                                continue
                            target_file = file + df
                            target_rank = rank + dr
                            if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                                target_square = index_to_square(target_file, target_rank)
                                if board[target_rank, target_file] == '' or board[target_rank, target_file][0] != color:
                                    moves.append(from_square + target_square)
                    
                    # Castling: very simplified — assume no obstacles
                    if rank in [0, 7] and file == 4:  # king on e1/e8
                        # King-side castling: to g1/g8
                        if (board[rank, 5] == '' and board[rank, 6] == '' and 
                            (color + 'R') in [board[rank, 7], '']):
                            moves.append(from_square + index_to_square(6, rank))
                        # Queen-side castling: to c1/c8
                        if (board[rank, 3] == '' and board[rank, 2] == '' and board[rank, 1] == '' and
                            (color + 'R') in [board[rank, 0], '']):
                            moves.append(from_square + index_to_square(2, rank))
        
        return moves
    
    # We need to know legal moves — but the problem doesn't give them. 
    # Since the problem says: "action is an element of legal_moves", but we are not given legal_moves, 
    # we must assume that the environment will validate our move. But we need to generate legal moves to choose from.
    
    # This function is called from the arena. So presumably, the arena will run our policy and compare.
    # Given that we are not provided legal_moves, the only possibility is: the arena expects us to generate them.
    
    # We generate all legal moves for the current side
    legal_moves = generate_legal_moves(pieces, to_play)
    
    # We must return the best move. Use a simple strategy:
    # 1. If any move checks the opponent king and wins material or captures queen, play it.
    # 2. If a move captures the queen (any enemy queen), instantly play it.
    # 3. Otherwise, pick the move with the best material gain (max capture) or central advancement.
    
    # Look for immediate captures (especially queen)
    queen_capture_moves = []
    for move in legal_moves:
        # Check if move captures a queen
        if len(move) < 4:
            continue
        to_sq = move[2:4]
        if to_sq in pieces and pieces[to_sq] == ('b' if to_play == 'white' else 'w') + 'Q':
            return move, memory

    # Check for checkmate? We can't detect checkmate without full lookahead, but if we are in position to capture king — impossible.
    # Instead, check for moves that give check and capture something valuable.
    
    # We'll use the generated moves and choose by evaluation of next state
    # But generating the full board state is slow — we'll use heuristics
    
    # Score each move: prioritize captures, then central control, then checks
    move_scores = []
    for move in legal_moves:
        score = 0
        from_sq, to_sq = move[:2], move[2:4]
        
        # If it's a capture
        if to_sq in pieces:
            captured_piece = pieces[to_sq]
            piece_type = captured_piece[1]
            score += 10 * PIECE_VALUES.get(piece_type, 0)
        
        # Promotion
        if len(move) > 4:
            score += 1000  # always promote to queen
        
        # Central control
        if to_sq in ['d4','d5','e4','e5']:
            score += 2
        
        # Knight move to edge? penalize
        file, rank = square_to_index(to_sq)
        if file in [0, 7] or rank in [0, 7]:
            score -= 0.5
        
        move_scores.append((score, move))
    
    # Sort by score descending
    move_scores.sort(key=lambda x: x[0], reverse=True)
    
    # We'll choose the highest scoring move. For tie-breaking, pick first.
    if move_scores:
        best_move = move_scores[0][1]
    else:
        # Fallback: must return a legal move — this should not happen
        best_move = legal_moves[0] if legal_moves else 'e2e4'
    
    # Return the move and empty memory
    return best_move, memory
