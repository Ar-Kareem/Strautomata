import io
import os
import time
import sys
import copy
import json
import inspect
import random
from typing import Optional
import urllib.request
from pathlib import Path
from functools import lru_cache
from datetime import date, datetime
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

from tqdm.notebook import tqdm
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from game_arena import base
from game_arena import utils
from game_arena import run_leaderboard


MODEL_NAME_MAP = {
        "gpt_6_astra_high": "GPT-6 Astra High",
        "gpt_5.6_sol_high": "GPT-5.6 Sol High",
        "gpt_5.5_xhigh": "GPT-5.5 XHigh",
        "gpt_5.5_high": "GPT-5.5 High",
        "gpt_5.5_medium": "GPT-5.5 Medium",
        "gpt_5.5_low": "GPT-5.5 Low",
        "gpt_5.5_instant": "GPT-5.5 Instant",
        "gpt_5.4": "GPT-5.4",
        "gpt_5.4_instant": "GPT-5.4 Instant",
        "gpt_5.4_low": "GPT-5.4 Low",
        "gpt_5.4_medium": "GPT-5.4 Medium",
        "gpt_5.4_high": "GPT-5.4 High",
        "gpt_5.2": "GPT-5.2 (Adaptive)",
        "gpt_5_mini": "GPT-5 Mini",
        "gpt_5.4_nano": "GPT-5.4 Nano",
        "gpt_5.2_codex": "GPT-5.2 Codex",
        "gpt_4o_mini": "GPT-4o Mini",

        "gemini_3_pro_preview": "Gemini 3 Pro",
        "gemini_3_flash_preview": "Gemini 3 Flash",
        "gemini_2.0_flash_001": "Gemini 2.0 Flash",
        "gemini_3.1_flash_lite_preview": "Gemini 3.1 Flash",
        "gemini_3.8_flash": "Gemini 3.8 Flash",

        "claude_opus_4.5": "Claude Opus 4.5",
        "claude_haiku_4.5": "Claude Haiku 4.5",
        "claude_sonnet_4.5": "Claude Sonnet 4.5",
        "claude_opus_4.6": "Claude Opus 4.6 (instant)",
        "claude_opus_4.7_high": "Claude Opus 4.7 High",
        "claude_fable_5.1_high": "Claude Fable 5.1 High",

        "kimi_k2_thinking": "Kimi K2",
        "kimi_k2.5": "Kimi K2.5",
        "kimi_k3": "Kimi K3",

        "glm_4.7": "GLM 4.7",
        "glm_5": "GLM 5",

        "minimax_m2": "MiniMax M2",
        "minimax_m2.1": "MiniMax M2.1",
        "minimax_m2.7": "MiniMax M2.7",

        "deepseek_v3.2": "DeepSeek V3.2",
        "deepseek_v4_pro": "DeepSeek V4 Pro",
        "deepseek_chat_v3_0324": "DeepSeek Chat V3",
        "deepseek_r1t2_chimera_free": "DeepSeek R1T2",
        "tng_r1t_chimera_free": "DeepSeek TNG R1T",

        "gpt_oss_120b": "GPT-OSS 120B",

        "mimo_v2_flash_free": "MiMo V2 Flash",
        "mimo_v2_flash": "MiMo V2 Flash",

        "qwen3_235b_a22b_2507": "Qwen3 235B",
        "qwen3_next_80b_a3b_instruct": "Qwen3 Next 80B",
        "qwen3_32b": "Qwen3 32B",
        "qwen3_coder": "Qwen3 Coder",
        "qwen3_coder_30b_a3b_instruct": "Qwen3 Coder 30B",

        "muse_spark_1.3": "Muse Spark 1.3",

        "kat_coder_pro": "KAT Coder Pro",
        "grok_code_fast_1": "Grok Code Fast 1",

        "devstral_2512_free": "Devstral",
        "devstral_2512": "Devstral",
        "ministral_14b_2512": "Ministral 14B",
        "nemotron_nano_12b_v2_vl_free": "Nemotron Nano 12B",
        "trinity_mini_free": "Trinity Mini",
        'solar_pro_3_free': 'Solar Pro 3 Free',

        "random": "Random",
    }

