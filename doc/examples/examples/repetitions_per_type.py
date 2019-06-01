axs = col.cards.hist(column="creps", by="ctype", layout=(1, 2), figsize=(12, 3))
for ax in axs:
    ax.set_xlabel("#Reviews")
    ax.set_ylabel("Count")
