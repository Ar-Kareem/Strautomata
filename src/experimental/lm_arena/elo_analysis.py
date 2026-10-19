# From: https://github.com/lm-sys/FastChat/
import argparse
import datetime
import pickle
from pytz import timezone
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tqdm import tqdm

from experimental.lm_arena.rating_systems import (
    compute_elo,
    compute_bt,
    compute_style_control,
    compute_bootstrap_elo,
    compute_bootstrap_bt,
    compute_bootstrap_style_control,
)
from experimental.exp_utils import MODEL_NAME_MAP, LOGO_URLS

pd.options.display.float_format = "{:.2f}".format


def get_median_elo_from_bootstrap(bootstrap_df):
    median = dict(bootstrap_df.quantile(0.5))
    median = {k: int(v + 0.5) for k, v in median.items()}
    return median


def compute_pairwise_win_fraction(battles, model_order, all_models=None, limit_show_number=None):
    if all_models is None:
        all_models = set(battles["model_a"]) | set(battles["model_b"])
    # Times each model wins as Model A
    a_win_ptbl = pd.pivot_table(
        battles[battles["winner"] == "model_a"],
        index="model_a",
        columns="model_b",
        aggfunc="size",
        fill_value=0,
    )
    a_win_ptbl = a_win_ptbl.reindex(all_models, columns=all_models, fill_value=0)

    # Table counting times each model wins as Model B
    b_win_ptbl = pd.pivot_table(
        battles[battles["winner"] == "model_b"],
        index="model_a",
        columns="model_b",
        aggfunc="size",
        fill_value=0,
    )
    b_win_ptbl = b_win_ptbl.reindex(all_models, columns=all_models, fill_value=0)

    # Table counting number of A-B pairs
    num_battles_ptbl = pd.pivot_table(
        battles, index="model_a", columns="model_b", aggfunc="size", fill_value=0
    )

    # Computing the proportion of wins for each model as A and as B
    # against all other models
    row_beats_col_freq = (a_win_ptbl + b_win_ptbl.T) / (
        num_battles_ptbl + num_battles_ptbl.T
    )

    if model_order is None:
        prop_wins = row_beats_col_freq.mean(axis=1).sort_values(ascending=False)
        model_order = list(prop_wins.keys())

    if limit_show_number is not None:
        model_order = model_order[:limit_show_number]

    # Arrange ordering according to proprition of wins
    model_order_row = [m for m in model_order if m in row_beats_col_freq.index]
    model_order_col = [m for m in model_order if m in row_beats_col_freq.columns]
    row_beats_col = row_beats_col_freq.loc[model_order_row, model_order_col]
    return row_beats_col


def visualize_leaderboard_table(rating):
    models = list(rating.keys())
    models.sort(key=lambda k: -rating[k])

    emoji_dict = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    md = ""
    md += "| Rank | Model | Elo Rating | Description |\n"
    md += "| --- | --- | --- | --- |\n"
    for i, model in enumerate(models):
        rank = i + 1
        minfo = {
            'link': 'dummylink',
            'description': 'dummydescription',
        }
        emoji = emoji_dict.get(rank, "")
        md += f"| {rank} | {emoji} [{model}]({minfo['link']}) | {rating[model]:.0f} | {minfo['description']} |\n"

    return md


def visualize_pairwise_win_fraction(battles, model_order, scale=1):
    row_beats_col = compute_pairwise_win_fraction(battles, model_order)
    fig = px.imshow(
        row_beats_col,
        color_continuous_scale="RdBu",
        text_auto=".2f",
        height=700 * scale,
        width=700 * scale,
    )
    fig.update_layout(
        xaxis_title="Model B",
        yaxis_title="Model A",
        xaxis_side="top",
        title_y=0.07,
        title_x=0.5,
    )
    fig.update_traces(
        hovertemplate="Model A: %{y}<br>Model B: %{x}<br>Fraction of A Wins: %{z}<extra></extra>"
    )

    return fig


