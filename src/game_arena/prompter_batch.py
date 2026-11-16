"""
Prompt automata through the OpenRouter Batch API (asynchronous, 24h completion window, ~50% off on most models).

Two-phase workflow. Records live in game_arena/batches/{pending,done,failed}/<batch_id>.json.

    # 1. submit: to_place = wanted - done - pending, one batch per model covering every game/world
    python -m game_arena.prompter_batch place --n_bots 5 \
        --game_worlds "tic_tac_toe/world1,connect4/world1" \
        --models "anthropic/claude-fable-5.1-high,openai/gpt-6-astra-high" [--dry_run] [--allow_no_discount]

    # 2. later (poll as often as you like): fetch finished batches, parse, save bots / trash bad ones
    python -m game_arena.prompter_batch collect [--batch_id ID]

    python -m game_arena.prompter_batch status      # pending batches and their progress
    python -m game_arena.prompter_batch reconcile   # batches OpenRouter knows about that have no local record

Failed / expired requests are simply no longer "pending" after collect, so re-running `place` re-submits them.
"""
import re
import json
import uuid
import shutil
import argparse
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime
from dataclasses import asdict
from collections import defaultdict

from game_arena.utils import get_examples_dir
from game_arena.prompter import (
    OPENROUTER_API_KEY, OpenRouterModel, logger,
    get_openrouter_models, get_prompt_from_world, get_done_counts, materialize_bot, dump_to_trash,
)


BATCH_API = "https://openrouter.ai/api/beta/batches"
MODELS_API = "https://openrouter.ai/api/v1/models"
ENDPOINT = "/v1/chat/completions"
TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}

BATCH_DIR = Path(__file__).parent / 'z_batched'
PENDING_DIR = BATCH_DIR / 'pending'
DONE_DIR = BATCH_DIR / 'done'
FAILED_DIR = BATCH_DIR / 'failed'


def _headers() -> dict:
    assert OPENROUTER_API_KEY, "OPENROUTER_LAB_API_KEY is not set"
    return {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}


def _now() -> str:
    return datetime.now().isoformat()


# ---------------------------------------------------------------- records

def _record_path(batch_id: str, folder: Path = PENDING_DIR) -> Path:
    safe = re.sub(r'[^A-Za-z0-9_.-]', '_', batch_id)
    return folder / f"{safe}.json"


def _load_record(path: Path) -> dict:
    return json.loads(path.read_text())


def _save_record(record: dict, path: Path) -> None:
    tmp = path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(record, indent=2))
    tmp.replace(path)  # atomic on POSIX


def _pending_records() -> list[tuple[Path, dict]]:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for path in sorted(PENDING_DIR.glob('*.json')):
        out.append((path, _load_record(path)))
    return out


def _all_known_batch_ids() -> set[str]:
    ids = set()
    for folder in (PENDING_DIR, DONE_DIR, FAILED_DIR):
        if folder.exists():
            for path in folder.glob('*.json'):
                try:
                    ids.add(_load_record(path)['batch_id'])
                except Exception:
                    pass
    return ids


def get_pending_counts() -> dict[tuple[str, str, str], int]:
    """(game, world, save_name) -> number of submitted-but-not-yet-consumed requests."""
    counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for _, record in _pending_records():
        save_name = record['model']['save_name']
        for req in record['requests']:
            if not req.get('consumed'):
                counts[(req['game'], req['world'], save_name)] += 1
    return counts


# ---------------------------------------------------------------- pricing guard

def get_batch_pricing(openrouter_ids: list[str]) -> dict[str, tuple[Optional[float], Optional[float]]]:
    """openrouter_id -> (sync completion $/tok, batch completion $/tok or None if no :batch listing)."""
    data = requests.get(MODELS_API, timeout=30).json()['data']
    pricing = {m['id']: m.get('pricing', {}) for m in data}
    out = {}
    for mid in openrouter_ids:
        sync = pricing.get(mid, {}).get('completion')
        batch = pricing.get(f"{mid}:batch", {}).get('completion')
        out[mid] = (float(sync) if sync is not None else None, float(batch) if batch is not None else None)
    return out


