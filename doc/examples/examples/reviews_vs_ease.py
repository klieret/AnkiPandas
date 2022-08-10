from __future__ import annotations

import pandas as pd

xs = []
ys = []
decks = []
for deck in col.cards.cdeck.unique():
    selected = col.cards[col.cards["cdeck"] == deck]
    if len(selected) < 500:
        continue
    decks.append(deck)
    binned = pd.qcut(selected["creps"], 15, duplicates="drop")
    results = selected.groupby(binned)["civl"].mean()
    y = results.tolist()
    x = results.index.map(lambda x: x.mid).tolist()
    xs.append(x)
    ys.append(y)

ax = plt.gca()
for i in range(len(xs)):
    ax.plot(xs[i], ys[i], "o-", label=decks[i])
ax.set_xlabel("#Reviews")
ax.set_ylabel("Expected retention length/review interval [days]")
ax.set_title("Number of reviews vs retention length")
ax.legend(frameon=False)