def visualize_battle_count(battles, model_order, scale=1):
    ptbl = pd.pivot_table(
        battles, index="model_a", columns="model_b", aggfunc="size", fill_value=0
    )
    battle_counts = ptbl + ptbl.T
    model_order_row = [m for m in model_order if m in battle_counts.index]
    model_order_col = [m for m in model_order if m in battle_counts.columns]
    fig = px.imshow(
        battle_counts.loc[model_order_row, model_order_col],
        text_auto=True,
        height=700 * scale,
        width=700 * scale,
    )
    fig.update_layout(
        xaxis_title="Model B",
        yaxis_title="Model A",
        xaxis_side="top",
        title_y=0.07,
        title_x=0.5,
    )
    fig.update_traces(
        hovertemplate="Model A: %{y}<br>Model B: %{x}<br>Count: %{z}<extra></extra>"
    )
    return fig


def visualize_average_win_rate(battles, limit_show_number, scale=1):
    row_beats_col_freq = compute_pairwise_win_fraction(
        battles, None, limit_show_number=limit_show_number
    )
    fig = px.bar(
        row_beats_col_freq.mean(axis=1).sort_values(ascending=False),
        text_auto=".2f",
        height=500 * scale,
        width=700 * scale,
    )
    fig.update_layout(
        yaxis_title="Average Win Rate", xaxis_title="Model", showlegend=False
    )
    return fig


def visualize_bootstrap_elo_rating(df, df_final, limit_show_number, scale=1):
    bars = (
        pd.DataFrame(
            dict(
                lower=df.quantile(0.025),
                rating=df_final,
                upper=df.quantile(0.975),
            )
        )
        .reset_index(names="model")
        .sort_values("rating", ascending=False)
    )
    bars = bars[:limit_show_number]
    bars["error_y"] = bars["upper"] - bars["rating"]
    bars["error_y_minus"] = bars["rating"] - bars["lower"]
    bars["rating_rounded"] = np.round(bars["rating"])
    fig = px.scatter(
        bars,
        x="model",
        y="rating",
        error_y="error_y",
        error_y_minus="error_y_minus",
        text="rating_rounded",
        height=700,
        width=700 * scale,
    )
    fig.update_layout(xaxis_title="Model", yaxis_title="Rating")
    return fig


