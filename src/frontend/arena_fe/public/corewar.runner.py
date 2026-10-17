import random
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np


def _add_sys_path(path: Path) -> None:
    if path.exists():
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.append(path_str)


_PUBLIC_ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
_DRQ_ROOT = _PUBLIC_ROOT / "game_arena" / "clone_wars" / "drq"

_add_sys_path(_DRQ_ROOT / "src")
_add_sys_path(_DRQ_ROOT / "corewar")

try:
    from corewar_util import SimulationArgs
    from corewar_util import simargs_to_environment
    from corewar_util import MyMARS
    from corewar import Core, redcode
    from corewar.mars import (
        EVENT_EXECUTED,
        EVENT_I_WRITE,
        EVENT_A_WRITE,
        EVENT_B_WRITE,
        EVENT_A_DEC,
        EVENT_A_INC,
        EVENT_B_DEC,
        EVENT_B_INC,
        EVENT_A_ARITH,
        EVENT_B_ARITH,
    )
except Exception as e:  # pragma: no cover
    raise RuntimeError("Failed to import corewar modules: %s" % e)


_STATE = {
    "next_warrior_id": 7000,
    "next_match_id": 200,
    "matches": {},
}


class RunnerMARS(MyMARS):
    def __init__(self, *args, **kwargs):
        self.last_executed = 0
        self.dirty_addrs: set[int] = set()
        core = kwargs.get("core")
        warriors = kwargs.get("warriors")
        if core is None and len(args) > 0:
            core = args[0]
        if warriors is None and len(args) > 1:
            warriors = args[1]
        self.memory_owner: list[int] = [-1] * len(core) if core is not None else []
        self.warrior_index: dict[Any, int] = {warrior: idx for idx, warrior in enumerate(warriors or [])}
        super().__init__(*args, **kwargs)

    def core_event(self, warrior, address, event_type):
        super().core_event(warrior, address, event_type)
        if event_type in (
            EVENT_I_WRITE,
            EVENT_A_WRITE,
            EVENT_B_WRITE,
            EVENT_A_DEC,
            EVENT_A_INC,
            EVENT_B_DEC,
            EVENT_B_INC,
            EVENT_A_ARITH,
            EVENT_B_ARITH,
        ):
            addr = address % len(self.core)
            self.dirty_addrs.add(addr)
            if self.memory_owner is not None:
                idx = self.warrior_index.get(warrior)
                if idx is not None:
                    self.memory_owner[addr] = idx
        if event_type == EVENT_EXECUTED:
            executed = address % len(self.core)
            self.last_executed = executed
            warrior.last_executed = executed


@dataclass
class MatchState:
    simargs: SimulationArgs
    rounds: int
    seed_base: int
    randomize: bool
    warrior_ids: list[int]
    warriors: list[Any]
    config: dict
    round_idx: int = 0
    cycle: int = 0
    sim: Optional[RunnerMARS] = None
    score: Optional[np.ndarray] = None
    alive_score: Optional[np.ndarray] = None
    total_spawned: Optional[np.ndarray] = None
    prev_nprocs: Optional[np.ndarray] = None
    core_cache: Optional[list[str]] = None


def _init_round(match: MatchState, round_index: int) -> None:
    seed = match.seed_base + round_index
    random.seed(seed)

    core = Core(size=match.simargs.size)
    match.sim = RunnerMARS(
        core=core,
        warriors=match.warriors,
        minimum_separation=match.simargs.distance,
        max_processes=match.simargs.processes,
        randomize=match.randomize,
    )
    assert match.sim is not None
    if len(match.sim.memory_owner) != len(match.sim.core):
        match.sim.memory_owner = [-1] * len(match.sim.core)
    if not match.sim.warrior_index:
        match.sim.warrior_index = {warrior: idx for idx, warrior in enumerate(match.warriors)}

    for warrior in match.warriors:
        warrior.last_executed = None

    match.cycle = 0
    n = len(match.warriors)
    match.score = np.zeros(n, dtype=float)
    match.alive_score = np.zeros(n, dtype=float)
    match.total_spawned = np.zeros(n, dtype=int)
    match.prev_nprocs = np.array([len(w.task_queue) for w in match.warriors], dtype=int)
    match.core_cache = [str(match.sim.core[i]) for i in range(len(match.sim.core))]
    match.sim.dirty_addrs.clear()


def _get_match(match_id):
    return _STATE["matches"].get(match_id)


