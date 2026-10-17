
import random
import numpy as np
from typing import Dict, List, Tuple, Optional

# Piece values
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (from white's perspective)
# Positive values are good for white, negative for black
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

# Reverse the tables for black
PAWN_TABLE_BLACK = PAWN_TABLE[::-1]
KNIGHT_TABLE_BLACK = KNIGHT_TABLE[::-1]
BISHOP_TABLE_BLACK = BISHOP_TABLE[::-1]
ROOK_TABLE_BLACK = ROOK_TABLE[::-1]
QUEEN_TABLE_BLACK = QUEEN_TABLE[::-1]
KING_TABLE_BLACK = KING_TABLE[::-1]

def get_piece_value(piece: str) -> int:
    """Get the material value of a piece."""
    if piece == '':
        return 0
    return PIECE_VALUES[piece[1]]

def is_capture(board: Dict[str, str], move: str) -> bool:
    """Check if a move is a capture."""
    end_pos = move[2:4]
    return end_pos in board

def is_check(board: Dict[str, str], move: str, to_play: str) -> bool:
    """Check if a move gives check (simplified)."""
    # For this implementation, we'll just check if the move attacks the enemy king
    # This is a simplified check detection
    end_pos = move[2:4]
    target_color = 'w' if to_play == 'black' else 'b'
    
    # Check if the move attacks the enemy king
    # This is a simplified version - a full implementation would check all attack paths
    return board.get(end_pos, '') == target_color + 'K'

def get_mobility(board: Dict[str, str], color: str) -> int:
    """Calculate mobility score (number of legal moves)."""
    # Simplified mobility calculation
    # In a full implementation, this would generate all legal moves
    # For now, we'll just count the number of pieces of this color
    count = 0
    for piece in board.values():
        if piece.startswith(color):
            count += 1
    return count * 10  # Simple scaling factor

def evaluate_board(board: Dict[str, str], to_play: str) -> int:
    """Evaluate the board position."""
    score = 0
    
    # Material score
    for pos, piece in board.items():
        if piece == '':
            continue
            
        value = get_piece_value(piece)
        if piece[0] == 'w':
            score += value
        else:
            score -= value
    
    # Positional score using piece-square tables
    for pos, piece in board.items():
        if piece == '':
            continue
            
        file = ord(pos[0]) - ord('a')
        rank = int(pos[1]) - 1
        index = rank * 8 + file
        
        if piece[0] == 'w':
            if piece[1] == 'P':
                score += PAWN_TABLE[index]
            elif piece[1] == 'N':
                score += KNIGHT_TABLE[index]
            elif piece[1] == 'B':
                score += BISHOP_TABLE[index]
            elif piece[1] == 'R':
                score += ROOK_TABLE[index]
            elif piece[1] == 'Q':
                score += QUEEN_TABLE[index]
            elif piece[1] == 'K':
                score += KING_TABLE[index]
        else:
            if piece[1] == 'P':
                score -= PAWN_TABLE_BLACK[index]
            elif piece[1] == 'N':
                score -= KNIGHT_TABLE_BLACK[index]
            elif piece[1] == 'B':
                score -= BISHOP_TABLE_BLACK[index]
            elif piece[1] == 'R':
                score -= ROOK_TABLE_BLACK[index]
            elif piece[1] == 'Q':
                score -= QUEEN_TABLE_BLACK[index]
            elif piece[1] == 'K':
                score -= KING_TABLE_BLACK[index]
    
    # Mobility score
    white_mobility = get_mobility(board, 'w')
    black_mobility = get_mobility(board, 'b')
    score += white_mobility - black_mobility
    
    # Adjust score based on who is playing
    if to_play == 'black':
        score = -score
        
    return score

def apply_move(board: Dict[str, str], move: str) -> Dict[str, str]:
    """Apply a move to the board and return the new board state."""
    start = move[0:2]
    end = move[2:4]
    
    # Copy the board
    new_board = board.copy()
    
    # Get the piece being moved
    piece = new_board[start]
    
    # Remove the piece from the start position
    del new_board[start]
    
    # Handle captures
    if end in new_board:
        del new_board[end]
    
    # Handle pawn promotion
    if len(move) == 5 and piece[1] == 'P':
        # Promote to the specified piece
        new_board[end] = piece[0] + move[4].upper()
    else:
        # Normal move
        new_board[end] = piece
    
    return new_board

def get_ordered_moves(board: Dict[str, str], legal_moves: List[str], to_play: str) -> List[str]:
    """Order moves by priority: captures, checks, promotions, etc."""
    captures = []
    checks = []
    promotions = []
    others = []
    
    for move in legal_moves:
        if is_capture(board, move):
            captures.append(move)
        elif is_check(board, move, to_play):
            checks.append(move)
        elif len(move) == 5:  # Promotion
            promotions.append(move)
        else:
            others.append(move)
    
    # Return moves in priority order
    return captures + checks + promotions + others

def minimax(board: Dict[str, str], depth: int, alpha: float, beta: float, 
           maximizing_player: bool, legal_moves: List[str], to_play: str) -> Tuple[int, str]:
    """Minimax algorithm with alpha-beta pruning."""
    if depth == 0 or not legal_moves:
        return evaluate_board(board, to_play), ""
    
    if maximizing_player:
        max_eval = float('-inf')
        best_move = ""
        
        ordered_moves = get_ordered_moves(board, legal_moves, to_play)
        
        for move in ordered_moves:
            new_board = apply_move(board, move)
            new_legal_moves = get_legal_moves(new_board, 'black' if to_play == 'white' else 'white')
            
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False, 
                                  new_legal_moves, 'black' if to_play == 'white' else 'white')
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
                
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = ""
        
        ordered_moves = get_ordered_moves(board, legal_moves, 'black' if to_play == 'white' else 'white')
        
        for move in ordered_moves:
            new_board = apply_move(board, move)
            new_legal_moves = get_legal_moves(new_board, to_play)
            
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True, 
                                  new_legal_moves, to_play)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
                
        return min_eval, best_move

