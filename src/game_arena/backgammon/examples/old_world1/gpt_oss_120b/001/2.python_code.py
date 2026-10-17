
import copy
from typing import List, Tuple, Union, Optional, Dict

def policy(state: dict) -> str:
    """
    Returns a legal Backgammon move for the given state.
    The move format is <ORDER>:<FROM1>,<FROM2>.
    """
    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    def board_copy(board: dict) -> dict:
        """deep copy of a board dictionary (lists are copied)."""
        return {
            'my_pts': board['my_pts'][:],
            'opp_pts': board['opp_pts'][:],
            'my_bar': board['my_bar'],
            'opp_bar': board['opp_bar'],
            'my_off': board['my_off'],
            'opp_off': board['opp_off'],
        }

    def dest(start: Union[int, str], die: int) -> int:
        """Destination index for a move."""
        if start == 'B':               # entry from the bar
            return 24 - die            # player 0 moves from bar to 24-die
        else:
            return start - die

    def all_in_home(board: dict) -> bool:
        """True if every my checker is on points 0..5 (home)."""
        # No checker on points 6..23
        return all(p == 0 for p in board['my_pts'][6:])

    def higher_point_present(board: dict, idx: int) -> bool:
        """
        For bearing off from idx (0..5) check that there is no checker on a
        higher home point (idx+1 .. 5).
        """
        return any(board['my_pts'][j] > 0 for j in range(idx + 1, 6))

    def can_move(board: dict, start: Union[int, str], die: int) -> bool:
        """
        Determines whether a checker at `start` can be moved using `die`.
        """
        # bar handling
        if start == 'B':
            if board['my_bar'] == 0:
                return False
            dest_idx = dest('B', die)
            # destination blocked by two opponent checkers?
            return board['opp_pts'][dest_idx] < 2
        # point handling
        if board['my_pts'][start] == 0:
            return False
        dest_idx = dest(start, die)
        if dest_idx >= 0:
            # normal move
            return board['opp_pts'][dest_idx] < 2
        else:
            # bearing off
            if not all_in_home(board):
                return False
            # proper bearing‑off rule: cannot bear off from a lower point
            # if there are checkers on higher points
            if higher_point_present(board, start):
                return False
            return True

    def possible_sources(board: dict, die: int) -> List[Union[int, str]]:
        """
        Returns an ordered list of start locations that can be moved with `die`.
        Order favours:
          * bar,
          * hits,
          * bearing off,
          * otherwise farthest point first.
        """
        sources: List[Union[int, str]] = []

        # Bar must be cleared first
        if board['my_bar'] > 0:
            if can_move(board, 'B', die):
                sources.append('B')
            return sources  # no other moves allowed while on the bar

        # Points (iterate from farthest to nearest)
        for i in range(23, -1, -1):
            if board['my_pts'][i] == 0:
                continue
            dest_idx = dest(i, die)
            if dest_idx >= 0:
                if board['opp_pts'][dest_idx] < 2:
                    # Prefer hits
                    if board['opp_pts'][dest_idx] == 1:
                        sources.insert(0, i)  # hits first
                    else:
                        sources.append(i)
            else:
                # Bearing off candidate
                if all_in_home(board) and not higher_point_present(board, i):
                    sources.append(i)
        return sources

    def apply_move(board: dict, start: Union[int, str], die: int) -> dict:
        """Executes a move and returns the resulting board."""
        new = board_copy(board)

        if start == 'B':
            new['my_bar'] -= 1
            d = dest('B', die)
        else:
            new['my_pts'][start] -= 1
            d = dest(start, die)

        if d < 0:
            # bearing off
            new['my_off'] += 1
            return new

        # hit?
        if new['opp_pts'][d] == 1:
            new['opp_pts'][d] = 0
            new['opp_bar'] += 1
        # place my checker
        new['my_pts'][d] += 1
        return new

    def token(src: Union[int, str]) -> str:
        """Converts a source into the required string token."""
        if src == 'B':
            return 'B'
        if src == 'P':
            return 'P'
        return f'A{src}'

    # ----------------------------------------------------------------------
    # Main move search
    # ----------------------------------------------------------------------
    # an internal board representation
    board: Dict[str, Union[List[int], int]] = {
        'my_pts': state['my_pts'][:],
        'opp_pts': state['opp_pts'][:],
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off'],
    }

    dice = state['dice']
    # Normal backgammon always provides 2 dice, but handle the degenerate case.
    if len(dice) == 0:
        return "H:P,P"
    if len(dice) == 1:
        high = low = dice[0]
    else:
        high = max(dice)
        low = min(dice)

    def find_pair(board0: dict, d1: int, d2: int,
                  order_char: str) -> Optional[Tuple[Union[int, str], Union[int, str]]]:
        """
        Tries to play die d1 first, then d2.
        Returns (src1, src2) where srcX may be 'P' (pass) if that die cannot be used.
        """
        # Try to play both dice
        for src1 in possible_sources(board0, d1):
            b1 = apply_move(board0, src1, d1)
            src2_candidates = possible_sources(b1, d2)
            if src2_candidates:
                src2 = src2_candidates[0]
                return src1, src2

        # No pair found – check if only one die can be played
        src1_only = possible_sources(board0, d1)
        if src1_only:
            return src1_only[0], 'P'

        src2_only = possible_sources(board0, d2)
        if src2_only:
            # Higher die not usable, lower die is.  Use pass for the first slot.
            return 'P', src2_only[0]

        return None

    # Try order H (higher die first)
    result = find_pair(board, high, low, 'H')
    if result is not None:
        src1, src2 = result
        return f"H:{token(src1)},{token(src2)}"

    # Try order L (lower die first)
    result = find_pair(board, low, high, 'L')
    if result is not None:
        src1, src2 = result
        return f"L:{token(src1)},{token(src2)}"

    # No legal move at all – pass
    return "H:P,P"
