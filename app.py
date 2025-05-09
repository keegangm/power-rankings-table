import streamlit as st

import pandas as pd
import numpy as np

import os
import requests
from io import StringIO
import pytz
import datetime as dt
import matplotlib.pyplot as plt
from datetime import date, timedelta
from io import BytesIO
import base64

from support import nba_teams


def find_file(file_name):
    """Find file within Dash_Deploy/support/ or support/."""
    file_name = f"{file_name}.csv"
    possible_paths = [
        os.path.join("Dash_Deploy", "support", "data", file_name),
        os.path.join("support", "data", file_name),
    ]

    for file_path in possible_paths:
        if os.path.exists(file_path):
            return file_path  # Return the first found file

    return None  # File not found in either path


WEEK_REFERENCE_PATH = find_file("nba_weeks_ref")


def read_nba_week():
    """Read NBA Week from reference file."""
    return pd.read_csv(
        WEEK_REFERENCE_PATH, parse_dates=["sunday"], dtype={"nba_week": int}
    )


def read_ranking_file():
    """Read NBA Ranking file from GitHub first, then local if unavailable."""

    github_url = "https://raw.githubusercontent.com/keegangm/nba-power-rankings/main/Dash_Deploy/support/data/latest_powerrankings.csv"

    # Start with GitHub
    try:
        response = requests.get(github_url, timeout=5)
        response.raise_for_status()

        csv_content = StringIO(response.text)

        from_github = pd.read_csv(
            csv_content, parse_dates=["date"], date_format="%y%m%d"
        )

        # print("Loaded rankings from GitHub.")
        return from_github
    except (requests.RequestException, pd.errors.ParserError) as e:
        print(f"GitHub fetch failed: {e}. Falling back to local file.")
    # Fallback to local file
    rk = pd.read_csv(
        find_file("latest_powerrankings"), parse_dates=["date"], date_format="%y%m%d"
    )  # 02-Dec-24
    return rk


us_central_tz = pytz.timezone("US/Central")
today = dt.datetime.now(us_central_tz).date()
# print(today)


def create_rk_pt(df: pd.DataFrame):
    """Create a pivot table for Average Ranks and NBA_Weeks."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    rk_pt = pd.pivot_table(df, index="teamname", columns="nba_week", values="ranking")
    rk_pt = rk_pt.round(2)

    # rk_pt will be input for graphs
    return rk_pt


def create_filtered_df(
    df: pd.DataFrame, start_date="2024-10-20", end_date=dt.datetime.today()
):
    """Filter the DataFrame to only include rows with specified NBA weeks."""

    start_adjust = most_recent_sunday(start_date)  # find most recent sunday
    end_adjust = end_date

    df["date"] = pd.to_datetime(df["date"])
    df = df[df["nba_week"].notna()]
    df["nba_week"] = df["nba_week"].astype(int)

    filtered_df = df[(df.date >= start_adjust) & (df.date <= end_adjust)]

    return filtered_df


def most_recent_sunday(date):
    """Find date of most recent Sunday."""
    date = pd.to_datetime(date)
    if date.weekday() == 6:
        return date
    else:
        return date - pd.to_timedelta(date.weekday() + 1, unit="D")


def create_and_merge_rank_week():

    rk = read_ranking_file()
    wk = read_nba_week()

    rk["sunday"] = rk["date"].apply(most_recent_sunday)
    rk["sunday"] = pd.to_datetime(rk["sunday"])
    wk["sunday"] = pd.to_datetime(wk["sunday"])

    df = pd.merge(rk, wk[["sunday", "nba_week"]], on="sunday", how="left")
    return df


def df_string_for_graph_2(start="2024-10-20", end=dt.datetime.today()):
    ranking_file = find_file("latest_powerrankings")
    df = create_filtered_df(create_and_merge_rank_week(), start, end)
    rk_pt = create_rk_pt(df)

    return rk_pt


df = df_string_for_graph_2()
teams = df.index

df = df.reset_index()
week_cols = [col for col in df.columns if col != "teamname"]


df_long = df.melt(id_vars="teamname", var_name="week", value_name="rank")
# df_long["change"] = df_long.groupby("teamname")["rank"].diff().abs()
df_long["change"] = -1 * df_long.groupby("teamname")["rank"].diff()  # .abs()
df_group = df_long.groupby("teamname")["change"].agg(["min", "max"])

for index, row in df_group.iterrows():
    # if row min is greater than row max, that means that the FALL is the greatest weekly change
    if abs(row["min"]) > row["max"]:
        df_group.loc[index, "max_change"] = row["min"]
    else:
        df_group.loc[index, "max_change"] = row["max"]

    # print(df_group)

# print(df_group)
df_group.drop(["min", "max"], axis=1, inplace=True)

stats = (
    df_long.groupby("teamname")["rank"].agg(["min", "max", "mean", "std"])
    .round(2)
    # .reset_index()
)

stats = stats.merge(df_group, how="left", on="teamname")

# print(stats)


def trend_to_sparkline(team):
    color = nba_teams.team_color1(team)
    trend = df[df["teamname"] == team][week_cols].values.flatten()
    fig, ax = plt.subplots(figsize=(2, 0.5))
    ax.plot(trend, color=color, linewidth=2)
    ax.fill_between(
        range(len(trend)),
        trend,
        30,
        color=color,
        alpha=0.2,  # Slightly transparent fill
    )
    ax.set_ylim(30, 1)
    ax.axis("off")

    img_bytes = BytesIO()
    plt.savefig(img_bytes, format="png", bbox_inches="tight", dpi=150, transparent=True)
    plt.close()
    return f"data:image/png;base64,{base64.b64encode(img_bytes.getvalue()).decode()}"


# stats.insert((0, 'Rank', range(1, len(stats) + 1)))

stats["trend"] = stats.index.to_series().apply(trend_to_sparkline)

# df["trend_graph"] = df
stats = stats.rename(
    columns={
        "min": "best rank",
        "max": "worst rank",
        "mean": "mean rank",
        "std": "standard dev.",
    }
)

print(stats)


st.dataframe(
    stats,
    height=700,
    # width= 900,
    column_config={
        "trend": st.column_config.ImageColumn("performance", width="small"),
        "mean": st.column_config.NumberColumn(format="%.2f"),
        "std": st.column_config.NumberColumn(format="%.2f"),
        "max_change": st.column_config.NumberColumn("max 1wk change", format="%.2f"),
    },
    use_container_width=True,
)
