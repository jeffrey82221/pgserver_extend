"""Basic usage of pg_textsearch: BM25 ranked search (PostgreSQL >= 17 only)."""


def test_bm25_search(tmp_postgres, require_extension):
    require_extension("pg_textsearch")
    out = tmp_postgres.psql("""
        CREATE EXTENSION pg_textsearch;
        CREATE TABLE documents (id int PRIMARY KEY, content text);
        INSERT INTO documents VALUES
            (1, 'PostgreSQL is a powerful database system'),
            (2, 'BM25 is an effective ranking function'),
            (3, 'Full text search with custom scoring');
        CREATE INDEX docs_idx ON documents USING bm25(content) WITH (text_config='english');
        SELECT id FROM documents ORDER BY content <@> 'database system' LIMIT 1;
    """)
    assert "CREATE INDEX" in out
    assert out.split("(1 row)")[0].split()[-1] == "1"