# Human-readable model name -> tuple metadata.
# Current tuple schema: (is_open_source, total_parameters_billions, parameter_details)
MODEL_NAME_TUPLE_MAP = {
    "Claude Opus 4.5": (False, None, None),
    "Claude Opus 4.6 (instant)": (False, None, None),
    "Claude Sonnet 4.5": (False, None, None),
    "Claude Opus 4.7 High": (False, None, None),
    "Claude Fable 5.1 High": (False, None, None),
    "DeepSeek Chat V3": (True, 685.0, "685B (MoE; 37B)"),  # ??? (openrouter 685B, HF 685B, arxiv 671B & MOE 37B, github "The total size of DeepSeek-V3 models on Hugging Face is 685B, which includes 671B of the Main Model weights and 14B of the Multi-Token Prediction (MTP) Module weights.")
    "DeepSeek R1T2": (True, 671.0, "671B (MoE)"),  # ??? dont know active count
    "DeepSeek TNG R1T": (False, None, None),  # dont try to search on openrouter; this is the link https://openrouter.ai/tngtech/tng-r1t-chimera; NOT https://openrouter.ai/tngtech/deepseek-r1t-chimera
    "DeepSeek V3.2": (True, 685.0, "685B (MoE; 37B)"),  # ??? (openrouter none, HF 685B, based on V3 so same MOE)
    "DeepSeek V4 Pro": (True, 1600.0, "1600B (MoE; 49B)"),  # MIT; https://deepseek.com/en/news/v4-preview/
    "Devstral": (True, 123.0, "123B"),  # good
    "GLM 4.7": (True, 355.0, "355B (MoE; 32B)"),  # ??? (4.5 arxiv 355B (MoE; 32B), DigitalApplied 355B (MoE; 32B) https://www.digitalapplied.com/blog/glm-4-7-zai-coding-model-guide)
    "GLM 5": (True, 744.0, "744B (MoE; 40B)"),  # good (arxiv)
    "GPT-4o Mini": (False, None, None),
    "GPT-5 Mini": (False, None, None),
    "GPT-5.2 (Adaptive)": (False, None, None),
    "GPT-5.2 Codex": (False, None, None),
    "GPT-5.4": (False, None, None),
    "GPT-5.4 Instant": (False, None, None),
    "GPT-5.4 Low": (False, None, None),
    "GPT-6 Astra High": (False, None, None),
    "GPT-5.6 Sol High": (False, None, None),
    "GPT-5.5 XHigh": (False, None, None),
    "GPT-5.5 High": (False, None, None),
    "GPT-5.5 Medium": (False, None, None),
    "GPT-5.5 Low": (False, None, None),
    "GPT-5.5 Instant": (False, None, None),
    "GPT-OSS 120B": (True, 117.0, "117B (MoE; 5.1B)"),  # good
    "Gemini 2.0 Flash": (False, None, None),
    "Gemini 3 Flash": (False, None, None),
    "Gemini 3 Pro": (False, None, None),
    "Gemini 3.8 Flash": (False, None, None),
    "Grok Code Fast 1": (False, None, None),
    "KAT Coder Pro": (False, None, None),
    "Kimi K2": (True, 1000.0, "1000B (MoE; 32B)"),  # good
    "Kimi K2.5": (True, 1000.0, "1000B (MoE; 32B)"),  # good
    "Kimi K3": (True, 2800.0, "2800B (MoE; 104B)"),  # Open weights, Kimi K3 License; https://huggingface.co/moonshotai/Kimi-K3
    "MiMo V2 Flash": (True, 309.0, "309B (MoE; 15B)"),  # good
    "MiniMax M2": (True, 230.0, "230B (MoE; 10B)"),  # good
    "MiniMax M2.1": (True, 230.0, "230B (MoE; 10B)"),  # good
    "Ministral 14B": (True, 13.5, "13.5B"),  # good (HF 13.5B Language Model 0.4B Vision Encoder)
    "Muse Spark 1.3": (False, None, None),  # meta/muse-spark-1.3 on openrouter
    "Nemotron Nano 12B": (True, 12.0, "12B"),  # good
    "Qwen3 235B": (True, 235.0, "235B (MoE; 22B)"),  # good
    "Qwen3 32B": (True, 32.8, "32.8B"),  # good
    "Qwen3 Coder": (True, 480.0, "480B (MoE; 35B)"),  # good
    "Qwen3 Coder 30B": (True, 30.5, "30.5B (MoE; 3.3B)"),  # good (HF)
    "Qwen3 Next 80B": (True, 80.0, "80B (MoE; 3B)"),  # good (HF)
    "Solar Pro 3 Free": (False, 102.0, "102B (MoE; 12B)"),  # good
    "Trinity Mini": (True, 26.0, "26B (MoE; 3B)"),  # good
}

