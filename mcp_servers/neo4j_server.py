"""Neo4j MCP Server — exposes graph database tools for Claude Code."""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load .env from project root (one level up from mcp_servers/)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

mcp = FastMCP("neo4j")


def _get_driver():
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    return GraphDatabase.driver(uri, auth=(username, password))


def _run_query(cypher: str, params: Optional[dict] = None) -> list:
    driver = _get_driver()
    db = os.getenv("NEO4J_DATABASE", "neo4j")
    with driver.session(database=db) as session:
        result = session.run(cypher, params or {})
        return [dict(record) for record in result]
    driver.close()


@mcp.tool()
def run_cypher(query: str, params: str = "{}") -> str:
    """Run an arbitrary Cypher query against the Neo4j graph database.

    Args:
        query: Cypher query string.
        params: JSON string of query parameters, e.g. '{"name": "Trade"}'. Defaults to '{}'.

    Returns:
        JSON-formatted list of result records.
    """
    try:
        param_dict = json.loads(params)
        rows = _run_query(query, param_dict)
        return json.dumps(rows, indent=2, default=str)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_schema() -> str:
    """Return the Neo4j graph schema: node labels, relationship types, and property keys.

    Returns:
        Human-readable schema summary.
    """
    try:
        labels = _run_query("CALL db.labels() YIELD label RETURN label ORDER BY label")
        rel_types = _run_query("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
        prop_keys = _run_query("CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey ORDER BY propertyKey")

        label_list = [r["label"] for r in labels]
        rel_list = [r["relationshipType"] for r in rel_types]
        prop_list = [r["propertyKey"] for r in prop_keys]

        return (
            f"Node Labels ({len(label_list)}):\n  " + "\n  ".join(label_list) +
            f"\n\nRelationship Types ({len(rel_list)}):\n  " + "\n  ".join(rel_list) +
            f"\n\nProperty Keys ({len(prop_list)}):\n  " + "\n  ".join(prop_list)
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_use_case_graph(use_case_name: str) -> str:
    """Retrieve the full subgraph for a specific use case or business process.

    Traverses entity relationships to surface requirements, workflows, statuses, and
    error codes connected to the named use case.

    Args:
        use_case_name: Name of the use case or process (e.g. "Trade Amendment").

    Returns:
        JSON list of relationship triples: source → relationship → target.
    """
    try:
        cypher = """
        CALL db.index.fulltext.queryNodes('entity', $query, {limit: 5})
        YIELD node, score
        CALL (node) {
            MATCH (node)-[r]->(neighbor)
            RETURN node.id AS source, type(r) AS rel, neighbor.id AS target
            UNION ALL
            MATCH (node)<-[r]-(neighbor)
            RETURN neighbor.id AS source, type(r) AS rel, node.id AS target
        }
        RETURN source, rel, target LIMIT 100
        """
        words = use_case_name.replace("-", " ").split()
        query = " AND ".join(f"{w}~2" for w in words if w)
        rows = _run_query(cypher, {"query": query})
        if not rows:
            return f"No graph data found for use case: '{use_case_name}'"
        return json.dumps(rows, indent=2)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def list_all_use_cases() -> str:
    """List all use cases and business entities stored in the knowledge graph.

    Returns:
        Newline-separated list of entity IDs found in the graph.
    """
    try:
        rows = _run_query(
            "MATCH (e:__Entity__) RETURN DISTINCT e.id AS id ORDER BY id LIMIT 200"
        )
        if not rows:
            return "No entities found. The graph may be empty — run RequirementGraphEngine with rebuild=True."
        return "\n".join(r["id"] for r in rows if r.get("id"))
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_error_codes() -> str:
    """Retrieve all error codes and their descriptions from the knowledge graph.

    Returns:
        JSON list of error code nodes with their properties.
    """
    try:
        rows = _run_query(
            """
            MATCH (e:__Entity__)
            WHERE e.id =~ '(?i).*(error|ERR|code|exception|invalid|fail).*'
            RETURN e.id AS id, e.description AS description, labels(e) AS labels
            ORDER BY e.id
            LIMIT 100
            """
        )
        if not rows:
            # Fallback: look for Document nodes with error content
            rows = _run_query(
                """
                MATCH (d:Document)
                WHERE d.text =~ '(?i).*(error code|ERR-|exception).*'
                RETURN d.text AS text LIMIT 20
                """
            )
            if not rows:
                return "No error code entities found. Try run_cypher with a custom query."
        return json.dumps(rows, indent=2, default=str)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def debug_rag_retrieval(question: str) -> str:
    """Debug the RAG retrieval pipeline for a given question.

    Shows what graph relationships and document chunks would be retrieved
    by RequirementGraphEngine for this question, without invoking the LLM.

    Args:
        question: The question to debug retrieval for (e.g. "Trade Amendment validation rules").

    Returns:
        Combined structured graph data and top vector search hits.
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_neo4j import Neo4jVector
        from langchain_neo4j.vectorstores.neo4j_vector import remove_lucene_chars

        # Graph retrieval
        words = [w for w in remove_lucene_chars(question).split() if w]
        graph_results = []
        for word in words[:5]:
            cypher = """
            CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
            YIELD node, score
            CALL (node) {
                MATCH (node)-[r:!MENTIONS]->(neighbor)
                RETURN node.id + ' -[' + type(r) + ']-> ' + neighbor.id AS rel
                UNION ALL
                MATCH (node)<-[r:!MENTIONS]-(neighbor)
                RETURN neighbor.id + ' -[' + type(r) + ']-> ' + node.id AS rel
            }
            RETURN rel LIMIT 20
            """
            query = f"{word}~2"
            try:
                rows = _run_query(cypher, {"query": query})
                graph_results.extend(r["rel"] for r in rows if r.get("rel"))
            except Exception:
                pass

        # Vector retrieval
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        vector_store = Neo4jVector.from_existing_graph(
            embedding=embeddings,
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD"),
            database=os.getenv("NEO4J_DATABASE"),
            search_type="hybrid",
            node_label="Document",
            text_node_properties=["text"],
            embedding_node_property="embedding",
        )
        docs = vector_store.similarity_search(question, k=5)
        vector_snippets = [d.page_content[:300] for d in docs]

        return (
            "=== Graph Relationships ===\n" +
            ("\n".join(graph_results) if graph_results else "None found") +
            "\n\n=== Top Vector Chunks ===\n" +
            ("\n---\n".join(vector_snippets) if vector_snippets else "None found")
        )
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