# ---------------------------------------------------------------- place

def _custom_id(game: str, world: str, save_name: str) -> str:
    # Anthropic's batch backend only allows [A-Za-z0-9_-] in custom_id (no '.', '|', '/'). Routing on collect
    # goes through the pending record, so the id only needs to be unique and safe, not parseable.
    raw = f"{game}_{world}_{save_name}_{uuid.uuid4().hex[:12]}"
    return re.sub(r'[^A-Za-z0-9_-]', '_', raw)


def _request_body(model: OpenRouterModel, prompt: str) -> dict:
    return {
        "model": model.openrouter_id,
        "messages": [{"role": "user", "content": prompt}],
        **(model.parameters or {}),
    }


def place(models: list[str], game_worlds: list[tuple[str, str]], n_bots: int, dry_run: bool, allow_no_discount: bool) -> None:
    openrouter_models = get_openrouter_models(models)
    PENDING_DIR.mkdir(parents=True, exist_ok=True)

    # discount guard: don't queue for 24h if the batch price isn't lower
    pricing = get_batch_pricing([m.openrouter_id for m in openrouter_models])
    usable: list[OpenRouterModel] = []
    for m in openrouter_models:
        sync_p, batch_p = pricing[m.openrouter_id]
        if batch_p is None:
            msg = f"{m.openrouter_id}: no ':batch' listing on OpenRouter"
        elif sync_p is not None and batch_p >= sync_p:
            msg = f"{m.openrouter_id}: batch completion price ${batch_p*1e6:.2f}/M is not lower than sync ${sync_p*1e6:.2f}/M"
        else:
            print(f"  {m.openrouter_id}: sync ${sync_p*1e6:.2f}/M -> batch ${batch_p*1e6:.2f}/M completion")
            usable.append(m)
            continue
        if allow_no_discount:
            print(f"  WARNING {msg} (submitting anyway, --allow_no_discount)")
            usable.append(m)
        else:
            print(f"  SKIP {msg} (use the synchronous prompter, or pass --allow_no_discount)")

    pending_counts = get_pending_counts()
    per_model: dict[str, list[dict]] = defaultdict(list)  # save_name -> request records
    prompts: dict[tuple[str, str], str] = {}
    for game, world in game_worlds:
        world_dir: Path = get_examples_dir(game) / world
        world_dir.mkdir(parents=True, exist_ok=True)
        prompts[(game, world)] = get_prompt_from_world(game, world)
        done_counts = get_done_counts(world_dir)
        for m in usable:
            done = done_counts.get(m.save_name, 0)
            pending = pending_counts.get((game, world, m.save_name), 0)
            need = n_bots - done - pending
            if need > 0:
                print(f"  {game}/{world} {m.save_name}: wanted={n_bots} done={done} pending={pending} -> place {need}")
            for slot in range(need):
                per_model[m.save_name].append({
                    "custom_id": _custom_id(game, world, m.save_name),
                    "game": game, "world": world, "slot": done + pending + slot,
                    "prompt": prompts[(game, world)],
                    "consumed": False, "outcome": None,
                })

    total = sum(len(v) for v in per_model.values())
    if total == 0:
        print("Nothing to place.")
        return
    print(f"Total requests to place: {total} across {len(per_model)} batch(es)")
    if dry_run:
        print("(dry run, nothing submitted)")
        return

    for m in usable:
        reqs = per_model.get(m.save_name)
        if not reqs:
            continue
        payload = {
            "endpoint": ENDPOINT,
            "model": m.openrouter_id,
            "requests": [{"custom_id": r['custom_id'], "body": _request_body(m, r['prompt'])} for r in reqs],
        }
        resp = requests.post(BATCH_API, headers=_headers(), data=json.dumps(payload), timeout=120)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text}
        if resp.status_code not in (200, 202) or 'id' not in body:
            logger.error(f"Batch submit failed for {m.save_name}: HTTP {resp.status_code} {body}")
            continue
        record = {
            "batch_id": body['id'],
            "model": asdict(m),
            "endpoint": ENDPOINT,
            "submitted_at": _now(),
            "status": body.get('status'),
            "last_checked": _now(),
            "request_counts": body.get('request_counts'),
            "usage": None,
            "requests": reqs,
        }
        _save_record(record, _record_path(body['id']))
        print(f"  submitted {body['id']} for {m.save_name}: {len(reqs)} requests, status={body.get('status')}")