# (optional) per-model logo URLs; keep PNGs here if you add more
_company_logos = {
    'minimax':'https://registry.npmmirror.com/@lobehub/icons-static-png/latest/files/dark/minimax-color.png',
    'qwen':'https://custom.typingmind.com/assets/models/qwen2.png',
    'mimo':'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Xiaomi_logo_%282021-%29.svg/500px-Xiaomi_logo_%282021-%29.svg.png',
    'kwaipilot': 'https://registry.npmmirror.com/@lobehub/icons-static-png/latest/files/light/kwaipilot.png',
    'trinity': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR51bVJbUsKo2oHNJj4-Ydyl99Pi9ivM6-CRA&s',
    'nvidia': 'https://registry.npmmirror.com/@lobehub/icons-static-png/latest/files/dark/nvidia-color.png',
    'meta': 'https://registry.npmmirror.com/@lobehub/icons-static-png/latest/files/dark/meta-color.png',
    'openai': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQVRSNCZKUcvSYkmDLtSNNaRwRDh8rz5HxHA&s',
    # 'gemini': 'https://brandlogos.net/wp-content/uploads/2025/03/gemini_icon-logo_brandlogos.net_aacx5.png',
    'gemini': 'https://i.imgur.com/f1fjokC.png',
    'claude': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ9NAHBHbG_tj_AFFrJGCKAWEPDRtvFL28sug&s',
    'deepseek': 'https://custom.typingmind.com/assets/models/deepseek.png',
    'grok': 'https://raw.githubusercontent.com/lobehub/lobe-icons/refs/heads/master/packages/static-png/light/grok.png',
    'mistral': 'https://custom.typingmind.com/assets/models/mistralai.png',
    'kimi': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrC6cAlvFjySE6YHnaZwbHZq8U7VkAvalQEw&s',
    'glm': 'https://pbs.twimg.com/profile_images/1970775077181411328/W8XKaUIh_400x400.jpg',
    'upstage': 'https://pbs.twimg.com/profile_images/1763095918096924673/weqDbuYr_400x400.jpg'
}
    
LOGO_URLS = {
    'gpt_6_astra_high': _company_logos['openai'],
    'gpt_5.6_sol_high': _company_logos['openai'],
    'gpt_5.5_xhigh': _company_logos['openai'],
    'gpt_5.5_high': _company_logos['openai'],
    'gpt_5.5_medium': _company_logos['openai'],
    'gpt_5.5_low': _company_logos['openai'],
    'gpt_5.5_instant': _company_logos['openai'],
    'gpt_5.4': _company_logos['openai'],
    'gpt_5.4_instant': _company_logos['openai'],
    'gpt_5.4_low': _company_logos['openai'],
    'gpt_5.4_medium': _company_logos['openai'],
    'gpt_5.4_high': _company_logos['openai'],
    'gpt_5.2': _company_logos['openai'],
    'gpt_5.4_nano': _company_logos['openai'],
    'gpt_5_mini': _company_logos['openai'],
    'gpt_4o_mini': _company_logos['openai'],
    'gpt_5.2_codex': _company_logos['openai'],
    'gpt_oss_120b': _company_logos['openai'],

    'gemini_3.1_flash_lite_preview': _company_logos['gemini'],
    'gemini_3_flash_preview': _company_logos['gemini'],
    'gemini_2.0_flash_001': _company_logos['gemini'],
    'gemini_3_pro_preview': _company_logos['gemini'],
    'gemini_3.8_flash': _company_logos['gemini'],

    'kimi_k2.5': _company_logos['kimi'],
    'kimi_k3': _company_logos['kimi'],
    'kimi_k2_thinking': _company_logos['kimi'],

    'claude_sonnet_4.5': _company_logos['claude'],
    'claude_haiku_4.5': _company_logos['claude'],
    'claude_opus_4.5': _company_logos['claude'],
    'claude_opus_4.6': _company_logos['claude'],
    'claude_opus_4.7_high': _company_logos['claude'],
    'claude_fable_5.1_high': _company_logos['claude'],

    'qwen3_235b_a22b_2507': _company_logos['qwen'],
    'qwen3_next_80b_a3b_instruct': _company_logos['qwen'],
    'qwen3_coder': _company_logos['qwen'],
    'qwen3_coder_30b_a3b_instruct': _company_logos['qwen'],
    'qwen3_32b': _company_logos['qwen'],

    'deepseek_v3.2': _company_logos['deepseek'],
    'deepseek_v4_pro': _company_logos['deepseek'],
    'deepseek_r1t2_chimera_free': _company_logos['deepseek'],
    'deepseek_chat_v3_0324': _company_logos['deepseek'],
    'tng_r1t_chimera_free': _company_logos['deepseek'], 
    
    'minimax_m2': _company_logos['minimax'],
    'minimax_m2.1': _company_logos['minimax'],
    'minimax_m2.7': _company_logos['minimax'],

    'ministral_14b_2512': _company_logos['mistral'],
    'devstral_2512_free': _company_logos['mistral'],
    'devstral_2512': _company_logos['mistral'],

    'mimo_v2_flash_free': _company_logos['mimo'],
    'mimo_v2_flash': _company_logos['mimo'],

    'glm_4.7': _company_logos['glm'],
    'glm_5': _company_logos['glm'],

    'muse_spark_1.3': _company_logos['meta'],
    'grok_code_fast_1': _company_logos['grok'],
    'kat_coder_pro': _company_logos['kwaipilot'],
    'trinity_mini_free': _company_logos['trinity'],
    'nemotron_nano_12b_v2_vl_free': _company_logos['nvidia'],
    'solar_pro_3_free': _company_logos['upstage'],

    'DEFUALT': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_KeZcnUAdVOHNnAUKS2CdI2iJnRTImISHZg&s',
}


