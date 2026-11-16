import json
import random
import time
import traceback
from typing import Any

import numpy as np

from game_arena import utils
import inspect


def _move_to_str(move):
    move = _to_native(move)
    if hasattr(move, "get_unparsed_str"):
        try:
            return move.get_unparsed_str()
        except Exception:
            pass
    return str(move)


def _to_native(value):
    """NumPy scalars (np.int64, np.str_, ...) become their Python equivalents, also inside tuples/lists."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return tuple(_to_native(v) for v in value)
    if isinstance(value, list):
        return [_to_native(v) for v in value]
    return value


def _action_for_engine(action, legal_moves, legal_move_strings):
    """The form of a policy's answer that game.get_move accepts.

    Engines whose moves have a string form (get_unparsed_str) parse that string; engines with tuple /
    int moves want their own object back when the policy answered with its string form.
    """
    action = _to_native(action)
    if hasattr(action, "get_unparsed_str"):
        try:
            return action.get_unparsed_str()
        except Exception:
            return action
    if isinstance(action, str) and action in legal_move_strings:
        candidate = legal_moves[legal_move_strings.index(action)]
        if not isinstance(candidate, str) and not hasattr(candidate, "get_unparsed_str"):
            return candidate
    return action


def _move_to_json(move):
    """A replayable, JSON-friendly form of a move, matching what the history exporter stores
    (tuples become lists so replay_moves can hand them back to the engine unchanged)."""
    move = _to_native(move)
    if hasattr(move, "get_unparsed_str"):
        try:
            return move.get_unparsed_str()
        except Exception:
            pass
    if isinstance(move, (tuple, list)):
        return [_move_to_json(m) for m in move]
    if isinstance(move, (str, int, float, bool)) or move is None:
        return move
    return str(move)


_POLICIES = {}
_RAW_POLICIES = {}  # unwrapped policy functions, re-wrapped per match so `memory` starts empty
_PENDING_HUMAN_ACTION = None
_USER_POLICY_NAME = "user"
_BUILTIN_POLICIES = {"human", "random", "first", "last"}


def _ensure_selected_policies(game_name, world_name, selected_bot_ids):
    key = (game_name, world_name)
    policies = _POLICIES.get(key)
    if policies is None:
        policies = {}
        _POLICIES[key] = policies
    for bot_id in selected_bot_ids:
        if not bot_id or bot_id in _BUILTIN_POLICIES:
            continue
        if bot_id in policies:
            continue
        if bot_id == _USER_POLICY_NAME:
            return "Your automaton has not been compiled yet"
        path = f"/home/src/game_arena/{game_name}/examples/{world_name}/{bot_id}/2.python_code.py"
        try:
            with open(path, "r") as f:
                code = f.read()
        except Exception as e:
            return f"Failed to read bot code for {bot_id}: {e}"
        policy_fn, msg = utils.get_policy_fn(code, path, f"{game_name}/{world_name}/{bot_id}")
        if policy_fn is None:
            return msg or f"Failed to compile bot code for {bot_id}"
        _RAW_POLICIES.setdefault(key, {})[bot_id] = policy_fn
        policies[bot_id] = utils.wrap_policy_fn_with_memory(policy_fn)
    return None


def _choose_action(game_name, world_name, policy_name, observation, legal_moves):
    if not legal_moves:
        return None
    if policy_name == "human":
        return None
    if policy_name == "first":
        return _move_to_str(legal_moves[0])
    if policy_name == "last":
        return _move_to_str(legal_moves[-1])
    if policy_name == "random":
        return _move_to_str(random.choice(legal_moves))
    policy = _POLICIES[(game_name, world_name)].get(policy_name)
    if policy is None:
        return _move_to_str(random.choice(legal_moves))
    kwargs = dict(observation)
    try:
        if "_debug_legal_moves" in inspect.signature(policy).parameters:
            kwargs["_debug_legal_moves"] = legal_moves
    except Exception:
        pass
    result = policy(**kwargs)  # type: ignore
    return result


def _safe_final_stats(game):
    try:
        return game.get_final_stats()
    except Exception as e:
        return {"error": str(e)}


def _winner_for_illegal(player):
    try:
        player_id = int(player)
    except Exception:
        return None
    if player_id in (0, 1):
        return 1 - player_id
    return None


_GAME = None
_TURN = 0
# set by resolve_hung_automaton: the next automaton move is a random legal move instead of a policy call
_FORCE_RANDOM_MOVE = False
WORLD_NAME = ""


def init_match():
    global _GAME, _TURN, _PENDING_HUMAN_ACTION
    logs = []
    error = _ensure_selected_policies(GAME_NAME, WORLD_NAME, [BOT_A, BOT_B])
    if error:
        logs.append(error)
        return {"error": error, "logs": logs, "done": True}
    try:
        game_cls = utils.get_game(GAME_NAME)
        if hasattr(game_cls, "LIVE_SEAT_SWAPPER"):  # e.g. chess: automaton A plays white NOT black
            game_cls = game_cls.LIVE_SEAT_SWAPPER
        _GAME = game_cls(GAME_CONFIG)
    except Exception as e:
        tb = traceback.format_exc()
        logs.append("init_error_traceback:")
        logs.extend(tb.splitlines())
        return {"error": "Failed to initialize game: " + str(e) + "\\n" + tb, "logs": logs, "done": True}
    _TURN = 0
    _PENDING_HUMAN_ACTION = None
    logs.append(f"game={GAME_NAME} world=browser config={GAME_CONFIG}")
    return {"logs": logs, "done": False, "state_player": {
        "state": _GAME.get_fixed_observation(),  # type: ignore
        "player": _GAME.current_player(),
    }}


def policy_error(logs, policy_name, player):
    final_stats = _safe_final_stats(_GAME)
    winner = _winner_for_illegal(player)
    if winner is not None:
        if isinstance(final_stats, dict):
            final_stats: dict[str, Any] = dict(final_stats)
        else:
            final_stats = {}
        final_stats["winner"] = winner
        logs.append(f"illegal_move_winner={winner}")
    logs.append("final_stats=" + str(final_stats))
    return {
        "done": True,
        "final": final_stats,
        "illegal": True,
        "illegal_bot": policy_name,
        "illegal_action": None,
    }
    
def move_error(logs, e, policy_name, action, player):
    logs.append("Move error: " + str(e))
    logs.append(f"Illegal move by {policy_name}.")
    illegal_action = _move_to_str(action)
    logs.append(f"illegal_action={illegal_action}")
    final_stats = _safe_final_stats(_GAME)
    winner = _winner_for_illegal(player)
    if winner is not None:
        if isinstance(final_stats, dict):
            final_stats: dict[str, Any] = dict(final_stats)
        else:
            final_stats = {}
        final_stats["winner"] = winner
        logs.append(f"illegal_move_winner={winner}")
    logs.append("final_stats=" + str(final_stats))
    return {
        "done": True,
        "final": final_stats,
        "illegal": True,
        "illegal_bot": policy_name,
        "illegal_action": illegal_action,
    }

def _forgive_automaton_faults():
    """Human vs automaton: an automaton fault is replaced by a random legal move instead of ending the game."""
    return (BOT_A == "human") != (BOT_B == "human")


def step_match():
    global _GAME, _TURN
    global _PENDING_HUMAN_ACTION
    logs = []
    return_kwargs = {
        "logs": logs,
        "state_player": None
    }
    if _GAME is None:
        return {"error": "No game initialized", "done": True, **return_kwargs}
    if (GAME_NAME, WORLD_NAME) not in _POLICIES:
        return {"error": "no policies found for game/world", "done": True, **return_kwargs}
    if _GAME.is_done():
        final_stats = _safe_final_stats(_GAME)
        logs.append("final_stats=" + str(final_stats))
        return {"done": True, "final": final_stats, **return_kwargs}
    if hasattr(_GAME, "get_fixed_observation"):
        observation = _GAME.get_fixed_observation()  # type: ignore
        bot_observation = _GAME.get_observation()
    else:
        observation = _GAME.get_observation()
        bot_observation = observation
    player = _GAME.current_player()
    return_kwargs["state_player"] = {
        "state": observation,
        "player": player,
    }
    legal_moves = _GAME.get_legal_moves()
    legal_move_strings = [_move_to_str(move) for move in legal_moves]
    sample = ", ".join(legal_move_strings[:8])
    logs.append(
        f"turn={_TURN} player={player} legal_moves={len(legal_moves)} sample=[{sample}]"
    )
    if observation is not None and "board" in observation:
        logs.append("board=" + str(observation["board"]))
    else:
        logs.append("observation=" + str(observation))
    try:
        logs.append("state_pre_move=\n" + str(_GAME._state))  # type: ignore
    except Exception as e:
        logs.append("Exception: error getting state before move: " + str(e))
    policy_name = BOT_A if player == 0 else BOT_B
    action = None
    fault = None
    if policy_name == "human":
        if _PENDING_HUMAN_ACTION is None:
            return {
                "done": False,
                "awaiting_input": True,
                "legal_moves": legal_move_strings,
                **return_kwargs,
            }
        pending_human_action = _PENDING_HUMAN_ACTION
        _PENDING_HUMAN_ACTION = None
        force_apply = False
        if isinstance(pending_human_action, dict):
            action = pending_human_action.get("action")
            force_apply = bool(pending_human_action.get("force_apply", False))
        else:
            action = pending_human_action
        action_str = str(action)
        if force_apply:
            logs.append(f"Force-applying human move: {action_str}")
        if not force_apply and action_str not in legal_move_strings:
            logs.append(f"Invalid human move: {action_str}")
            return {
                "done": False,
                "awaiting_input": True,
                "legal_moves": legal_move_strings,
                "invalid_move": action_str,
                **return_kwargs,
            }
    elif _FORCE_RANDOM_MOVE:
        fault = "hung"
    else:
        try:
            action = _choose_action(game_name=GAME_NAME, world_name=WORLD_NAME, policy_name=policy_name, observation=bot_observation, legal_moves=legal_moves)
        except KeyboardInterrupt:
            # the host stopped a hung policy; nothing was played, the host decides what happens next
            logs.append(f"{policy_name} was interrupted while choosing a move")
            return {"done": False, "interrupted": True, **return_kwargs}
        except Exception as e:
            logs.append(f"Exception: error executing policy for {policy_name}: " + str(e) + "\n" + traceback.format_exc())
            if not _forgive_automaton_faults():
                return {**policy_error(logs, policy_name, player), **return_kwargs}
            fault = "crashed"
    if action is None and fault is None:
        logs.append(f"Action was none by {policy_name}. Not allowed.")
        if not _forgive_automaton_faults():
            return {**policy_error(logs, policy_name, player), **return_kwargs}
        fault = "returned no move"
    if fault is not None:
        action = random.choice(legal_move_strings)
    action_for_move = _action_for_engine(action, legal_moves, legal_move_strings)
    logs.append(f"{policy_name} chooses {_move_to_str(action)}")
    try:
        action_obj = _GAME.get_move(action_for_move)  # type: ignore
        _GAME.game_step(action_obj)  # type: ignore
    except Exception as e:
        logs.append("Exception: error getting move: " + str(e) + "\n" + traceback.format_exc())
        if policy_name == "human" or fault is not None or not _forgive_automaton_faults():
            return {**move_error(logs, e, policy_name, action, player), **return_kwargs}
        fault = f"played illegal move {_move_to_str(action)}"
        idx = random.randrange(len(legal_moves))
        action = legal_move_strings[idx]
        action_for_move = _action_for_engine(action, legal_moves, legal_move_strings)
        try:
            _GAME.game_step(_GAME.get_move(action_for_move))  # type: ignore
        except Exception as e2:
            logs.append("Exception: error applying random fallback move: " + str(e2) + "\n" + traceback.format_exc())
            return {**move_error(logs, e2, policy_name, action, player), **return_kwargs}
    if fault is not None:
        return_kwargs["warning"] = f"{policy_name} {fault}. A random legal move ({_move_to_str(action)}) was played instead."
        logs.append("warning=" + return_kwargs["warning"])
    try:
        if hasattr(_GAME, "get_fixed_observation"):
            new_observation = _GAME.get_fixed_observation()  # type: ignore
        else:
            new_observation = _GAME.get_observation()
        logs.append('new_observation=' + str(new_observation))
        return_kwargs["state_player"] = {
            "state": new_observation,
            "player": _GAME.current_player(),
            "old_state": return_kwargs["state_player"]["state"],
            "old_player": return_kwargs["state_player"]["player"],
            "action": action_for_move,
        }
    except Exception as e:
        logs.append("Exception: error getting new observation: " + str(e))
    try:
        logs.append("state_post_move=\n" + str(_GAME._state))  # type: ignore
    except Exception:
        logs.append("Exception: error getting state after move")
    _TURN += 1
    if _GAME.is_done():
        final_stats = _safe_final_stats(_GAME)
        logs.append("final_stats=" + str(final_stats))
        return {"done": True, "final": final_stats, **return_kwargs}
    return {"done": False, **return_kwargs}


def resolve_hung_automaton(choice):
    """Human vs automaton, after the host interrupted a hung policy.

    "random" plays a random legal move for the automaton and continues; "forfeit" ends the game
    with the automaton losing. If the automaton's move went through after all, "random" just
    returns the human's turn.
    """
    global _FORCE_RANDOM_MOVE
    if _GAME is None:
        return {"error": "No game initialized", "done": True, "logs": [], "state_player": None}
    player = _GAME.current_player()
    policy_name = BOT_A if player == 0 else BOT_B
    if choice == "random" or _GAME.is_done() or policy_name == "human":
        _FORCE_RANDOM_MOVE = True
        try:
            return step_match()
        finally:
            _FORCE_RANDOM_MOVE = False
    logs = [f"{policy_name} hung and forfeits the game"]
    final_stats = _safe_final_stats(_GAME)
    final_stats = dict(final_stats) if isinstance(final_stats, dict) else {}
    final_stats["winner"] = 1 - int(player)
    logs.append("final_stats=" + str(final_stats))
    return {"done": True, "final": final_stats, "forfeit_bot": policy_name, "logs": logs}


def submit_human_move(action, force_apply=False):
    global _PENDING_HUMAN_ACTION
    _PENDING_HUMAN_ACTION = {"action": action, "force_apply": bool(force_apply)}
    return step_match()


def _tuplify(value):
    if isinstance(value, list):
        return tuple(_tuplify(v) for v in value)
    return value


def replay_moves(game_name, world_name, config, seed, moves):
    """Replay a recorded move list (Match Viewer) and return one observation per turn.

    Independent from the live match globals (_GAME etc.), so it can run while a match is open.
    """
    try:
        moves = list(moves or [])
        if hasattr(config, "to_py"):
            config = config.to_py()
        game_cls = utils.get_game(game_name)
        if seed is not None and int(seed) >= 0:
            utils.set_seed(int(seed))
        game = game_cls(dict(config or {}))
    except Exception as e:
        return {"ok": False, "why": "init failed: " + str(e), "frames": [], "applied": 0, "total": len(moves or [])}

    frames = []

    def push():
        try:
            if hasattr(game, "get_fixed_observation"):
                obs = game.get_fixed_observation()
            else:
                obs = game.get_observation()
        except Exception as e:
            obs = {"error": str(e)}
        try:
            player = game.current_player()
        except Exception:
            player = None
        frames.append({"state": obs, "player": player})

    push()
    applied = 0
    failed = None
    for item in moves:
        if game.is_done():
            break
        try:
            player = item[0]
            action = item[1]
        except Exception:
            failed = {"index": applied, "player": None, "action": str(item), "why": "malformed move"}
            break
        if action is None:
            failed = {"index": applied, "player": player, "action": None,
                      "why": "no move was produced (the player timed out or crashed before answering)"}
            break
        try:
            try:
                game.get_observation()  # some engines (Backgammon) parse moves against the current observation
            except Exception:
                pass
            if isinstance(action, list):
                try:
                    move_obj = game.get_move(_tuplify(action))
                except Exception:
                    move_obj = game.get_move(action)
            else:
                move_obj = game.get_move(action)
            game.game_step(move_obj)
        except Exception as e:
            failed = {"index": applied, "player": player, "action": action, "why": str(e)[:300]}
            break
        applied += 1
        push()
    final = _safe_final_stats(game)
    try:
        done = bool(game.is_done())
    except Exception:
        done = False
    return {
        "ok": True,
        "frames": frames,
        "applied": applied,
        "total": len(moves),
        "failed_move": failed,
        "final": final,
        "done": done,
    }

if __name__ == "__main__":
    GAME_NAME: Any
    GAME_CONFIG: Any
    BOT_A: Any
    BOT_B: Any


# ---------------------------------------------------------------------------------------
# "Create your own Automata": compile user code, fetch the game prompt, play whole matches
# ---------------------------------------------------------------------------------------
def get_game_prompt(game_name, config):
    if hasattr(config, "to_py"):
        config = config.to_py()
    try:
        game_cls = utils.get_game(game_name)
        return {"prompt": game_cls.get_prompt(dict(config or {}))}
    except Exception as e:
        return {"error": str(e)}


def _user_error_line(exc, path):
    """Line number inside the user's file where an exception originated (innermost user frame)."""
    if isinstance(exc, SyntaxError) and exc.filename == path and exc.lineno:
        return int(exc.lineno)
    line = None
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == path:
            line = tb.tb_lineno
        tb = tb.tb_next
    return line


