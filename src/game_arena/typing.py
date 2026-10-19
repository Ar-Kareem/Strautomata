from typing import Any, Callable, Optional, Union, Literal, NotRequired, TypedDict
from pathlib import Path
import time


PolicyFn = Callable[[Any], int]
Player = tuple[str, PolicyFn]
BotPath = tuple[str, Path]
BotPairGames = list[tuple[BotPath, BotPath, int]]

_Winner = Union[int, Literal["timeout", "error", "draw"]]

class PartialMatchResults(TypedDict):
    done: bool
    winner: _Winner
    player_err_counts: list[int]
    exception: NotRequired[str]
    exception_traceback: NotRequired[str]
    other: NotRequired[dict[str, Any]]

class MatchResults(TypedDict):
    name0: str
    name1: str
    seed: Optional[int]
    start_timestamp: str  # YYYY-MM-DD HH:MM:SS
    time_elapsed: float
    done: bool  # copied from inner_results if available
    winner: _Winner  # copied from inner_results if available
    action_history: str

    r: Optional[PartialMatchResults]  # the internal results of the game
    exception: NotRequired[str]
    exception_traceback: NotRequired[str]
    timeout_hit: NotRequired[tuple[str, float]]

def init_match_results(bot_names: list[str], seed: Optional[int]) -> MatchResults:
    assert len(bot_names) == 2, f"Currently the typehint only supports 2 player games"
    return MatchResults(
        # **{f'name{i}': p[0] for i, p in enumerate(bot_paths)},
        name0=bot_names[0],
        name1=bot_names[1],
        seed=seed,
        start_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        # below will be updated later
        time_elapsed=-1.0,
        done=False,
        winner='error',
        action_history='',
        r=None,
    )