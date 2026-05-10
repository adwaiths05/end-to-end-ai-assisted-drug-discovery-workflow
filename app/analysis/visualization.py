from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_prediction_distribution(frame: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4))
    frame["predicted_pic50"].plot(kind="hist", bins=20, ax=ax)
    ax.set_xlabel("Predicted pIC50")
    ax.set_ylabel("Count")
    return fig