def set_user_policy(game_name, world_name, code, config=None, smoke=False):
    """Compile the user's code (it must define a callable `policy`); optionally run the smoke test too."""
    key = (game_name, world_name)
    path = "/home/user_automaton.py"
    ns = {"np": np, "random": random, "__file__": path}
    try:
        exec(compile(code, path, "exec"), ns)
    except Exception as e:
        return {"ok": False, "stage": "compile", "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc(), "line": _user_error_line(e, path)}
    policy_fn = ns.get("policy")
    if policy_fn is None or not callable(policy_fn):
        return {"ok": False, "stage": "compile", "error": "The code must define a function called `policy`."}
    _RAW_POLICIES.setdefault(key, {})[_USER_POLICY_NAME] = policy_fn
    _POLICIES.setdefault(key, {})[_USER_POLICY_NAME] = utils.wrap_policy_fn_with_memory(policy_fn)
    try:
        utils.get_game(game_name)  # import the engine now so a broken runtime fails here, not mid-match
    except Exception as e:
        return {"ok": False, "stage": "runtime", "error": f"The game engine could not be loaded in this runtime: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}
    if smoke:
        return smoke_test_user_policy(game_name, world_name, config, None)
    return {"ok": True}


def smoke_test_user_policy(game_name, world_name, config=None, move_timeout=None):
    """Call the compiled user policy once on the initial board; the policy's own memory is reset afterwards."""
    if hasattr(config, "to_py"):
        config = config.to_py()
    key = (game_name, world_name)
    path = "/home/user_automaton.py"
    policy_fn = _RAW_POLICIES.get(key, {}).get(_USER_POLICY_NAME)
    if policy_fn is None:
        return {"ok": False, "stage": "smoke", "error": "Your automaton has not been compiled yet"}
    utils.set_seed(0)
    random.seed(0)
    try:
        game = utils.get_game(game_name)(dict(config or {}))
    except Exception as e:
        return {"ok": False, "stage": "smoke", "error": "Failed to initialize game: " + str(e), "traceback": traceback.format_exc()}
    legal_moves = game.get_legal_moves()
    legal_strs = [_move_to_str(m) for m in legal_moves]
    _POLICIES[key][_USER_POLICY_NAME] = utils.wrap_policy_fn_with_memory(policy_fn)
    ts = time.time()
    try:
        action = _choose_action(game_name=game_name, world_name=world_name, policy_name=_USER_POLICY_NAME, observation=game.get_observation(), legal_moves=legal_moves)
    except Exception as e:
        return {"ok": False, "stage": "smoke", "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc(), "line": _user_error_line(e, path)}
    finally:
        _POLICIES[key][_USER_POLICY_NAME] = utils.wrap_policy_fn_with_memory(policy_fn)
    dt = time.time() - ts
    if move_timeout and dt > float(move_timeout):
        return {"ok": False, "stage": "smoke", "error": f"move took {dt:.2f}s on the initial board (limit {move_timeout}s)", "secs": round(dt, 3)}
    if action is None:
        return {"ok": False, "stage": "smoke", "error": "policy returned None on the initial board"}
    try:
        _apply_action(game, action, legal_moves, legal_strs)
    except Exception as e:
        return {"ok": False, "stage": "smoke", "error": f"illegal move {_move_to_str(action)!r} on the initial board: {e}", "traceback": traceback.format_exc()}
    return {"ok": True, "move": _move_to_str(action), "secs": round(dt, 3)}


def _apply_action(game, action, legal_moves, legal_move_strings):
    """Apply a policy's answer to the engine and return the form that was actually applied
    (string, tuple or engine action id), which is what a replay must feed back in."""
    action_for_move = _action_for_engine(action, legal_moves, legal_move_strings)
    game.game_step(game.get_move(action_for_move))
    return action_for_move


def _match_fault(history, t0, player, names, reason, error, tb):
    if names[player] in _BUILTIN_POLICIES:
        # a built-in baseline cannot fault on its own: this is a runtime/engine problem, not a result
        return {
            "winner": None,
            "reason": "setup",
            "culprit": None,
            "error": f"The {names[player]} baseline could not play a legal move ({error}). This is an error in the runtime, not in your automaton.",
            "traceback": tb,
            "moves": len(history),
            "history": history,
            "secs": round(time.time() - t0, 2),
        }
    return {
        "winner": 1 - player,
        "reason": reason,
        "culprit": player,
        "culprit_name": names[player],
        "error": error,
        "traceback": tb,
        "moves": len(history),
        "history": history,
        "secs": round(time.time() - t0, 2),
    }


def play_full_match(game_name, world_name, config, bot_a, bot_b, seed, move_timeout, progress=None):
    """Play one whole match and return its outcome (winner/reason/culprit/error/history).

    `progress(moves_so_far, player_to_move, last_move_json)` is called right before every move so
    the host can detect a policy that never returns without waiting for the whole match, and keeps
    a copy of every move played so far even if this runtime has to be killed.
    """
    if hasattr(config, "to_py"):
        config = config.to_py()
    err = _ensure_selected_policies(game_name, world_name, [bot_a, bot_b])
    if err:
        return {"reason": "setup", "error": err}
    key = (game_name, world_name)
    raw = _RAW_POLICIES.get(key, {})
    for name in (bot_a, bot_b):
        if name in raw:  # fresh memory for every match, like the tournament runner
            _POLICIES[key][name] = utils.wrap_policy_fn_with_memory(raw[name])
    utils.set_seed(int(seed))
    random.seed(int(seed))
    try:
        game = utils.get_game(game_name)(dict(config or {}))
    except Exception as e:
        return {"reason": "setup", "error": "Failed to initialize game: " + str(e), "traceback": traceback.format_exc()}
    names = [bot_a, bot_b]
    history = []
    t0 = time.time()
    while not game.is_done():
        player = int(game.current_player())
        name = names[player]
        legal_moves = game.get_legal_moves()
        legal_strs = [_move_to_str(m) for m in legal_moves]
        observation = game.get_observation()
        if progress is not None:
            try:
                progress(len(history), player, json.dumps(history[-1]) if history else None)
            except Exception:
                pass
        ts = time.time()
        try:
            action = _choose_action(game_name=game_name, world_name=world_name, policy_name=name, observation=observation, legal_moves=legal_moves)
        except Exception as e:
            return _match_fault(history, t0, player, names, "error", f"{type(e).__name__}: {e}", traceback.format_exc())
        dt = time.time() - ts
        if action is None:
            return _match_fault(history, t0, player, names, "error", "policy returned None", None)
        if move_timeout and dt > float(move_timeout):
            return _match_fault(history, t0, player, names, "timeout", f"move took {dt:.2f}s (limit {move_timeout}s)", None)
        try:
            applied = _apply_action(game, action, legal_moves, legal_strs)
        except Exception as e:
            return _match_fault(history, t0, player, names, "illegal", f"illegal move {_move_to_str(action)!r}: {e}", traceback.format_exc())
        history.append([player, _move_to_json(applied), round(dt, 3)])
        if len(history) > 5000:
            break
    final = _safe_final_stats(game)
    winner = final.get("winner") if isinstance(final, dict) else None
    if winner not in (0, 1):
        winner = None
    return {
        "winner": winner,
        "reason": "win" if winner is not None else "draw",
        "culprit": None,
        "moves": len(history),
        "history": history,
        "secs": round(time.time() - t0, 2),
        "final": final,
    }