def init_match(config=None, warrior_specs=None):
    logs = []
    error_indices = []

    if config is None:
        config = {}
    if warrior_specs is None:
        warrior_specs = []

    try:
        simargs = SimulationArgs()
        for field in ("rounds", "size", "cycles", "processes", "length", "distance"):
            if field in config and config[field] is not None:
                setattr(simargs, field, int(config[field]))

        rounds = int(config.get("rounds", simargs.rounds))
        seed_base = int(config.get("seed", 0))
        randomize = bool(config.get("randomize", True))

        warriors = []
        warrior_ids = []
        error_message = None
        error_traceback = None
        for idx, spec in enumerate(warrior_specs):
            source = spec.get("source")
            code = spec.get("code", spec.get("value"))
            if source != "inline":
                raise ValueError("only inline warriors are supported")
            if not isinstance(code, str):
                raise ValueError("inline code must be a string")
            try:
                warrior = redcode.parse(code.split("\n"), simargs_to_environment(simargs))
            except Exception as exc:
                if error_message is None:
                    error_message = str(exc)
                    error_traceback = traceback.format_exc()
                error_indices.append(idx)
                continue
            warriors.append(warrior)
            warrior_ids.append(_STATE["next_warrior_id"])
            _STATE["next_warrior_id"] += 1

        if error_indices:
            logs.append("init_error_traceback:")
            if error_traceback:
                logs.extend(error_traceback.splitlines())
            return {
                "done": True,
                "error": error_message or "Invalid warrior code",
                "error_indices": error_indices,
                "logs": logs,
            }

        if not warriors:
            raise ValueError("no warriors provided")

        match = MatchState(
            simargs=simargs,
            rounds=rounds,
            seed_base=seed_base,
            randomize=randomize,
            warrior_ids=warrior_ids,
            warriors=warriors,
            config=dict(config),
        )
        match.round_idx = 0
        _init_round(match, match.round_idx)

        match_id = _STATE["next_match_id"]
        _STATE["next_match_id"] += 1
        _STATE["matches"][match_id] = match

        state = _build_state(match)
        frame = _build_frame(match, view="full")
        done = _round_done(match)
        logs.append("init_round=%d" % match.round_idx)
        result = {"done": done, "match_id": match_id, "logs": logs, "state": state}
        if frame is not None:
            result["frame"] = frame
        if done and match.round_idx + 1 >= match.rounds:
            result["final"] = state.get("metrics")
            result["match_done"] = True
        else:
            result["match_done"] = False
        return result
    except Exception as e:
        tb = traceback.format_exc()
        logs.append("init_error_traceback:")
        logs.extend(tb.splitlines())
        return {"done": True, "error": str(e), "error_indices": error_indices, "logs": logs}


def compile_warrior(code, config=None):
    logs = []
    if not isinstance(code, str):
        return {"ok": False, "error": "inline code must be a string", "logs": logs}
    try:
        simargs = SimulationArgs()
        if config is None:
            config = {}
        for field in ("rounds", "size", "cycles", "processes", "length", "distance"):
            if field in config and config[field] is not None:
                setattr(simargs, field, int(config[field]))
        redcode.parse(code.split("\n"), simargs_to_environment(simargs))
        return {"ok": True}
    except Exception as e:
        tb = traceback.format_exc()
        logs.append("compile_error_traceback:")
        logs.extend(tb.splitlines())
        return {"ok": False, "error": str(e), "logs": logs}


def _update_metrics(match: MatchState):
    nprocs = np.array([len(w.task_queue) for w in match.warriors], dtype=int)
    alive_flags = (nprocs > 0).astype(int)
    n_alive = int(alive_flags.sum())
    if n_alive == 0:
        return True

    match.score += (alive_flags * (1.0 / n_alive)) / match.simargs.cycles
    match.alive_score += alive_flags / match.simargs.cycles
    match.total_spawned += np.maximum(0, nprocs - match.prev_nprocs)
    match.prev_nprocs = nprocs
    active_warrior_to_stop = 1 if len(match.warriors) >= 2 else 0
    return n_alive <= active_warrior_to_stop


def _round_done(match: MatchState):
    if match.cycle >= match.simargs.cycles:
        return True
    if match.warriors:
        active_warrior_to_stop = 1 if len(match.warriors) >= 2 else 0
        alive = sum(1 for w in match.warriors if w.task_queue)
        if alive <= active_warrior_to_stop:
            return True
    return False


def step_match(match_id, steps=1, view="summary", center_addr=None, window=18):
    logs = []
    match = _get_match(match_id)
    if match is None:
        return {"done": True, "error": "match not found", "logs": logs}

    if steps is None:
        steps = 1
    try:
        steps = int(steps)
    except Exception:
        steps = 1

    for _ in range(max(0, steps)):
        if _round_done(match):
            break
        match.sim.step()
        match.cycle += 1
        ended = _update_metrics(match)
        if ended:
            break
    assert match.sim is not None
    for addr in match.sim.dirty_addrs:
        match.core_cache[addr] = str(match.sim.core[addr])
    match.sim.dirty_addrs.clear()

    done = _round_done(match)
    state = _build_state(match)
    frame = _build_frame(match, view=view, center_addr=center_addr, window=window)
    result = {"done": done, "logs": logs, "state": state}
    if frame is not None:
        result["frame"] = frame
    if done and match.round_idx + 1 >= match.rounds:
        result["final"] = state.get("metrics")
        result["match_done"] = True
    else:
        result["match_done"] = False
    return result


