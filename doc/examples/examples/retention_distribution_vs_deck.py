import matplotlib.pyplot as plt
import numpy as np

ax = plt.gca()
for deck in col.cards.cdeck.unique():
    selected = col.cards[col.cards.cdeck == deck]["civl"]
    if len(selected) < 1000:
        continue
    selected.plot.hist(
        ax=ax,
        label=deck,
        histtype="step",
        linewidth=2,
        xlim=(0, 365),
        bins=np.linspace(0, 365, 10),
    )
ax.set_xlabel("Predicted retention length (review interval)")
ax.set_ylabel("Number of cards")
ax.set_title("Expected retention length per deck [days]")
ax.legend(frameon=False)
