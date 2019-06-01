cards = col.cards.merge_notes()
counts = cards[cards.has_tag("leech")]["cdeck"].value_counts()
counts.plot.pie(title="Leeches per deck")
