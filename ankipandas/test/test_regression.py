""" These tests are created from issues that we fixed to avoid that they might
come back later.
"""

from __future__ import annotations

import tempfile
import shutil
from pathlib import Path

# ours
from ankipandas.collection import Collection
from ankipandas.test.util import parameterized_paths
from ankipandas.raw import load_db, close_db, get_table, set_table


@parameterized_paths()
def test_inplace_merge_notes(db_path):
    """https://github.com/klieret/AnkiPandas/issues/51
    AttributeError: 'NoneType' object has no attribute 'col'
    """
    col = Collection(db_path)
    col.cards.merge_notes(inplace=True)

@parameterized_paths()
def test_primary_key_constraint_preserved(db_path):
    """https://github.com/klieret/AnkiPandas/issues/137
    
    Ensure PRIMARY KEY constraint is preserved when replacing table data.
    """
    # Create temporary copy of the database
    with tempfile.NamedTemporaryFile(suffix='.anki2', delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        shutil.copy(db_path, temp_path)
    
    db = None
    try:
        db = load_db(temp_path)
        for table_name in ['notes', 'cards']:
            table_data = get_table(db, table_name)
            set_table(db, table_data, table_name, "replace")

            cursor = db.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
            has_primary_key = any(col[1] == 'id' and col[5] == 1 for col in columns)
            
            assert has_primary_key, f"PRIMARY KEY constraint was lost on {table_name} table"
    finally:
        if db is not None:
            close_db(db)
        temp_path.unlink(missing_ok=True)
