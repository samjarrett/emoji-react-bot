from datetime import date, time
import ssl
from typing import Optional
import re

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from slack_sdk import WebClient

ssl._create_default_https_context = ssl._create_unverified_context


def get_vaccination_data(
    states: list = ["vic"], include_aus: bool = True
) -> pd.DataFrame:
    """Get vaccination data"""
    if include_aus:
        states.append("aus")

    data_frame: pd.DataFrame = pd.DataFrame()
    for state in states:
        vaccinations = pd.read_html(
            f"https://covidlive.com.au/report/daily-vaccinations/{state}",
            attrs={"class": "DAILY-VACCINATIONS"},
            index_col="DATE",
        )[0]

        vaccinations.at["15 Feb 21", "NET"] = 0
        vaccinations.index = pd.to_datetime(vaccinations.index, format="%d %b %y")

        if data_frame.empty:
            data_frame = vaccinations.sort_index()
            del data_frame["VAR"]
            del data_frame["NET"]
            del data_frame["DOSES"]

        data_frame[state.upper()] = pd.to_numeric(vaccinations["NET"])
        # data_frame[f"{state.upper()} Total"] = vaccinations["DOSES"]

    data_frame.index = data_frame.index.to_period()

    return data_frame


def plot_cumulative_doses(vaccination_data: pd.DataFrame):
    """Plot the cumulative vaccination dose info"""
    cumsum = vaccination_data.cumsum()
    ax = cumsum.plot(
        figsize=(15, 5),
        title="Cumulative vaccinations over time",
        xlabel="Date",
        ylabel="Total Vaccinated (million)",
    )
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    # Add annotation of the final number
    for key in vaccination_data.keys():
        plt.annotate(
            "{:,}".format(cumsum[key].max()),
            xy=(1, cumsum[key].max()),
            xytext=(8, 0),
            xycoords=("axes fraction", "data"),
            textcoords="offset points",
        )

    ax.figure.set_facecolor("white")

    plt.tight_layout()
    # ax.figure.savefig("vaccinations_over_time.svg")
    ax.figure.savefig("vaccinations_over_time.png")

    return (
        "vaccinations_over_time.png",
        vaccination_data.last_valid_index(),
        {
            key: value[vaccination_data.last_valid_index()]
            for key, value in vaccination_data.items()
        },
    )


def plot_daily_doses(vaccination_data: pd.DataFrame, rolling_states: list = ["VIC"]):
    """Plot the daily doses and trend line"""
    include_keys = vaccination_data.keys()
    for key in rolling_states:
        vaccination_data[f"{key} 7-day"] = (
            vaccination_data[key].rolling(7).mean().round()
        )
        vaccination_data[f"{key} 3-day"] = (
            vaccination_data[key].rolling(3).mean().round()
        )

    thirty_day_vax = vaccination_data[vaccination_data.last_valid_index() - 30 :]

    # include_aus = "AUS" in vaccination_data
    # if include_aus:
    #     for key in include_keys:
    #         if key != "AUS":
    #             vaccination_data["AUS"] = vaccination_data["AUS"].subtract(
    #                 vaccination_data[key]
    #             )

    ax = thirty_day_vax[include_keys].plot(
        kind="area",
        stacked=False,
        figsize=(15, 5),
        title="Vaccinations per day",
        xlabel="Date",
        ylabel="Number Vaccinated",
    )

    for key in rolling_states:
        for period in ["3", "7"]:
            thirty_day_vax[f"{key} {period}-day"].plot.line(ax=ax, marker="o")
            final_val = int(
                thirty_day_vax[f"{key} {period}-day"][thirty_day_vax.last_valid_index()]
            )
            plt.annotate(
                "{:,}".format(final_val),
                xy=(1, final_val),
                xytext=(8, 0),
                xycoords=("axes fraction", "data"),
                textcoords="offset points",
            )

    ax.figure.set_facecolor("white")
    ax.legend()

    plt.tight_layout()
    # ax.figure.savefig("vaccinations_per_day.svg")
    ax.figure.savefig("vaccinations_per_day.png")

    return (
        "vaccinations_per_day.png",
        thirty_day_vax.last_valid_index(),
        {
            key: thirty_day_vax[key][thirty_day_vax.last_valid_index()]
            for key in include_keys
        },
    )


def on_app_mention(
    web_client: WebClient,
    text: str,
    channel: str,
    thread_ts: Optional[str],
    ts: str,
):
    """Trigger event when the app is mentioned"""
    match = re.search(r"(all|daily|total) (vax|vaccination) numbers", text)
    if not match:
        return

    vaccination_data = get_vaccination_data(["vic"])

    post_type = match[1]
    timestamp = ts if "thread" in text else thread_ts
    if post_type in ("daily", "all"):
        (filename, period, last_figure) = plot_daily_doses(
            vaccination_data.sort_index()
        )
        message = (
            f"Vaccination data for {period.to_timestamp().strftime('%A, %B %-d, %Y')}: \n"
            + "\n".join([f" - {key}: {value:,}" for key, value in last_figure.items()])
        )
        web_client.files_upload(
            channels=channel,
            thread_ts=timestamp,
            file=filename,
            initial_comment=message,
        )

    if post_type in ("total", "all"):
        (filename, period, last_figure) = plot_cumulative_doses(
            vaccination_data.sort_index()
        )
        message = (
            f"Total Vaccinations as of {period.to_timestamp().strftime('%A, %B %-d, %Y')}: \n"
            + "\n".join([f" - {key}: {value:,}" for key, value in last_figure.items()])
        )
        web_client.files_upload(
            channels=channel,
            thread_ts=timestamp,
            file=filename,
            initial_comment=message,
        )