# ---------------------------------------------------------------- collect

def _fetch_batch(batch_id: str) -> dict:
    resp = requests.get(f"{BATCH_API}/{batch_id}", headers=_headers(), timeout=120)
    resp.raise_for_status()
    return resp.json()


def _fetch_results(batch_id: str, batch_obj: dict) -> Optional[list]:
    results = batch_obj.get('results')
    if results is not None:
        return results
    # some API versions serve results from a sub-resource
    resp = requests.get(f"{BATCH_API}/{batch_id}/results", headers=_headers(), timeout=300)
    if resp.status_code != 200:
        logger.error(f"Could not fetch results for {batch_id}: HTTP {resp.status_code} {resp.text[:300]}")
        return None
    body = resp.json()
    return body.get('results', body if isinstance(body, list) else None)


def _existing_custom_ids(world_dir: Path, save_name: str) -> set[str]:
    ids = set()
    model_dir = world_dir / save_name
    if not model_dir.exists():
        return ids
    for info_path in model_dir.glob('*/0.info.json'):
        try:
            cid = json.loads(info_path.read_text()).get('custom_id')
            if cid:
                ids.add(cid)
        except Exception:
            pass
    return ids


def _batch_token_prices(openrouter_id: str) -> Optional[tuple[float, float]]:
    """(prompt $/tok, completion $/tok) at batch pricing, or None if unavailable."""
    try:
        data = requests.get(MODELS_API, timeout=30).json()['data']
        pricing = {m['id']: m.get('pricing', {}) for m in data}
        pr = pricing.get(f"{openrouter_id}:batch") or pricing.get(openrouter_id)
        if pr and pr.get('prompt') is not None and pr.get('completion') is not None:
            return float(pr['prompt']), float(pr['completion'])
    except Exception as e:
        logger.warning(f"could not fetch batch pricing for {openrouter_id}: {e}")
    return None


def _fill_request_cost(usage: Optional[dict], prices: Optional[tuple[float, float]], batch_usage: Optional[dict]) -> Optional[dict]:
    """Batch results carry token counts but no per-request 'cost'. Derive it so info.json matches the sync format."""
    if not isinstance(usage, dict) or 'cost' in usage:
        return usage
    usage = dict(usage)
    pt, ct = usage.get('prompt_tokens') or 0, usage.get('completion_tokens') or 0
    if prices is not None:
        usage['cost'] = pt * prices[0] + ct * prices[1]
        usage['cost_source'] = 'derived: tokens x batch price'
    elif batch_usage and batch_usage.get('cost') and batch_usage.get('total_tokens'):
        usage['cost'] = batch_usage['cost'] * (pt + ct) / batch_usage['total_tokens']
        usage['cost_source'] = 'derived: prorated share of batch cost by tokens'
    return usage


def _process_result(model: OpenRouterModel, req: dict, result: dict) -> str:
    """Returns outcome: 'saved' | 'trash' | 'error' | 'duplicate'."""
    world_dir = get_examples_dir(req['game']) / req['world']
    label = f"batch {req['custom_id']}"
    if req['custom_id'] in _existing_custom_ids(world_dir, model.save_name):
        logger.warning(f"{label}: bot already exists for this custom_id, skipping")
        return 'duplicate'

    err = result.get('error')
    response = result.get('response') or {}
    body = response.get('body') or {}
    if err or response.get('status_code', 200) >= 400 or 'error' in body:
        detail = err or body.get('error') or response
        logger.error(f"{label}: request failed: {json.dumps(detail)[:500]}")
        dump_to_trash(model.save_name, world_dir, f"BATCH ERROR {req['custom_id']}\n{json.dumps(detail, indent=2)}")
        return 'error'

    try:
        message = body['choices'][0]['message']
        content = message.get('content')
        reasoning = message.get('reasoning')
        usage = _fill_request_cost(body.get('usage'), req.get('_prices'), req.get('_batch_usage'))
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"{label}: malformed response body ({e}): {json.dumps(body)[:500]}")
        dump_to_trash(model.save_name, world_dir, f"BATCH MALFORMED {req['custom_id']}\n{json.dumps(body, indent=2)}")
        return 'error'

    extra = {"batch": True, "batch_id": req['_batch_id'], "custom_id": req['custom_id'], "generation_id": body.get('id'), "batch_model_snapshot": req.get('_remote_model')}
    ok = materialize_bot(model, req['prompt'], world_dir, content, usage, reasoning, extra_info=extra, attempt_label=label)
    return 'saved' if ok else 'trash'