# these must be completely removed
_ignore_file = utils.get_root_path() / 'src' / 'experimental' / 'model_ignore.json'
NAME_DELETE = json.loads(_ignore_file.read_text())['model_ignore']
NAME_FIX_MAP = {
    # 'kat_coder_pro_free': 'kat_coder_pro',
    # 'kat_code_pro_free': 'kat_coder_pro',
    'mimo_v2_flash_free': 'mimo_v2_flash',
    'devstral_2512_free': 'devstral_2512',
}


MAIN_GAMES_WORLD_COLUMNS: list[tuple[str, str, str, Optional[str]]] = [
    ('tic_tac_toe_3d', 'world1', '3D TTT', None),
    ('tic_tac_toe', 'world1', '3x3 TTT', None),
    ('tic_tac_toe', 'world2', '4x4 TTT', None),
    # ('blackjack', 'world1', 'Blackjack', None),
    ('battleships', 'world1', 'Battleships', None),
    ('connect4', 'world1', 'Connect4', None),
    ('lines_of_action', 'world1', 'LoA', None),
    ('mancala', 'world1', 'Mancala', None),
    ('clobber', 'world1', 'Clobber', None),
    ('pentago', 'world1', 'Pentago', None),
    ('amazons', 'world1', 'Amazons', None),
    ('backgammon', 'world1', 'Backgammon', None),
    ('nim', 'world1', 'Nim', None),
    ('othello', 'world1', 'Othello', None),
    ('dots_and_boxes', 'world1', 'Dots&B', None),
    ('breakthrough', 'world1', 'Breakthrough', None),
    ('hex', 'world1', 'Hex', None),
    ('havannah', 'world1', 'Havannah', None),
    ('go', 'world1', 'Go', None),
    ('checkers', 'world1', 'Checkers', None),
    ('chess', 'worlduci1', 'Chess UCI', None),
    # ('chess', 'world1', 'Chess', None),
    # ('go', 'worldmem1', 'Go', None),
]


# --------------- END OF CONSTANTS ---------------


_DEBUG_PRINTED = set()
def model_name_map(model_name: str):
    if '/' in model_name:
        a, b = model_name.split('/', 1)
        return model_name_map(a) + f'/{b}'
    if model_name not in MODEL_NAME_MAP and model_name not in _DEBUG_PRINTED:
        print(model_name, 'missing')
        _DEBUG_PRINTED.add(model_name)
    if model_name not in LOGO_URLS and model_name != 'random' and model_name not in _DEBUG_PRINTED:
        print(model_name, 'missing logo')
        _DEBUG_PRINTED.add(model_name)
    return MODEL_NAME_MAP.get(model_name, model_name)

