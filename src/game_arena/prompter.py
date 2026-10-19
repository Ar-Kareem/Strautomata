import os
import re
import sys
import json
import time
import random
import logging
import argparse
import requests
import traceback
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm
from dotenv import load_dotenv

from game_arena.utils import get_root_path, get_game_dir, get_examples_dir, setup_logging, get_policy_fn, get_config_file, get_logs_dir, get_game


assert load_dotenv(get_root_path() / '.env')


logger = setup_logging("openrouter.log", "openrouter", to_stdout=True, stdout_level=logging.INFO, rotate=True)
# add another file for errors
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh = logging.FileHandler(str(get_logs_dir() / 'openrouter-failures.log'))
fh.setLevel(logging.ERROR)
fh.setFormatter(formatter)
logger.addHandler(fh)


OPENROUTER_API_KEY = os.getenv("OPENROUTER_LAB_API_KEY")


@dataclass
class Response:
    content: Optional[str]
    usage: Optional[dict]
    reasoning: Optional[str]
    raw: Optional[dict] = None  # full OpenRouter response json


@dataclass(frozen=True)
class OpenRouterModel:
    save_name: str
    openrouter_id: str
    comments: Optional[str] = None
    parameters: Optional[dict] = None

def _openrouter_post(model: OpenRouterModel, messages: list[dict[str, str]], timeout: Optional[float] = None) -> Optional[requests.Response]:
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            },
            data=json.dumps({
                "model": model.openrouter_id,
                "messages": messages,
                **(model.parameters or {})
            }),
            timeout=timeout,
        )
        return response
    except Exception as e:
        logger.error(f"Error getting response for {model.save_name} ({model.openrouter_id}): {e}")
        return None


def get_response_single_msg(model: OpenRouterModel, user_message: str) -> Optional[Response]:
    response = _openrouter_post(model, [{
            "role": "user",
            "content": user_message
        }])
    if response is None:
        return None
    user_message_no_newlines = user_message.replace('\n', '\\n')
    logger.debug(f"single message response for '{model.openrouter_id}' with user message: '{user_message_no_newlines}'")
    try:
        response_json = response.json()
    except Exception as e:
        logger.error(f"Error parsing response for {model.save_name} ({model.openrouter_id}): {e}\nResponse: {response.text}")
        return None
    logger.debug(f"Response: {response_json}")
    if 'error' in response_json:
        logger.error(f"OpenRouter API error for '{model.save_name} ({model.openrouter_id})': {response_json['error']}")
        return None
    msg_content = response_json["choices"][0]["message"]["content"]
    usage = response_json["usage"]
    reasoning = response_json["choices"][0]["message"]['reasoning']
    return Response(content=msg_content, usage=usage, reasoning=reasoning)

def send_chat(model: OpenRouterModel, messages: list[dict[str, str]], timeout: Optional[float] = None, attempt_log: Optional[list[dict]] = None) -> Optional[Response]:
    """attempt_log: if given, one record is appended per call (success or failure) holding the raw response/error and timing."""
    assert isinstance(model, OpenRouterModel), "Model must be an OpenRouterModel"
    t_start = time.time()
    response = _openrouter_post(model, messages, timeout=timeout)
    attempt = {'t_start': t_start, 'latency_s': time.time() - t_start, 'status_code': response.status_code if response is not None else None, 'raw': None, 'error': None}
    if attempt_log is not None:
        attempt_log.append(attempt)
    last_user_message = messages[-1]['content'].replace('\n', '\\n')
    logger.debug(f"chat response for '{model.save_name} ({model.openrouter_id})' with last user message: '{last_user_message}'")
    try:
        assert response is not None, f"Response is None for {model}"
        response_json = response.json()
    except Exception as e:
        attempt['error'] = f"{type(e).__name__}: {e}"
        attempt['raw'] = response.text if response is not None else None
        logger.error(f"Error parsing response for {model.save_name} ({model.openrouter_id}): {e}\nResponse: {response.text if response is not None else None}")
        return None
    attempt['raw'] = response_json
    logger.debug(f"Response: {response_json}")
    if 'error' in response_json:
        attempt['error'] = 'openrouter_error'
        logger.error(f"OpenRouter API error for '{model.save_name} ({model.openrouter_id})': {response_json['error']}")
        return None
    msg_content = response_json["choices"][0]["message"]["content"]
    usage = response_json["usage"]
    reasoning = response_json["choices"][0]["message"].get('reasoning')
    return Response(content=msg_content, usage=usage, reasoning=reasoning, raw=response_json)


def get_prompt_from_world(game_name: str, world: str):
    config = get_config_file(game_name, world)
    game = get_game(game_name)
    return game.get_prompt(config=config)


def get_model_save_name(model: str) -> str:
    return model.split('/')[-1].replace('-', '_').replace(':', '_')

