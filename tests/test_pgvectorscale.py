"""Basic usage of pgvectorscale: a DiskANN index on a pgvector column."""


def test_diskann_index_search(tmp_postgres, require_extension):
    require_extension("vectorscale")
    out = tmp_postgres.psql("""
        CREATE EXTENSION vectorscale CASCADE;
        CREATE TABLE items (id int PRIMARY KEY, embedding vector(3));
        INSERT INTO items VALUES (1, '[1,0,0]'), (2, '[0,1,0]'), (3, '[0,0,1]'), (4, '[0.9,0.1,0]');
        CREATE INDEX items_idx ON items USING diskann (embedding vector_cosine_ops);
        SELECT id FROM items ORDER BY embedding <=> '[1,0,0]' LIMIT 1;
    """)
    assert "CREATE INDEX" in out
    assert out.split("(1 row)")[0].split()[-1] == "1"
