import sys
import time
import json
import math
import random
import argparse
import traceback
import inspect
from typing import Any, Optional
from datetime import datetime, timezone
from collections import defaultdict

import pandas as pd
import numpy as np

from game_arena.base import Game, Player, run_policy_with_timeout, BotPolicyError
from game_arena.utils import setup_logging, get_config_file, get_game, get_examples_dir, get_root_path, get_policy_fn_with_memory, get_bot_paths_from_world
from game_arena.prompter import send_chat, get_openrouter_models, OpenRouterModel


logger = setup_logging("logs/live_play.log", "live_play", to_stdout=True)
error_logger = setup_logging("logs/live_play_error.log", "live_play_error", to_stdout=True)

LIVE_RESULTS_DIR = 'results_side_experiments/results_live'
LIVE_UNSAVED_DIR = 'results_side_experiments/results_live_unsaved'


_GAME_WORLD_TO_NAME = {
    ('tic_tac_toe_3d', 'world1'): '3D TTT',
    ('tic_tac_toe', 'world1'): '3x3 TTT',
    ('tic_tac_toe', 'world2'): '4x4 TTT',
    ('blackjack', 'world1'): 'Blackjack',
    ('battleships', 'world1'): 'Battleships',
    ('connect4', 'world1'): 'Connect4',
    ('lines_of_action', 'world1'): 'LoA',
    ('mancala', 'world1'): 'Mancala',
    ('clobber', 'world1'): 'Clobber',
    ('pentago', 'world1'): 'Pentago',
    ('amazons', 'world1'): 'Amazons',
    ('backgammon', 'world1'): 'Backgammon',
    ('nim', 'world1'): 'Nim',
    ('dots_and_boxes', 'world1'): 'Dots&B',
    ('chess', 'world1'): 'Chess',
    ('chess', 'worlduci1'): 'Chess UCI',
    ('breakthrough', 'world1'): 'Breakthrough',
    ('hex', 'world1'): 'Hex',
    ('havannah', 'world1'): 'Havannah',
    ('go', 'world1'): 'Go',
    ('checkers', 'world1'): 'Checkers',
}


def get_live_play_counts(game_world: str):
    live_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # llm_name -> bot_name -> count per color
    live_dir = get_root_path() / LIVE_RESULTS_DIR
    for fp in live_dir.glob(f"*/{game_world}/*.json"):
        with open(fp, "r") as f:
            data = json.load(f)
        if data['name0'].startswith('LLM_'):
            llm_name = data['name0']
            bot_name = data['name1']
            llm_color = 'A'
        elif data['name1'].startswith('LLM_'):
            llm_name = data['name1']
            bot_name = data['name0']
            llm_color = 'B'
        else:
            raise ValueError(f"Unknown model name: {data['name0']} {data['name1']}")
        live_counts[llm_name][bot_name][llm_color] += 1
    return live_counts


class IllegalMoveForfeit(Exception):
    """The LLM used all its attempts for a turn on illegal moves."""


