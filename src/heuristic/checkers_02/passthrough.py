from pathlib import Path
import sys

CHECKERS_ROOT = Path(__file__).resolve().parent / "Checkers-Engine" / "src" / "python"
sys.path.append(str(CHECKERS_ROOT))

try:
    import search_engine  # type: ignore
except ImportError as exc:  # pragma: no cover - fail fast with guidance
    raise RuntimeError(
        "search_engine module not found. Build the C extension for your Python "
        "version in `checkers_02/Checkers-Engine/src/python` using "
        "`python Package_engine.py build_ext --inplace`."
    ) from exc

from bitboard_converter import convert_to_bitboard, convert_bit_move  # noqa: E402


def _to_engine_coords(row: int, col: int) -> tuple[int, int]:
    return 7 - row, col


def _from_engine_coords(row: int, col: int) -> tuple[int, int]:
    return 7 - row, col


def _coord_to_action(from_coord: tuple[int, int], to_coord: tuple[int, int]) -> str:
    from_row, from_col = from_coord
    to_row, to_col = to_coord
    return f"{chr(ord('a') + from_col)}{from_row + 1}{chr(ord('a') + to_col)}{to_row + 1}"


def _build_board(my_men, my_kings, opp_men, opp_kings, color: str) -> tuple[list[list[int]], int]:
    board = [[0 for _ in range(8)] for _ in range(8)]

    if color == "w":
        my_man, my_king = 1, 3
        opp_man, opp_king = 2, 4
        player = 1
    else:
        my_man, my_king = 2, 4
        opp_man, opp_king = 1, 3
        player = 2

    for row, col in my_men:
        ey, ex = _to_engine_coords(row, col)
        board[ey][ex] = my_man
    for row, col in my_kings:
        ey, ex = _to_engine_coords(row, col)
        board[ey][ex] = my_king
    for row, col in opp_men:
        ey, ex = _to_engine_coords(row, col)
        board[ey][ex] = opp_man
    for row, col in opp_kings:
        ey, ex = _to_engine_coords(row, col)
        board[ey][ex] = opp_king

    return board, player


def policy(my_men, my_kings, opp_men, opp_kings, color):
    board, player = _build_board(my_men, my_kings, opp_men, opp_kings, color)
    p1, p2, p1k, p2k = convert_to_bitboard(board)
    results = search_engine.search_position(p1, p2, p1k, p2k, player, 0.2, 6)
    if not results or not results[0]:
        raise RuntimeError("search_engine returned no move.")

    move = convert_bit_move(results[0])
    from_coord = _from_engine_coords(move[0][1], move[0][0])
    to_coord = _from_engine_coords(move[1][1], move[1][0])
    action_str = _coord_to_action(from_coord, to_coord)

    return (from_coord, to_coord)