@lru_cache(maxsize=256)
def get_logo(name: str, size: int = 96) -> np.ndarray:
    url = LOGO_URLS.get(name, LOGO_URLS["DEFUALT"])
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = r.read()

    img = Image.open(io.BytesIO(data)).convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)

    bg = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    bg.paste(img, (0, 0), img)          # uses img alpha as mask
    out = bg.convert("RGB")

    return np.asarray(out, dtype=np.uint8)


def get_match_results(match_json: Path, get_pre_elimination: bool = False):
    if isinstance(match_json, str):
        match_json = Path(match_json)
    if isinstance(match_json, Path) and match_json.exists():
        with open(match_json, 'r') as f:
            match_json_data = json.load(f)
    else:
        assert False, f"Match JSON file not found {match_json}"
    all_data = run_leaderboard.filter_matches_to_qual_bots(match_json_data['match_results'], match_json_data.get('qual_bot_names'))
    if get_pre_elimination:
        pre_elim_matches = match_json_data['pre_elimination_results']['match_results'] if match_json_data.get('pre_elimination_results') else []
        return all_data, pre_elim_matches
    return all_data


def get_wins_against_random(all_data, combine_method: str):
    matches_with_random = [m for m in all_data if m['name0'].endswith('random') or m['name1'].endswith('random')]
    if len(matches_with_random) == 0:
        return None
    score_vs_random = defaultdict(int)
    total_vs_random = defaultdict(int)
    for m in matches_with_random:
        winner = utils.get_match_result(m, verbose=False)[1]
        if m['name0'] == 'random':
            score_vs_random[m['name1']] += (winner == 1)  # 1 means agent wins, 0 means random wins
            total_vs_random[m['name1']] += 1
        else:
            score_vs_random[m['name0']] += (winner == 0)  # 1 means random wins, 0 means agent wins
            total_vs_random[m['name0']] += 1
    if combine_method == 'combine':
        score_vs_random_combined = defaultdict(float)
        total_vs_random_combined = defaultdict(int)
        for k, v in score_vs_random.items():
            score_vs_random_combined[k.split('/')[0]] += v
            total_vs_random_combined[k.split('/')[0]] += total_vs_random[k]
        for k, v in score_vs_random_combined.items():
            score_vs_random_combined[k] = v / total_vs_random_combined[k]
        series = pd.Series(score_vs_random_combined).round(2)
        return series
    elif combine_method == 'none':
        assert len(score_vs_random) > 0, f"No matches with random found"
        return pd.Series(score_vs_random).round(2)
    else:
        raise ValueError(f'combine_method {combine_method} not supported')


def get_done_count(all_data):
    matches_done = [m for m in all_data if m['done'] and m['r'] is not None]
    done_count = defaultdict(int)
    for m in matches_done:
        done_count[m['name0']] += 1
        done_count[m['name1']] += 1
    return pd.Series(done_count)
# all_data = get_match_results('pentago', 'world1', 'matches_pentago_world1_703_1.json')
# get_done_count(all_data)


def get_wins_count(all_data, combine_method: str):
    score = defaultdict(int)
    total = defaultdict(int)
    for m in all_data:
        winner = utils.get_match_result(m, verbose=False)[1]
        score[m['name0']] += (winner == 0)  # 1 means agent wins, 0 means random wins
        score[m['name1']] += (winner == 1)  # 1 means agent wins, 0 means random wins
        total[m['name0']] += 1
        total[m['name1']] += 1
    if combine_method == 'combine':
        score_combined = defaultdict(float)
        total_combined = defaultdict(int)
        for k, v in score.items():
            score_combined[k.split('/')[0]] += v
            total_combined[k.split('/')[0]] += total[k]
        for k, v in score_combined.items():
            score_combined[k] = v / total_combined[k]
        series = pd.Series(score_combined).round(2)
        return series
    elif combine_method == 'none':
        return pd.Series(score).round(2)
    else:
        raise ValueError(f'combine_method {combine_method} not supported')
# all_data = get_match_results('mancala', 'world1', 'matches_mancala_world1_4186_1.json')
# get_wins_count(all_data, 'combine')

# get_wins_count('connect4', 'world1', 'matches_8128_2.json', 'combine')
# get_wins_count('mancala', 'world1', 'matches_mancala_world1_120_2.json', 'combine')
# get_wins_count('mancala', 'world1', 'matches_mancala_world1_120_2.json', 'combine')
# get_wins_count('mancala', 'world1', 'matches_mancala_world1_120_2.json', 'none')
# get_wins_count('lines_of_action', 'world1', 'matches_lines_of_action_world1_465_2.json', 'combine')