def play_game_live(game: Game, players: list[Player]) -> dict[str, Any]:
    player_err_counts = [0] * len(players)
    json_history = []
    while not game.is_done():
        current_player = game.current_player()
        if players[current_player][0].startswith('LLM_') and hasattr(game, 'live_play_observation'): # type: ignore
            kwargs = game.live_play_observation() # type: ignore
        else:
            kwargs = game.get_observation()
        assert current_player >= 0 and current_player < len(players), "Current player is out of range"
        name = players[current_player][0]
        policy = players[current_player][1]
        if '_debug_legal_moves' in inspect.signature(policy).parameters:
            kwargs['_debug_legal_moves'] = game.get_legal_moves()
        kwargs_str = kwargs_to_str(kwargs)
        json_history.append({'type': 'observation', 'kwargs': kwargs_str, 'current_player': current_player, 'name': name})
        policy_returned = False
        try:
            _step_name = 'calling policy() function'
            if players[current_player][0].startswith('LLM_'):
                action_str = policy(**kwargs)  # type: ignore
            else:
                action_str = run_policy_with_timeout(policy, kwargs, 30)  # 30 seconds timeout
            policy_returned = True
            json_history.append({'type': 'move', 'action': kwargs_to_str(action_str), 'current_player': current_player, 'name': name})
            _step_name = f'calling get_move() from policy output: {action_str}'
            action = game.get_move(action_str)
            _step_name = f'calling game_step() with action: {action}'
            game.game_step(action)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            player_err_counts[current_player] += 1
            e_str = f"Error in play_game. Game: <game>{game.__class__.__name__}</game> Player: <player>{name}</player> at step: <step>{_step_name}</step>: <exception>{traceback.format_exc()}</exception>"
            json_history.append({'type': 'error', 'error': str(e), 'traceback': traceback.format_exc(), 'game': game.__class__.__name__, 'step': _step_name, 'current_player': current_player, 'name': name})
            error_logger.error(e_str)
            # forfeit: the error is the erring player's own fault (counts as its loss); otherwise it is the harness / API
            if name.startswith('LLM_'):
                forfeit = isinstance(e, IllegalMoveForfeit)
            else:  # the bot returned an invalid move, or its code raised / hung / died
                forfeit = policy_returned or isinstance(e, BotPolicyError)
            return {
                'player_err_counts': player_err_counts,
                'forfeit': forfeit,
                **game.get_final_stats(),
                'exception': str(e),
                'exception_traceback': traceback.format_exc(),
                'json_history': json_history,
            }
    final_stats = game.get_final_stats()
    json_history.append({'type': 'finished', 'final_stats': final_stats})
    return {
        'player_err_counts': player_err_counts,
        **final_stats,
        'json_history': json_history,
    }


def parse_move_from_response(response: Any):
    if not isinstance(response, str):
        return response
    if '```python' in response:
        response = response.split('```python')[1].split('```')[0]
    response = response.strip()
    while response.startswith('`'):
        response = response[1:].strip()
    while response.endswith('`'):
        response = response[:-1].strip()
    if '{' in response and '}' in response:
        response = response[response.index('{'):response.index('}') + 1]
    try:
        return json.loads(response)['action']
    except Exception:
        return response

def _to_jsonable(x: Any) -> Any:
    if isinstance(x, np.generic):  # NumPy scalars (np.int64, np.float32, np.bool_, etc.)
        return x.item()
    if isinstance(x, np.ndarray):  # NumPy arrays
        return x.tolist()
    if isinstance(x, dict):  # Mappings
        return {str(k): _to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):  # Sequences
        return [_to_jsonable(i) for i in x]
    if isinstance(x, set):  # Common non-JSON container
        return [_to_jsonable(i) for i in x]
    return x  # Already JSON-serializable primitives (or json can handle it)

def kwargs_to_str(kwargs: Any) -> str:
    try:
        return json.dumps(_to_jsonable(kwargs), ensure_ascii=False)
    except TypeError as e:
        raise ValueError(f"Cannot convert {type(kwargs).__name__} to string; error: {e}") from e