def python_code_from_response(response: str) -> str:
    _found_code = False
    _found_block = False
    if '<code>' in response:
        _found_code = True
        response = response.split('<code>')[-1]
    if '</code>' in response:
        response = response.split('</code>')[0]
    if '```python' in response:
        if not _found_code:
            logger.debug(f'    Warning: response did not contain <code>...</code> but DID have ```python')
        response = response.split('```python')[-1]
        _found_block = True
    if '```' in response:
        response = response.split('```')[0]
    if not _found_code and not _found_block:
        logger.debug(f'    Warning: response might not be a valid python code (did not contain <code>...</code> or ```python) - assuming raw python code')
    return response

def dump_to_trash(model: str, world_dir: Path, output: str):
    trash_dir = world_dir / 'trash'
    trash_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat().replace(':', '_')
    trash_file = trash_dir / f'{model}_{now}.txt'
    trash_file.touch()
    with open(trash_file, 'w') as f:
        f.write(output)

def get_info(model: OpenRouterModel, prompt: str) -> dict:
    return {
        "model": asdict(model),
        "now": datetime.now().isoformat(),
        "prompt_version": "0.3",
        "prompt": prompt,
    }

def materialize_bot(model: OpenRouterModel, prompt: str, world_dir: Path, response_text: Optional[str], usage: Optional[dict], reasoning: Optional[str], extra_info: Optional[dict] = None, attempt_label: str = '') -> bool:
    """
        Turn a raw LLM response into a bot directory (0.info.json, 1.output.txt, 2.python_code.py).
        Shared by the synchronous prompter and the batch collector.
        Returns True if a bot was saved; False if the response was empty or the code did not load (dumped to trash).
    """
    parent_dir = world_dir / model.save_name

    # save basic info
    info = get_info(model, prompt)
    info['usage'] = usage
    info['reasoning'] = reasoning
    if extra_info:
        info.update(extra_info)

    if response_text is None or response_text.strip() == '':
        logger.error(f"Response is empty for {model.openrouter_id} {attempt_label}.")
        return False
    python_code = python_code_from_response(response_text)
    python_code = python_code.replace('\\n', '\n')
    # no longer needed as we are in python 3.12
    # python_code = re.sub(r"->\s*[^:]*\|[^:]*:", "-> None:", python_code)  # remove union annotations. from "-> x | y" to "-> None" to support Python 3.9
    python_code = python_code.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')  # fix &amp; to & and &lt; to < and &gt; to >

    policy_fn, msg = get_policy_fn(python_code, '2.python_code.py', f"{model.save_name} {attempt_label}")
    if policy_fn is None:
        logger.error(f"Policy failed for {model.save_name} ({model.openrouter_id}) {attempt_label}. Dumping to trash. {msg or 'Unknown error'}")
        dump_to_trash(model.save_name, world_dir, response_text)
        return False

    # Policy works!!! TIME TO MAKE THE POLICY FILE
    # inside is 1/ 2/ ...
    # need to find the first empty folder and save the xml there
    parent_dir.mkdir(parents=True, exist_ok=True)
    subdirs = [d for d in parent_dir.iterdir() if d.is_dir()]
    candidate_nums = [int(d.name) for d in subdirs if d.name.isdigit() and any(d.iterdir())]
    max_num = max(candidate_nums) if candidate_nums else 0
    new_dir = parent_dir / f"{max_num + 1:03d}"
    new_dir.mkdir(parents=True, exist_ok=True)
    with open(new_dir / '0.info.json', 'w') as f:
        json.dump(info, f)
    with open(new_dir / '1.output.txt', 'w') as f:
        f.write(response_text)
    with open(new_dir / '2.python_code.py', 'w') as f:
        f.write(python_code)
    return True


def get_policy(model: OpenRouterModel, prompt: str, world_dir: Path, retry_count: int = 1) -> bool:
    for attempt_i in range(retry_count):
        if attempt_i > 0:  # sleep in between attempts
            time.sleep(10)
        # ask LLM and save result
        response = get_response_single_msg(model, prompt)
        if response is None:
            continue
        if materialize_bot(model, prompt, world_dir, response.content, response.usage, response.reasoning, attempt_label=f"attempt {attempt_i}"):
            return True
    else:
        logger.error(f"Policy loop failed for {model.save_name} ({model.openrouter_id}) EXITING!!!")
        return False


def get_done_counts(world_dir: Path) -> dict[str, int]:
    done_counts = {}
    for model_dir in world_dir.iterdir():
        if not model_dir.is_dir():
            continue
        model_name = get_model_save_name(model_dir.name)
        done_counts[model_name] = 0
        for subdir in model_dir.iterdir():
            if not subdir.is_dir():
                continue
            if (subdir / '1.output.txt').exists():
                # print(f"Found policy for {model_name} {subdir.name}")
                done_counts[model_name] += 1
    return done_counts