def collect(batch_id: Optional[str]) -> None:
    records = _pending_records()
    if batch_id:
        records = [(p, r) for p, r in records if r['batch_id'] == batch_id]
        if not records:
            print(f"No pending record for {batch_id}")
            return
    if not records:
        print("No pending batches.")
        return
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)

    for path, record in records:
        bid = record['batch_id']
        model = OpenRouterModel(**record['model'])
        try:
            batch_obj = _fetch_batch(bid)
        except Exception as e:
            logger.error(f"{bid}: status fetch failed: {e}")
            continue
        status = batch_obj.get('status')
        record['status'] = status
        record['last_checked'] = _now()
        record['request_counts'] = batch_obj.get('request_counts', record.get('request_counts'))
        record['usage'] = batch_obj.get('usage', record.get('usage'))
        record['remote_model'] = batch_obj.get('model', record.get('remote_model'))
        _save_record(record, path)
        counts = record.get('request_counts') or {}
        if status not in TERMINAL_STATUSES:
            print(f"  {bid} [{model.save_name}] {status}: {counts.get('completed', '?')}/{counts.get('total', '?')} completed, {counts.get('failed', 0)} failed")
            continue

        results = _fetch_results(bid, batch_obj) if status != 'cancelled' else []
        if results is None:
            print(f"  {bid} [{model.save_name}] {status} but results unavailable; leaving pending")
            continue
        by_cid = {r.get('custom_id'): r for r in results}
        prices = _batch_token_prices(model.openrouter_id)
        derived_total = 0.0
        tally = defaultdict(int)
        for req in record['requests']:
            if req.get('consumed'):
                continue
            result = by_cid.get(req['custom_id'])
            if result is None:
                continue  # not returned (expired/failed batch); stays unconsumed -> re-placed next time
            req['_batch_id'] = bid
            req['_prices'] = prices
            req['_batch_usage'] = record.get('usage')
            req['_remote_model'] = record.get('remote_model')
            try:
                outcome = _process_result(model, req, result)
                u = ((result.get('response') or {}).get('body') or {}).get('usage')
                u = _fill_request_cost(u, prices, record.get('usage'))
                req['cost'] = u.get('cost') if isinstance(u, dict) else None
                derived_total += req['cost'] or 0.0
            except Exception as e:
                logger.error(f"{bid} {req['custom_id']}: unexpected error {e}")
                outcome = 'error'
            for k in ('_batch_id', '_prices', '_batch_usage', '_remote_model'):
                req.pop(k, None)
            req['consumed'] = True
            req['outcome'] = outcome
            req['consumed_at'] = _now()
            tally[outcome] += 1
            _save_record(record, path)  # after every bot so a crash never double-writes

        unconsumed = sum(1 for r in record['requests'] if not r.get('consumed'))
        cost = (record.get('usage') or {}).get('cost')
        if isinstance(cost, (int, float)) and cost > 0 and unconsumed == 0 and sum(tally.values()) == len(record['requests']):
            if abs(derived_total - cost) > 0.01 * cost:
                logger.warning(f"{bid}: derived per-request costs sum to ${derived_total:.4f} but batch reports ${cost:.4f}")
        summary = ", ".join(f"{k}={v}" for k, v in sorted(tally.items())) or "nothing new"
        if status == 'completed' and unconsumed == 0:
            dest = DONE_DIR
        else:
            for r in record['requests']:
                if not r.get('consumed'):
                    r['outcome'] = 'not_returned'
            dest = FAILED_DIR
        shutil.move(str(path), str(_record_path(bid, dest)))
        cost_str = f" cost=${cost:.2f}" if isinstance(cost, (int, float)) else ""
        print(f"  {bid} [{model.save_name}] {status}: {summary}, not_returned={unconsumed}{cost_str} -> {dest.name}/")