class LLM_Policy:
    def __init__(self, model: OpenRouterModel, game: Game, config: dict[str, Any], history_len: int, show_legal_moves: bool = False, debug: bool = False, request_timeout: Optional[float] = None):
        self.model = model
        self.game = game
        self.config = config
        self.api_attempts: list[dict] = []  # each element is raw OpenRouter API response
        self.history: list[list[dict]] = []
        self.history_len = history_len
        self.show_legal_moves = show_legal_moves
        self.debug = debug
        self.request_timeout = request_timeout
        self.max_retry_count = 3
        if hasattr(self.game, 'live_play_is_legal'):
            logger.info(f"Game {self.game.__class__.__name__} has function to check legality of moves")
        else:
            assert self.max_retry_count <= 0, "Max retry count must be 0 if game does not have function to check legality of moves"

        self.prompt = []
        self.prompt.append({"role": "system", "content": "You are a helpful assistant."})
        self.prompt.append({"role": "user", "content": self.game.get_prompt(config=self.config, live_play=True), "cache_control": {"type": "ephemeral"}})  # type: ignore
    
    def attempt_get_total_cost(self):
        try:
            return sum(a['raw']['usage']['cost'] for a in self.api_attempts if isinstance(a['raw'], dict) and 'usage' in a['raw'])
        except Exception:
            return None
    
    def DEBUG_AND_EXIT_SCRIPT(self):
        print('DEBUG MODE\n\nmessage:')
        msgs = self.prompt + [msg for h in self.history for msg in h]
        for msg in msgs:
            print(f'{msg["role"]}: {msg["content"]}')
        sys.exit(0)

    def get_messages(self):
        # last n elements in history, +1 for the current input
        n = self.history_len+1
        last_n_moves = self.history[-n:]
        results = []
        for move in last_n_moves:
            for msg in move:
                results.append(msg)
        return self.prompt + results
    
    def _call_once(self, kwargs_str):
        # time.sleep(random.uniform(0.5, 1.5))
        response = send_chat(self.model, self.get_messages(), timeout=self.request_timeout, attempt_log=self.api_attempts)
        if response is None:
            raise ValueError(f"No response from {self.model.save_name} for board: {kwargs_str}")
        self.history[-1].append({"role": "assistant", "content": response.content})
        assistant_reply = parse_move_from_response(response.content)
        _assistant_reply_one_line = str(assistant_reply).replace('\n', '\\n')
        logger.info(f'GAME STEP: {self.model.save_name} chooses {_assistant_reply_one_line} for board: {kwargs_str}')
        if hasattr(self.game, 'live_play_is_legal'):
            try:
                is_legal = self.game.live_play_is_legal(assistant_reply) # type: ignore
            except Exception:
                logger.warning(f"Legality check raised for agent response: '{_assistant_reply_one_line}'\n{traceback.format_exc()}")
                is_legal = False
            if not is_legal:
                logger.warning(f"Illegal move for agent response: '{_assistant_reply_one_line}'")
                return assistant_reply, False
        return assistant_reply, True

    def __call__(self, **kwargs):
        kwargs_str = f'Current state: {kwargs_to_str(kwargs)}'
        if self.show_legal_moves:
            kwargs_str += f"\nLegal moves: {self.game.live_play_legal_moves()}"
        self.history.append([{"role": "user", "content": kwargs_str}])
        if self.debug:
            self.DEBUG_AND_EXIT_SCRIPT()
        illegal_count = 0
        for _ in range(self.max_retry_count):  # if illegal tell the LLM and retry, if error, simply retry
            try:
                assistant_reply, is_legal = self._call_once(kwargs_str)
            except Exception as e:
                logger.error(f"Error in LLM_Policy.__call__: {e}")
                continue
            if is_legal:
                return assistant_reply
            illegal_count += 1
            self.history[-1].append({"role": "user", "content": f"Illegal move: {assistant_reply}. Please try again."})
        if illegal_count == self.max_retry_count:
            raise IllegalMoveForfeit(f"Max retry count {self.max_retry_count} reached, all illegal moves, last: {assistant_reply}")
        raise RuntimeError(f"Max retry count {self.max_retry_count} reached ({illegal_count} illegal moves, rest were failed API calls)")


def save_results(results, model_save_name, game_world, opponent_name, results_dir_name: str = LIVE_RESULTS_DIR):
    d = get_root_path() / results_dir_name / model_save_name / game_world
    d.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
    with open(d / f'{now},{opponent_name}.json', 'x', encoding='utf-8') as f:
        json.dump({'now': now, **results}, f, indent=2)


def is_number(s):
    try:
        x = float(s)
        return not math.isnan(x)
    except (TypeError, ValueError):
        return False

def resolve_model(model_name: str) -> OpenRouterModel:
    models = get_openrouter_models([model_name])
    assert len(models) == 1, f"Model {model_name} is not an openrouter model"
    return models[0]


def llm_player_name(model: OpenRouterModel) -> str:
    return 'LLM_' + model.save_name


