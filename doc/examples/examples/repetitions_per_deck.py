interesting_decks = list(col.cards.cdeck.unique())
interesting_decks.remove("archived::physics")
selected = col.cards[col.cards.cdeck.isin(interesting_decks)]
axss = selected.hist(
    column="creps",
    by="cdeck",
    sharex=True,
    layout=(5, 4),
    figsize=(15, 15),
    density=True,
)
for axs in axss:
    for ax in axs:
        ax.set_xlabel("#Reviews")
        ax.set_ylabel("Count")