def next_round(match_id):
    logs = []
    match = _get_match(match_id)
    if match is None:
        return {"done": True, "error": "match not found", "logs": logs}
    if match.round_idx + 1 >= match.rounds:
        return {"done": True, "error": "no more rounds", "logs": logs, "state": _build_state(match)}
    match.round_idx += 1
    _init_round(match, match.round_idx)
    logs.append("init_round=%d" % match.round_idx)
    state = _build_state(match)
    frame = _build_frame(match, view="full")
    done = _round_done(match)
    result = {"done": done, "logs": logs, "state": state}
    if frame is not None:
        result["frame"] = frame
    if done and match.round_idx + 1 >= match.rounds:
        result["final"] = state.get("metrics")
        result["match_done"] = True
    else:
        result["match_done"] = False
    return result


def get_processes(match_id):
    match = _get_match(match_id)
    if match is None:
        return {"processes": [], "error": "match not found"}
    if match.sim is None:
        return {"processes": [], "error": None}
    return {"processes": _build_processes(match), "error": None}


def reload_round(match_id):
    logs = []
    match = _get_match(match_id)
    if match is None:
        return {"done": True, "error": "match not found", "logs": logs}
    _init_round(match, match.round_idx)
    logs.append("reload_round=%d" % match.round_idx)
    state = _build_state(match)
    frame = _build_frame(match, view="full")
    done = _round_done(match)
    result = {"done": done, "logs": logs, "state": state}
    if frame is not None:
        result["frame"] = frame
    if done and match.round_idx + 1 >= match.rounds:
        result["final"] = state.get("metrics")
        result["match_done"] = True
    else:
        result["match_done"] = False
    return result


def destroy_match(match_id):
    match = _STATE["matches"].pop(match_id, None)
    if match is None:
        return {"done": True, "error": "match not found"}
    return {"done": True}


def _build_processes(match: MatchState):
    assert match.sim is not None
    size = len(match.sim.core)
    processes = []
    for wid, warrior in zip(match.warrior_ids, match.warriors):
        queue = getattr(warrior, "task_queue", []) or []
        locations = [int(pc) % size for pc in list(queue)]
        processes.append({
            "id": wid,
            "alive": len(locations) > 0,
            "queue": locations,
        })
    return processes


def _build_state(match: MatchState):
    assert match.sim is not None

    nprocs = [len(w.task_queue) for w in match.warriors]
    alive_flags = [1 if n > 0 else 0 for n in nprocs]
    per_warrior = []
    for wid, warrior, nproc in zip(match.warrior_ids, match.warriors, nprocs):
        per_warrior.append({
            "id": wid,
            "name": warrior.name,
            "author": warrior.author,
            "alive": nproc > 0,
            "n_processes": int(nproc),
            "last_executed": warrior.last_executed,
        })

    memory_coverage = [
        int(match.sim.warrior_cov[w].sum()) for w in match.warriors
    ]

    metrics = {
        "score": match.score.tolist() if match.score is not None else [],
        "alive_score": match.alive_score.tolist() if match.alive_score is not None else [],
        "total_spawned_procs": match.total_spawned.tolist() if match.total_spawned is not None else [],
        "memory_coverage": memory_coverage,
    }

    processes = _build_processes(match)

    return {
        "round_index": match.round_idx,
        "rounds": match.rounds,
        "cycle": match.cycle,
        "total_cycles": match.simargs.cycles if match.simargs else None,
        "core_size": len(match.sim.core),
        "alive_flags": alive_flags,
        "n_alive": int(sum(alive_flags)),
        "last_executed": match.sim.last_executed,
        "per_warrior": per_warrior,
        "processes": processes,
        "metrics": metrics,
    }


def _build_frame(match: MatchState, view="summary", center_addr=None, window=18):
    assert match.sim is not None
    if view is None or view == "summary":
        return None

    if center_addr is None:
        center_addr = getattr(match.sim, "last_executed", 0)

    try:
        center_addr = int(center_addr)
    except Exception:
        center_addr = 0

    size = len(match.sim.core)

    if view == "window":
        window = int(window) if window is not None else 18
        addresses = [((center_addr + offset) % size) for offset in range(-window, window + 1)]
        instructions = [str(match.sim.core[addr]) for addr in addresses]
        owners = [match.sim.memory_owner[addr] for addr in addresses]
    elif view == "full":
        addresses = None
        instructions = match.core_cache
        owners = match.sim.memory_owner
    else:
        return None

    return {
        "view": view,
        "center": center_addr % size,
        "addresses": addresses,
        "instructions": instructions,
        "owners": owners,
    }