def get_bots(game_str: str, world: str, elo_csv_fn: str):
    """The world's loadable bots (utils.get_bot_paths_from_world) with their rating from the csv."""
    elo_csv_path = get_root_path() / elo_csv_fn
    bot_elo_df = pd.read_csv(elo_csv_path, index_col=0)
    assert (game_str, world) in _GAME_WORLD_TO_NAME, f"Game {game_str} world {world} not found in _GAME_WORLD_TO_NAME"
    col_name = _GAME_WORLD_TO_NAME[(game_str, world)]
    assert col_name in bot_elo_df.columns, f"Column {col_name} not found in {bot_elo_df.columns} for csv in {elo_csv_fn}"
    mtime = datetime.fromtimestamp(elo_csv_path.stat().st_mtime, tz=timezone.utc)
    bots: list[dict] = []
    for bot_name, path in get_bot_paths_from_world(game_str, world).items():
        info_path = path / '0.info.json'
        if not info_path.exists():
            continue
        info = json.loads(info_path.read_text())
        # assert that bot created BEFORE csv
        t = datetime.fromisoformat(info['now']).replace(tzinfo=timezone.utc)
        assert t < mtime, f"Bot {bot_name} created after csv {elo_csv_path.as_posix()} was created"
        elo = bot_elo_df.at[bot_name, col_name] if bot_name in bot_elo_df.index else None
        bots.append({'name': bot_name, 'info': info, 'elo': elo})
    return bots

def sorted_by_elo(bots: list[dict]):
    return sorted(bots, key=lambda b: float(b['elo']) if is_number(b['elo']) else -float('inf'), reverse=True)

def play_live_game(model_name: str, game_str: str, world: str, bot_name: str, llm_color: str, history_len: int = 10, show_legal_moves: bool = False,
                   debug: bool = False, request_timeout: Optional[float] = None, extra_info: Optional[dict] = None) -> dict:
    """Play and save one game of model_name vs bot_name. llm_color 'A'|'B'
    Finished games and forfeits go to LIVE_RESULTS_DIR; any other failed game to LIVE_UNSAVED_DIR."""
    assert llm_color in ('A', 'B'), f"llm_color must be 'A' or 'B', got {llm_color}"
    model = resolve_model(model_name)
    bot_player = get_policy_fn_with_memory(bot_name, get_examples_dir(game_str) / world / bot_name)  # same loader as the tourney
    config = get_config_file(game_str, world)
    game_inst = get_game(game_name=game_str)(config)
    llm_policy = LLM_Policy(model, game_inst, config, history_len, show_legal_moves, debug, request_timeout)
    llm_player = (llm_player_name(model), llm_policy)
    players = [llm_player, bot_player] if llm_color == 'A' else [bot_player, llm_player]
    results = play_game_live(game_inst, players)
    results_dir_name = LIVE_RESULTS_DIR
    if not results['done'] and not results.get('forfeit'):
        logger.warning(f"Saving {game_str} {world} model {model_name} vs bot {bot_name} (LLM color {llm_color}) to {LIVE_UNSAVED_DIR} because it failed without a forfeit")
        results_dir_name = LIVE_UNSAVED_DIR
    save_results({
        **{f'name{i}': p[0] for i, p in enumerate(players)},
        **results,
        'live_play': {
            'total_cost': llm_policy.attempt_get_total_cost(),
            'show_legal_moves': show_legal_moves,
            'bot_name': bot_name,
            'llm_color': llm_color,
            'game_str': game_str,
            'world': world,
            'history_len': history_len,
            'llm_model_name': model_name,
            'openrouter_id': model.openrouter_id,
            'model_parameters': model.parameters,
            'request_timeout': request_timeout,
            **(extra_info or {}),
            'api_attempts': llm_policy.api_attempts,
            'messages': llm_policy.prompt + llm_policy.history,
        },
    }, model.save_name, f'{game_str}_{world}', bot_name.replace('/', '_'), results_dir_name)
    return results