def get_openrouter_models(models: list[str]) -> list[OpenRouterModel]:
    """
        Get the OpenRouter models from the overrides file. If the model is not in the overrides file, assume it is an openrouter model.
        The overrides file is used to handle the case where the save name and the openrouter id are different.
    """
    override_json_path = Path(__file__).parent / 'prompter_overrides.json'
    overrides = json.loads(override_json_path.read_text()).get('openrouter_overrides', {})
    results: list[OpenRouterModel] = []
    for model in models:
        if model in overrides:
            override_model = overrides[model]
            if override_model.get('method', {}).get('type') != 'openrouter':
                logger.info(f"Skipping {model} because it is not an openrouter model", "(Should be: {method: {type: openrouter}})")
                continue
            results.append(OpenRouterModel(
                save_name=override_model['save_name'],
                openrouter_id=override_model['method']['openrouter_id'],
                comments=override_model.get('comments', None),
                parameters=override_model['method'].get('parameters', None)
            ))
        else:
            # for now assume it is an openrouter model
            results.append(OpenRouterModel(save_name=get_model_save_name(model), openrouter_id=model))
    return results


def main_loop(models: list[str], game_worlds: list[tuple[str, str]], n_bots: int, filter_already_done: bool, retry_count: int, max_workers: int, verbose: bool = True):
    openrouter_models = get_openrouter_models(models)
    all_todo = []
    for game, world in game_worlds:
        game_dir: Path = get_game_dir(game)
        assert game_dir.exists(), "Game directory not found"
        world_dir: Path = get_examples_dir(game) / world
        prompt = get_prompt_from_world(game, world)
        if not world_dir.exists():
            print('world directory doesn\'t exist, creating', world_dir)
            world_dir.mkdir(parents=True, exist_ok=True)

        done_counts = get_done_counts(world_dir) if filter_already_done else {}
        if verbose:
            to_print = []
            for model in openrouter_models:
                done = done_counts.get(model.save_name, 0)
                need = n_bots - done
                if need > 0:
                    to_print.append(f"    Model: {model.save_name} ({model.openrouter_id}), Need: {need}")
            if len(to_print) > 0:
                print('game', game, 'world', world)
                print('\n'.join(to_print))

        todo = [(model, i, world_dir, prompt) for i in range(n_bots) for model in openrouter_models if i >= done_counts.get(model.save_name, 0)]
        all_todo.extend(todo)
    if len(all_todo) == 0:
        print("No bots to create")
        exit(0)
    random.shuffle(all_todo)
    print('Need to do:', len(all_todo))
    max_workers = min(max_workers, len(all_todo)) or 1
    pbar = tqdm(total=len(all_todo), desc="Creating bots")

    def _create_bot(model: OpenRouterModel, i: int, world_dir: Path, prompt: str) -> bool:
        time.sleep(i * 3)
        return get_policy(model, prompt, world_dir, retry_count)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_create_bot, model, i, world_dir, prompt): (model, i, world_dir, prompt) for model, i, world_dir, prompt in all_todo}
        success_count = 0
        fail_count = 0
        for future in as_completed(future_map):
            model, i, world_dir, prompt = future_map[future]
            try:
                success = future.result()
            except Exception as e:
                logger.error(f"Error creating bot for {model.save_name} ({model.openrouter_id}): {e}")
                traceback.print_exc()
                fail_count += 1
                pbar.set_postfix_str(f"success {success_count}/{success_count + fail_count}")
                pbar.set_description(f"Failed bot {i+1}/{n_bots} for {model.save_name} ({model.openrouter_id})")
                pbar.update(1)
                continue
            if success:
                success_count += 1
            else:
                fail_count += 1
            pbar.set_postfix_str(f"success {success_count}/{success_count + fail_count}")
            pbar.set_description(f"Finished bot {i+1}/{n_bots} for {model.save_name} ({model.openrouter_id})")
            pbar.update(1)
    pbar.close()
    if fail_count > 0:
        print(f"Failed to create {fail_count} bots")
        exit(1)

    print(f"Created {success_count} bots. All done!")
    exit(0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", action="append", required=True)
    parser.add_argument("--n_bots", type=int, required=True)
    parser.add_argument("--game_worlds", type=str, required=True)
    parser.add_argument("--filter_already_done", action="store_true", help="Filter out models that already have bots")
    parser.add_argument("--retry_count", type=int, default=1, help="Retry count for each model")
    parser.add_argument("--max_workers", type=int, default=48, help="Max workers")
    args = parser.parse_args()
    models = []
    for model_list in args.models:
        pipe_idx = model_list.find('|||')
        if pipe_idx == -1:
            models.extend(model_list.split(','))
        else:
            pre_pipe = model_list[:pipe_idx]
            post_pipe = model_list[pipe_idx+3:].split(',')
            print(f'#models {pre_pipe} = {len(post_pipe)}')
            models.extend(post_pipe)
    game_worlds = args.game_worlds.split(',')
    game_worlds = [(s.split('/')[0], s.split('/')[1]) for s in game_worlds]
    main_loop(models, game_worlds, args.n_bots, args.filter_already_done, args.retry_count, args.max_workers)

if __name__ == "__main__":
    main()
