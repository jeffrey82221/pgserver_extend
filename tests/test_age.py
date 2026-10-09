"""Basic usage of the Apache AGE graph extension."""


def test_age_graph(tmp_postgres, require_extension):
    require_extension("age")
    out = tmp_postgres.psql("""
        CREATE EXTENSION age;
        LOAD 'age';
        SET search_path = ag_catalog, "$user", public;
        SELECT create_graph('social');
        SELECT * FROM cypher('social', $$
            CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})
        $$) AS (v agtype);
        SELECT * FROM cypher('social', $$
            MATCH (a:Person)-[:KNOWS]->(b:Person) RETURN a.name, b.name
        $$) AS (a agtype, b agtype);
    """)
    assert "CREATE EXTENSION" in out
    assert '"Alice"' in out and '"Bob"' in out
