"""Deduplicate developer activity events using Polars."""

import polars as pl


def deduplicate_events(
    df: pl.DataFrame,
) -> tuple[pl.DataFrame, int]:
    """Remove duplicate event IDs while preserving the first occurrence.

    Returns:
        A tuple containing the deduplicated DataFrame and the number
        of removed rows.
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame.")

    if "event_id" not in df.columns:
        raise ValueError("Missing required column: event_id")

    original_count = df.height

    cleaned_df = df.unique(
        subset=["event_id"],
        keep="first",
        maintain_order=True,
    )

    removed_count = original_count - cleaned_df.height

    return cleaned_df, removed_count