# ---------------------------------------------------------------- status / reconcile

def status() -> None:
    records = _pending_records()
    if not records:
        print("No pending batches.")
        return
    for path, r in records:
        try:  # refresh from server; fall back to the local snapshot if offline
            b = _fetch_batch(r['batch_id'])
            r['status'], r['last_checked'] = b.get('status'), _now()
            r['request_counts'] = b.get('request_counts', r.get('request_counts'))
            r['usage'] = b.get('usage', r.get('usage'))
            _save_record(r, path)
        except Exception as e:
            print(f"  (could not refresh {r['batch_id']}: {e})")
        n = len(r['requests'])
        consumed = sum(1 for q in r['requests'] if q.get('consumed'))
        c = r.get('request_counts') or {}
        print(f"  {r['batch_id']} [{r['model']['save_name']}] status={r.get('status')} submitted={r['submitted_at'][:19]} "
              f"remote {c.get('completed', '?')}/{c.get('total', n)} done, {c.get('failed', 0)} failed | local consumed {consumed}/{n}")
    print("Pending per (game/world, model):")
    for (g, w, m), k in sorted(get_pending_counts().items()):
        print(f"    {g}/{w} {m}: {k}")


def reconcile() -> None:
    resp = requests.get(BATCH_API, headers=_headers(), timeout=60)
    resp.raise_for_status()
    body = resp.json()
    remote = body.get('data', body if isinstance(body, list) else [])
    known = _all_known_batch_ids()
    orphans = [b for b in remote if b.get('id') not in known]
    if not orphans:
        print(f"All {len(remote)} remote batches have local records.")
        return
    print("Remote batches with NO local record (submitted but record write failed?):")
    for b in orphans:
        c = b.get('request_counts') or {}
        print(f"  {b.get('id')} model={b.get('model')} status={b.get('status')} {c.get('completed', '?')}/{c.get('total', '?')} created={b.get('created_at')}")
    print("Inspect them on OpenRouter; results can be adopted by hand if needed.")


# ---------------------------------------------------------------- cli

def _parse_models(model_args: list[str]) -> list[str]:
    models = []
    for model_list in model_args:
        pipe_idx = model_list.find('|||')
        models.extend((model_list if pipe_idx == -1 else model_list[pipe_idx + 3:]).split(','))
    return [m for m in models if m]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('place', help='submit batches for (wanted - done - pending) bots')
    p.add_argument("--models", action="append", required=True)
    p.add_argument("--n_bots", type=int, required=True)
    p.add_argument("--game_worlds", type=str, required=True)
    p.add_argument("--dry_run", action="store_true")
    p.add_argument("--allow_no_discount", action="store_true", help="submit even if the model has no batch discount")

    c = sub.add_parser('collect', help='fetch finished batches, save bots, trash failures')
    c.add_argument("--batch_id", type=str, default=None)

    sub.add_parser('status', help='show pending batches')
    sub.add_parser('reconcile', help='list remote batches with no local record')

    args = parser.parse_args()
    if args.cmd == 'place':
        game_worlds = [(s.split('/')[0], s.split('/')[1]) for s in args.game_worlds.split(',') if s]
        place(_parse_models(args.models), game_worlds, args.n_bots, args.dry_run, args.allow_no_discount)
    elif args.cmd == 'collect':
        collect(args.batch_id)
    elif args.cmd == 'status':
        status()
    elif args.cmd == 'reconcile':
        reconcile()


if __name__ == '__main__':
    main()