def visualize_leaderboard_rating_ci(
    leaderboard_table_df,
    model_order=None,
    scale=1,
    show_ranking=True,
    height=None,
    width=None,
    show_logos=True,
    logo_y_pad=12,
    logo_size_y=None,
    logo_size_x=0.85,
    logo_x_shift=-14,
    rank_x_shift=10,
    skip_logo_models=("random",),
    use_name_map=True,
):
    df = leaderboard_table_df.reset_index(names="model").copy()
    if model_order is None:
        df = df.sort_values("rating", ascending=False)
        model_order = df["model"].tolist()
    else:
        df = df[df["model"].isin(model_order)].copy()
        df = df.sort_values("rating", ascending=False)
        model_order = df["model"].tolist()

    df["error_y"] = df["rating_q975"] - df["rating"]
    df["error_y_minus"] = df["rating"] - df["rating_q025"]
    df["final_ranking_label"] = df["final_ranking"].round().astype(int).astype(str)

    if height is None:
        height = max(320, int(420 * scale))
    if width is None:
        width = max(1240, int(1440 * scale))

    name_map = None
    logo_url_map = None
    default_logo_url = None
    if show_logos or use_name_map:
        if use_name_map:
            name_map = MODEL_NAME_MAP
        if show_logos:
            logo_url_map = LOGO_URLS
            if logo_url_map:
                default_logo_url = logo_url_map.get("DEFUALT")

    margin_l, margin_r, margin_t, margin_b = 40, 20, 20, 120
    axis_width = max((width or 800) - (margin_l + margin_r), 1)
    x_positions = np.arange(len(df), dtype=float)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=x_positions,
            y=df["rating"],
            marker=dict(line=dict(width=0)),
            error_y=dict(
                type="data",
                array=df["error_y"],
                arrayminus=df["error_y_minus"],
                thickness=1,
                width=0,
            ),
            customdata=np.stack(
                [
                    df["model"],
                    df["rating_q025"],
                    df["rating_q975"],
                    df["final_ranking"],
                ],
                axis=1,
            ),
            hovertemplate=(
                "Model: %{customdata[0]}<br>"
                "Rating: %{y:.2f}<br>"
                "CI 2.5%: %{customdata[1]:.2f}<br>"
                "CI 97.5%: %{customdata[2]:.2f}<br>"
                "Final ranking: %{customdata[3]:.0f}"
                "<extra></extra>"
            ),
        )
    )
    if show_ranking:
        rank_shift_units = rank_x_shift * max(len(df), 1) / axis_width
        fig.add_trace(
            go.Scatter(
                x=x_positions + rank_shift_units,
                y=df["rating"] + 12,
                mode="text",
                text=df["final_ranking_label"],
                textposition="top center",
                textfont=dict(size=12 * scale),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    has_logos = False
    if show_logos and logo_url_map:
        y_min = float(df["rating_q025"].min())
        y_max = float(df["rating_q975"].max())
        span = max(y_max - y_min, 1.0)
        if logo_size_y is None:
            logo_size_y = max(0.08 * span, 30 * scale)

        shift_units = logo_x_shift * max(len(df), 1) / axis_width

        images = []
        for x_pos, model, rating in zip(x_positions, df["model"], df["rating"]):
            if model in skip_logo_models:
                continue
            url = logo_url_map.get(model, default_logo_url)
            if not url:
                raise ValueError(f"No logo found for model {model}")
            images.append(
                dict(
                    source=url,
                    xref="x",
                    yref="y",
                    x=x_pos + shift_units,
                    y=rating + logo_y_pad,
                    sizex=logo_size_x,
                    sizey=logo_size_y,
                    xanchor="center",
                    yanchor="bottom",
                    layer="above",
                )
            )
        if images:
            fig.update_layout(images=images)
            has_logos = True
    fig.update_layout(
        showlegend=False,
        height=height,
        width=width,
        margin=dict(l=margin_l, r=margin_r, t=margin_t, b=margin_b),
    )
    fig.update_xaxes(
        title="Model",
        tickangle=35,
        automargin=True,
        tickmode="array",
        tickvals=x_positions,
        ticktext=[name_map.get(m, m) if name_map else m for m in model_order],
        range=[-0.5, max(len(df) - 0.5, 0.5)],
    )
    if has_logos or show_ranking:
        y_min = float(df["rating_q025"].min())
        y_max = float(df["rating_q975"].max())
        extra = 0.0
        if has_logos:
            extra = logo_y_pad + (logo_size_y or 0)
        elif show_ranking:
            extra = max(8 * scale, (y_max - y_min) * 0.02)
        pad = max((y_max - y_min) * 0.08, extra * 0.2)
        fig.update_yaxes(
            title="Rating",
            zeroline=False,
            range=[y_min - pad * 0.2, y_max + extra + pad],
        )
    else:
        fig.update_yaxes(title="Rating", zeroline=False)
    return fig


def limit_user_votes(battles, daily_vote_per_user):
    from datetime import datetime

    print("Before limiting user votes: ", len(battles))
    # add date
    battles["date"] = battles["tstamp"].apply(
        lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d")
    )

    battles_new = pd.DataFrame()
    for date in battles["date"].unique():
        # only take the first daily_vote_per_user votes per judge per day
        df_today = battles[battles["date"] == date]
        df_sub = df_today.groupby("judge").head(daily_vote_per_user)

        # add df_sub to a new dataframe
        battles_new = pd.concat([battles_new, df_sub])
    print("After limiting user votes: ", len(battles_new))
    return battles_new


def get_model_pair_stats(battles):
    battles["ordered_pair"] = battles.apply(
        lambda x: tuple(sorted([x["model_a"], x["model_b"]])), axis=1
    )

    model_pair_stats = {}

    for index, row in battles.iterrows():
        pair = row["ordered_pair"]
        if pair not in model_pair_stats:
            model_pair_stats[pair] = {"win": 0, "loss": 0, "tie": 0}

        if row["winner"] in ["tie", "tie (bothbad)"]:
            model_pair_stats[pair]["tie"] += 1
        elif row["winner"] == "model_a" and row["model_a"] == min(pair):
            model_pair_stats[pair]["win"] += 1
        elif row["winner"] == "model_b" and row["model_b"] == min(pair):
            model_pair_stats[pair]["win"] += 1
        else:
            model_pair_stats[pair]["loss"] += 1

    return model_pair_stats


def outlier_detect(
    model_pair_stats,
    battles,
    max_vote=100,
    randomized=False,
    alpha=0.05,
    c_param=0.5,
    user_list=None,
):
    if user_list is None:
        # only check user who has >= 5 votes to save compute
        user_vote_cnt = battles["judge"].value_counts()
        user_list = user_vote_cnt[user_vote_cnt >= 5].index.tolist()
    print("#User to be checked: ", len(user_list))

    bad_user_list = []
    for user in user_list:
        flag = False
        p_upper = []
        p_lower = []
        df_2 = battles[battles["judge"] == user]
        for row in df_2.iterrows():
            if len(p_upper) >= max_vote:
                break

            model_pair = tuple(sorted([row[1]["model_a"], row[1]["model_b"]]))

            if row[1]["winner"] in ["tie", "tie (bothbad)"]:
                vote = 0.5
            elif row[1]["winner"] == "model_a" and row[1]["model_a"] == model_pair[0]:
                vote = 1
            elif row[1]["winner"] == "model_b" and row[1]["model_b"] == model_pair[0]:
                vote = 1
            else:
                vote = 0

            stats = model_pair_stats[model_pair]
            # count all votes
            # ratings = np.array(
            #     [1] * stats["win"] + [0.5] * stats["tie"] + [0] * stats["loss"]
            # )

            # only count win and loss
            ratings = np.array([1] * stats["win"] + [0] * stats["loss"])
            if randomized:
                noise = np.random.uniform(-1e-5, 1e-5, len(ratings))
                ratings += noise
                vote += np.random.uniform(-1e-5, 1e-5)

            p_upper += [(ratings <= vote).mean()]
            p_lower += [(ratings >= vote).mean()]

            M_upper = np.prod(1 / (2 * np.array(p_upper)))
            M_lower = np.prod(1 / (2 * np.array(p_lower)))

            # M_upper = np.prod((1 - c_param) / (c_param * np.array(p_upper) ** c_param))
            # M_lower = np.prod((1 - c_param) / (c_param * np.array(p_lower) ** c_param))
            if (M_upper > 1 / alpha) or (M_lower > 1 / alpha):
                print(f"Identify bad user with {len(p_upper)} votes")
                flag = True
                break
        if flag:
            bad_user_list.append({"user_id": user, "votes": len(p_upper)})
    print("Bad user length: ", len(bad_user_list))
    print(bad_user_list)

    bad_user_id_list = [x["user_id"] for x in bad_user_list]
    # remove bad users
    battles = battles[~battles["judge"].isin(bad_user_id_list)]
    return battles


def filter_long_conv(row):
    threshold = 768
    for conversation_type in ["conversation_a", "conversation_b"]:
        cur_conv = row[conversation_type]
        num_tokens_all = sum([turn["num_tokens"] for turn in cur_conv])
        if num_tokens_all >= threshold:
            return True
    return False


def report_elo_analysis_results(
    battles_json,
    rating_system="bt",
    num_bootstrap=100,
    exclude_models=[],
    langs=[],
    exclude_tie=False,
    exclude_unknown_lang=False,
    daily_vote_per_user=None,
    run_outlier_detect=False,
    scale=1,
    filter_func=lambda x: True,
    style_control=False,
    num_cpu=None,
):
    battles = pd.DataFrame(battles_json)

    tqdm.pandas(desc=f"Processing using {filter_func.__name__}")
    filtered_indices = battles.progress_apply(filter_func, axis=1)
    battles = battles[filtered_indices]

    battles = battles.sort_values(ascending=True, by=["tstamp"])

    if len(langs) > 0:
        battles = battles[battles["language"].isin(langs)]
    if exclude_unknown_lang:
        battles = battles[~battles["language"].str.contains("unknown")]

    # remove excluded models
    battles = battles[
        ~(
            battles["model_a"].isin(exclude_models)
            | battles["model_b"].isin(exclude_models)
        )
    ]

    # Only use anonymous votes
    battles = battles[battles["anony"]].reset_index(drop=True)
    battles_no_ties = battles[~battles["winner"].str.contains("tie")]
    if exclude_tie:
        battles = battles_no_ties

    if daily_vote_per_user is not None:
        battles = limit_user_votes(battles, daily_vote_per_user)

    if run_outlier_detect:
        model_pair_stats = get_model_pair_stats(battles)
        battles = outlier_detect(model_pair_stats, battles)

    print(f"Number of battles: {len(battles)}")
    # Online update
    elo_rating_online = compute_elo(battles)

    if rating_system == "bt":
        if style_control:
            bootstrap_df, boostrap_coef = compute_bootstrap_style_control(
                battles, num_round=num_bootstrap
            )
            elo_rating_final, coef_final = compute_style_control(battles)
        else:
            bootstrap_df = compute_bootstrap_bt(
                battles, num_round=num_bootstrap, num_cpu=num_cpu
            )
            elo_rating_final = compute_bt(battles)
    elif rating_system == "elo":
        bootstrap_df = compute_bootstrap_elo(
            battles, num_round=num_bootstrap, num_cpu=num_cpu
        )
        elo_rating_median = get_median_elo_from_bootstrap(bootstrap_df)
        elo_rating_final = elo_rating_median

    model_order = list(elo_rating_final.keys())

    model_rating_q025 = bootstrap_df.quantile(0.025)
    model_rating_q975 = bootstrap_df.quantile(0.975)

    # compute ranking based on CI
    ranking = {}
    for i, model_a in enumerate(model_order):
        ranking[model_a] = 1
        for j, model_b in enumerate(model_order):
            if i == j:
                continue
            if model_rating_q025[model_b] > model_rating_q975[model_a]:
                ranking[model_a] += 1

    # leaderboard_table_df: elo rating, variance, 95% interval, number of battles
    leaderboard_table_df = pd.DataFrame(
        {
            "rating": elo_rating_final,
            "variance": bootstrap_df.var(),
            "rating_q975": bootstrap_df.quantile(0.975),
            "rating_q025": bootstrap_df.quantile(0.025),
            "num_battles": battles["model_a"]
            .value_counts()
            .add(battles["model_b"].value_counts(), fill_value=0),
            "final_ranking": pd.Series(ranking),
        }
    )

    model_order.sort(key=lambda k: -elo_rating_final[k])
    limit_show_number = int(25 * scale)
    model_order = model_order[:limit_show_number]

    # Plots
    leaderboard_table = visualize_leaderboard_table(elo_rating_final)
    win_fraction_heatmap = visualize_pairwise_win_fraction(
        battles_no_ties, model_order, scale=scale
    )
    battle_count_heatmap = visualize_battle_count(
        battles_no_ties, model_order, scale=scale
    )
    average_win_rate_bar = visualize_average_win_rate(
        battles_no_ties, limit_show_number, scale=scale
    )
    bootstrap_elo_rating = visualize_bootstrap_elo_rating(
        bootstrap_df, elo_rating_final, limit_show_number, scale=scale
    )
    leaderboard_rating_ci = visualize_leaderboard_rating_ci(
        leaderboard_table_df,
        model_order=model_order,
        scale=scale,
    )

    last_updated_tstamp = battles["tstamp"].max()
    last_updated_datetime = datetime.datetime.fromtimestamp(
        last_updated_tstamp, tz=timezone("US/Pacific")
    ).strftime("%Y-%m-%d %H:%M:%S %Z")

    return {
        "rating_system": rating_system,
        "elo_rating_online": elo_rating_online,
        "elo_rating_final": elo_rating_final,
        "leaderboard_table": leaderboard_table,
        "win_fraction_heatmap": win_fraction_heatmap,
        "battle_count_heatmap": battle_count_heatmap,
        "average_win_rate_bar": average_win_rate_bar,
        "bootstrap_elo_rating": bootstrap_elo_rating,
        "leaderboard_rating_ci": leaderboard_rating_ci,
        "last_updated_datetime": last_updated_datetime,
        "last_updated_tstamp": last_updated_tstamp,
        "bootstrap_df": bootstrap_df,
        "leaderboard_table_df": leaderboard_table_df,
        "style_coefficients": {
            "bootstrap": np.vstack(boostrap_coef),
            "final": coef_final,
        }
        if rating_system == "bt" and style_control
        else {},
        "battles": battles,
    }


def get_leaderboard_table_df(battles_json, rating_system="bt", num_bootstrap=100, num_cpu=None, confidence_level=0.95) -> list[dict[str, Any]]:
    battles = pd.DataFrame(battles_json)
    battles = battles.sort_values(ascending=True, by=["tstamp"])

    if rating_system == "bt":
        bootstrap_df = compute_bootstrap_bt(
            battles, num_round=num_bootstrap, num_cpu=num_cpu, verbose=False
        )
        elo_rating_final = compute_bt(battles)
    elif rating_system == "elo":
        bootstrap_df = compute_bootstrap_elo(
            battles, num_round=num_bootstrap, num_cpu=num_cpu
        )
        elo_rating_median = get_median_elo_from_bootstrap(bootstrap_df)
        elo_rating_final = elo_rating_median

    model_order = list(elo_rating_final.keys())

    alpha = 1 - confidence_level
    model_rating_qlower = bootstrap_df.quantile(alpha / 2)
    model_rating_qupper = bootstrap_df.quantile(1 - alpha / 2)

    # compute ranking based on CI
    ranking = {}
    for i, model_a in enumerate(model_order):
        ranking[model_a] = 1
        for j, model_b in enumerate(model_order):
            if i == j:
                continue
            if model_rating_qlower[model_b] > model_rating_qupper[model_a]:
                ranking[model_a] += 1

    # leaderboard_table_df: elo rating, variance, 95% interval, number of battles
    res = pd.DataFrame({
            "rating": elo_rating_final,
            "variance": bootstrap_df.var(),
            "rating_qupper": bootstrap_df.quantile(1 - alpha / 2),
            "rating_qlower": bootstrap_df.quantile(alpha / 2),
            "confidence_level": confidence_level,
            "num_battles": battles["model_a"]
            .value_counts()
            .add(battles["model_b"].value_counts(), fill_value=0),
            "final_ranking": pd.Series(ranking),
    }).reset_index(names="bot")
    return res.to_dict(orient="records")


def pretty_print_elo_rating(rating):
    model_order = list(rating.keys())
    model_order.sort(key=lambda k: -rating[k])
    for i, model in enumerate(model_order):
        print(f"{i+1:2d}, {model:25s}, {rating[model]:.0f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean-battle-file", type=str)
    parser.add_argument("--max-num-files", type=int)
    parser.add_argument("--num-bootstrap", type=int, default=100)
    parser.add_argument(
        "--rating-system", type=str, choices=["bt", "elo"], default="bt"
    )
    parser.add_argument("--exclude-models", type=str, nargs="+", default=[])
    parser.add_argument("--exclude-tie", action="store_true", default=False)
    parser.add_argument("--exclude-unknown-lang", action="store_true", default=False)
    parser.add_argument("--exclude-url", action="store_true", default=False)
    parser.add_argument("--langs", type=str, nargs="+", default=[])
    parser.add_argument("--daily-vote-per-user", type=int, default=None)
    parser.add_argument("--run-outlier-detect", action="store_true", default=False)
    parser.add_argument("--category", nargs="+", default=["full"])
    parser.add_argument("--scale", type=float, default=1)
    parser.add_argument("--style-control", action="store_true")
    parser.add_argument("--num-cpu", type=int, default=12)
    args = parser.parse_args()

    np.random.seed(42)

    battles = pd.read_json(args.clean_battle_file)

    filter_func_map = {
        "full": lambda x: True,
        "long": filter_long_conv,
        "chinese": lambda x: x["language"] == "Chinese",
        "english": lambda x: x["language"] == "English",
    }
    assert all(
        [cat in filter_func_map for cat in args.category]
    ), f"Invalid category: {args.category}"

    results = {}
    for cat in args.category:
        filter_func = filter_func_map[cat]
        results[cat] = report_elo_analysis_results(
            battles,
            rating_system=args.rating_system,
            num_bootstrap=args.num_bootstrap,
            exclude_models=args.exclude_models,
            langs=args.langs,
            exclude_tie=args.exclude_tie,
            exclude_unknown_lang=args.exclude_unknown_lang,
            daily_vote_per_user=args.daily_vote_per_user,
            run_outlier_detect=args.run_outlier_detect,
            scale=args.scale,
            filter_func=filter_func,
            style_control=args.style_control,
            num_cpu=args.num_cpu,
        )

    for cat in args.category:
        print(f"# Results for {cat} conversations")
        print("# Online Elo")
        pretty_print_elo_rating(results[cat]["elo_rating_online"])
        print("# Median")
        pretty_print_elo_rating(results[cat]["elo_rating_final"])
        print(f"last update : {results[cat]['last_updated_datetime']}")

        last_updated_tstamp = results[cat]["last_updated_tstamp"]
        cutoff_date = datetime.datetime.fromtimestamp(
            last_updated_tstamp, tz=timezone("US/Pacific")
        ).strftime("%Y%m%d")
        print(f"last update : {cutoff_date}")

    with open(f"elo_results_{cutoff_date}.pkl", "wb") as fout:
        pickle.dump(results, fout)