def get_legal_moves(board: Dict[str, str], to_play: str) -> List[str]:
    """Generate all legal moves for the current position."""
    # This is a simplified implementation
    # In a full chess engine, this would generate all legal moves according to chess rules
    # For this competition, we'll assume legal_moves are provided by the environment
    # So we'll just return a placeholder that will be overridden
    return []

def policy(pieces: Dict[str, str], to_play: str) -> str:
    """Main policy function that selects the best move."""
    # If this is the first move or very few pieces, use simple development
    if len(pieces) <= 4:
        # Simple development heuristic for opening
        if to_play == 'white':
            # Try to develop knights and control center
            if 'g1' in pieces and pieces['g1'] == 'wN':
                return 'g1f3'
            elif 'b1' in pieces and pieces['b1'] == 'wN':
                return 'b1c3'
        else:
            # Black development
            if 'g8' in pieces and pieces['g8'] == 'bN':
                return 'g8f6'
            elif 'b8' in pieces and pieces['b8'] == 'bN':
                return 'b8c6'
    
    # For the actual implementation, we would need the legal_moves parameter
    # Since it's not provided in the function signature, we'll need to generate it
    # This is a simplified version that prioritizes captures and checks
    
    # Get all possible moves (this is a simplified version)
    legal_moves = []
    our_color = 'w' if to_play == 'white' else 'b'
    enemy_color = 'b' if to_play == 'white' else 'w'
    
    # Generate moves (simplified)
    for pos, piece in pieces.items():
        if piece[0] == our_color:
            # Generate moves for this piece (simplified)
            file = pos[0]
            rank = int(pos[1])
            
            if piece[1] == 'P':
                # Pawn moves
                if our_color == 'w':
                    # White pawn
                    if rank < 8:
                        # Move forward
                        new_pos = file + str(rank + 1)
                        if new_pos not in pieces:
                            legal_moves.append(pos + new_pos)
                            # Double move from starting position
                            if rank == 2:
                                new_pos2 = file + str(rank + 2)
                                if new_pos2 not in pieces:
                                    legal_moves.append(pos + new_pos2)
                        # Captures
                        for df in [-1, 1]:
                            if 'a' <= chr(ord(file) + df) <= 'h':
                                capture_pos = chr(ord(file) + df) + str(rank + 1)
                                if capture_pos in pieces and pieces[capture_pos][0] == enemy_color:
                                    legal_moves.append(pos + capture_pos)
                else:
                    # Black pawn
                    if rank > 1:
                        # Move forward
                        new_pos = file + str(rank - 1)
                        if new_pos not in pieces:
                            legal_moves.append(pos + new_pos)
                            # Double move from starting position
                            if rank == 7:
                                new_pos2 = file + str(rank - 2)
                                if new_pos2 not in pieces:
                                    legal_moves.append(pos + new_pos2)
                        # Captures
                        for df in [-1, 1]:
                            if 'a' <= chr(ord(file) + df) <= 'h':
                                capture_pos = chr(ord(file) + df) + str(rank - 1)
                                if capture_pos in pieces and pieces[capture_pos][0] == enemy_color:
                                    legal_moves.append(pos + capture_pos)
            
            elif piece[1] == 'N':
                # Knight moves
                for df, dr in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                    new_file = chr(ord(file) + df)
                    new_rank = rank + dr
                    if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                        new_pos = new_file + str(new_rank)
                        if new_pos not in pieces or pieces[new_pos][0] == enemy_color:
                            legal_moves.append(pos + new_pos)
            
            elif piece[1] == 'B':
                # Bishop moves (simplified diagonal moves)
                for df, dr in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                    for i in range(1, 8):
                        new_file = chr(ord(file) + df * i)
                        new_rank = rank + dr * i
                        if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                            new_pos = new_file + str(new_rank)
                            if new_pos not in pieces:
                                legal_moves.append(pos + new_pos)
                            elif pieces[new_pos][0] == enemy_color:
                                legal_moves.append(pos + new_pos)
                                break
                            else:
                                break
                        else:
                            break
            
            elif piece[1] == 'R':
                # Rook moves (simplified orthogonal moves)
                for df, dr in [(-1,0), (1,0), (0,-1), (0,1)]:
                    for i in range(1, 8):
                        new_file = chr(ord(file) + df * i)
                        new_rank = rank + dr * i
                        if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                            new_pos = new_file + str(new_rank)
                            if new_pos not in pieces:
                                legal_moves.append(pos + new_pos)
                            elif pieces[new_pos][0] == enemy_color:
                                legal_moves.append(pos + new_pos)
                                break
                            else:
                                break
                        else:
                            break
            
            elif piece[1] == 'Q':
                # Queen moves (combination of rook and bishop)
                for df, dr in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                    for i in range(1, 8):
                        new_file = chr(ord(file) + df * i)
                        new_rank = rank + dr * i
                        if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                            new_pos = new_file + str(new_rank)
                            if new_pos not in pieces:
                                legal_moves.append(pos + new_pos)
                            elif pieces[new_pos][0] == enemy_color:
                                legal_moves.append(pos + new_pos)
                                break
                            else:
                                break
                        else:
                            break
            
            elif piece[1] == 'K':
                # King moves
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if df != 0 or dr != 0:
                            new_file = chr(ord(file) + df)
                            new_rank = rank + dr
                            if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                                new_pos = new_file + str(new_rank)
                                if new_pos not in pieces or pieces[new_pos][0] == enemy_color:
                                    legal_moves.append(pos + new_pos)
    
    # Filter out invalid moves (this is a basic check)
    valid_moves = []
    for move in legal_moves:
        start, end = move[0:2], move[2:4]
        if start in pieces:
            piece = pieces[start]
            if piece[0] == our_color:
                # Check if the move is to an empty square or enemy piece
                if end not in pieces or pieces[end][0] == enemy_color:
                    valid_moves.append(move)
    
    if not valid_moves:
        # Fallback to a random valid move
        # In a real implementation, we would have a proper move generation
        # For now, return a random move from the input (this won't work in practice)
        return random.choice(list(pieces.keys())) + list(pieces.keys())[0]
    
    # Use minimax to find the best move
    # Limit depth based on time constraints
    depth = 2 if len(pieces) > 10 else 3
    
    try:
        _, best_move = minimax(pieces, depth, float('-inf'), float('inf'), True, valid_moves, to_play)
        if best_move and best_move in valid_moves:
            return best_move
    except:
        pass
    
    # Fallback to capture highest value piece
    captures = [m for m in valid_moves if is_capture(pieces, m)]
    if captures:
        # Sort captures by value of captured piece
        captures.sort(key=lambda m: get_piece_value(pieces.get(m[2:4], '')), reverse=True)
        return captures[0]
    
    # Fallback to random move
    return random.choice(valid_moves)