def get_match_file_path(game_str, world, match_json: Optional[str] = None, result_dir: str = 'results'):
    match_json_path = None
    if match_json is None:
        try:
            result_dir_path = Path(result_dir)
            matches = list(result_dir_path.glob(f'matches_{game_str}_{world}*.json'))
            assert len(matches) > 0, f"No matches found for {game_str} {world}"
            assert len(matches) == 1, f"Multiple matches found for {game_str} {world}: {matches}"
            match_json_path = matches[0]
        except Exception as e:
            print(f'ERROR========================== {game_str} {world}\nERROR {game_str} {world}: {e}')
            return None
    elif isinstance(match_json, str):
        match_json_path = Path(result_dir) / match_json
    else:
        match_json_path = match_json
    return match_json_path

def get_main_elo_data(gs: list[tuple[str, str, str, Optional[str]]], result_dir: str = 'results'):
    elos = []
    elos_pre = []
    colnames = []
    raw_match_data = {}
    pruned_match_data = {}
    wins_against_random = {}
    done_count = {}
    wins_count = {}
    top_bot_ids = {}
    total_num_games = 0
    for game_str, world, colname, match_json in gs:
        match_json = get_match_file_path(game_str, world, match_json, result_dir=result_dir)
        if match_json is None:
            continue
        all_data_pruned = get_match_results(match_json)
        all_data_pruned = [g for g in all_data_pruned if g['name0'].split('/')[0] not in NAME_DELETE and g['name1'].split('/')[0] not in NAME_DELETE]  # type: ignore
        raw_match_data[colname] = copy.deepcopy(all_data_pruned)
        num_games = len(all_data_pruned)
        print(f'{game_str} {world} {len(all_data_pruned)}')
        total_num_games += num_games

        elo_pre, top_models = run_leaderboard.get_elo_df_combined(all_data_pruned, combine_method='top_1', verbose=False)
        elos_pre.append(elo_pre)
        assert top_models is not None, f"UNEXPECTED: Top models is None for {game_str} {world}"
        top_models_names = set(top_models)
        all_data_pruned = [g for g in all_data_pruned if g['name0'] in top_models_names and g['name1'] in top_models_names]  # type: ignore
        for g in all_data_pruned:
            assert isinstance(g, dict), f"All data must be a dictionary"
            g['name0'] = g['name0'].split('/')[0]
            # if g['name0'].startswith('world1'):
            #     g['name0'] = g['name0'].split(':')[1]
            g['name1'] = g['name1'].split('/')[0]
            # if g['name1'].startswith('world1'):
            #     g['name1'] = g['name1'].split(':')[1]
            g['name0'] = NAME_FIX_MAP.get(g['name0'], g['name0'])
            g['name1'] = NAME_FIX_MAP.get(g['name1'], g['name1'])
        pruned_match_data[colname] = all_data_pruned.copy()
        random.shuffle(all_data_pruned)
        elo_post, top_models = run_leaderboard.get_elo_df_combined(all_data_pruned, combine_method='none', verbose=False, learning_rate=4, iters=500)
        elos.append(elo_post)
        colnames.append(colname)

        # wins_against_random[colname] = get_wins_against_random(all_data_pruned, 'combine')
        wins_against_random[colname] = get_wins_against_random(all_data_pruned, 'none')
        done_count[colname] = get_done_count(all_data_pruned)
        # print(colname, done_count[colname])
        wins_count[colname] = get_wins_count(all_data_pruned, 'combine')

        top_bot_ids_game = [x.split('/') for x in top_models_names]
        top_bot_ids[colname] = {x[0]: (x[1] if len(x) > 1 else '') for x in top_bot_ids_game if x[0] not in NAME_DELETE}
    print('total games =', total_num_games)
    for i in range(len(elos)):
        elos[i] = elos[i].astype(float)
    return {
        'elos': elos,
        'colnames': colnames,
        'elos_pre': elos_pre,
        'raw_match_data': raw_match_data,
        'pruned_match_data': pruned_match_data,
        'wins_against_random': wins_against_random,
        'done_count': done_count,
        'wins_count': wins_count,
        'top_bot_ids': top_bot_ids,
        'total_num_games': total_num_games,
    }