def main_llm_vs_bot(game_str: str, world: str, model_name: str, vs_model_parent_name: str, elo_csv_fn: str, num_games: int = 1, skip_n_bots: int = 0, history_len: int = 10, show_legal_moves: bool = False, debug: bool = False, request_timeout: Optional[float] = None):
    model = resolve_model(model_name)
    live_counts = get_live_play_counts(f'{game_str}_{world}')

    bots = get_bots(game_str, world, elo_csv_fn)
    model_names = set(b['name'].split('/')[0] for b in bots)
    model_bots = {name: [b for b in bots if b['name'].startswith(name + '/')] for name in model_names}
    to_vs = []
    if vs_model_parent_name == '':  # only keep the 1 top model
        to_vs = [sorted_by_elo(bots)[0]]
    elif vs_model_parent_name == 'ALL' or ',' in vs_model_parent_name:
        if vs_model_parent_name == 'ALL':
            vs_model_name_list = model_names
        else:
            vs_model_name_list = vs_model_parent_name.split(',')
        for name in vs_model_name_list:
            best_bot = sorted_by_elo(model_bots[name])[0]
            if is_number(best_bot['elo']) and float(best_bot['elo']) > 0:
                to_vs.append(best_bot)
            else:
                logger.warning(f"Skipping {name} for game {game_str}/{world} because its best bot has elo {best_bot['elo']}")
    else:  # specific model
        assert vs_model_parent_name in model_names, f"Model {vs_model_parent_name} not found in {model_names}"
        best_bot = sorted_by_elo(model_bots[vs_model_parent_name])[0]
        assert is_number(best_bot['elo']) and float(best_bot['elo']) > 0, f"Best bot {best_bot['name']} has non-positive elo {best_bot['elo']}"
        to_vs = [best_bot]
    to_vs = sorted_by_elo(to_vs)
    if skip_n_bots >= len(to_vs):
        logger.warning(f"Skipping all bots because skip_n_bots {skip_n_bots} >= len(to_vs) {len(to_vs)}")
        return
    to_vs = to_vs[skip_n_bots:]

    for bot_idx, bot in enumerate(to_vs):
        for i in range(2*num_games):
            color = 'A' if i % 2 == 0 else 'B'
            current_game_count = i // 2
            if current_game_count < live_counts[llm_player_name(model)][bot['name']][color]:
                logger.warning(f"Skipping game {i} of {2*num_games} for {game_str} {world} model {model_name} vs bot {bot['name']} (bot#{bot_idx}/{len(to_vs)}) [ELO: {bot['elo']}]")
                continue
            logger.info(f"MAIN_LLM_VS_BOT: Playing game {i} of {2*num_games} for {game_str} {world} model {model_name} vs bot {bot['name']} (bot#{bot_idx}/{len(to_vs)}) [ELO: {bot['elo']}]")
            play_live_game(model_name, game_str, world, bot['name'], color, history_len, show_legal_moves, debug, request_timeout,
                           extra_info={'i': i, 'elo_csv_fn': elo_csv_fn})


def main_llm_vs_bot_multi_games(game_worlds: list[tuple[str, str]], model_name: str, vs_model_parent_name: str, elo_csv_fn: str, num_games: int = 1, skip_n_bots: int = 0, history_len: int = 10, show_legal_moves: bool = False, debug: bool = False, request_timeout: Optional[float] = None):
    for game_str, world in game_worlds:
        main_llm_vs_bot(game_str, world, model_name, vs_model_parent_name, elo_csv_fn, num_games, skip_n_bots, history_len, show_legal_moves, debug, request_timeout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--game_worlds", type=str, required=True)
    parser.add_argument('--model', type=str, required=True)
    parser.add_argument('--vs_model_parent', type=str, default='')
    parser.add_argument('--num_games', type=int, default=1)
    parser.add_argument('--skip_n_bots', type=int, default=0)
    parser.add_argument('--elo_csv_fn', type=str, default='src/frontend/arena_fe/public/elos_all_bots.csv')
    parser.add_argument('--history_len', type=int, default=10, help='number of previous turns sent to the LLM; -1 sends the full game history')
    parser.add_argument('--show_legal_moves', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--request_timeout', type=float, default=None, help='seconds before an API request is abandoned (counts as a failed attempt)')
    args = parser.parse_args()
    game_worlds = args.game_worlds.split(',')
    game_worlds = [(s.split('/')[0], s.split('/')[1]) for s in game_worlds]
    main_llm_vs_bot_multi_games(
        game_worlds=game_worlds,
        model_name=args.model,
        vs_model_parent_name=args.vs_model_parent,
        elo_csv_fn=args.elo_csv_fn,
        num_games=args.num_games,
        skip_n_bots=args.skip_n_bots,
        history_len=args.history_len,
        show_legal_moves=args.show_legal_moves,
        debug=args.debug,
        request_timeout=args.request_timeout,
    )
