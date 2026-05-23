import os
import time
from typing import List
import logging
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph
from langchain_community.document_loaders import ConfluenceLoader
from langchain_text_splitters import TokenTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jVector
from langchain_neo4j.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel


# Embedding Model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class RequirementGraphEngine:
    """RAG Engine for querying Confluence-based requirement data."""
    
    def __init__(self, rebuild: bool = False):
        """Initialize the RAG engine.
        
        Args:
            rebuild: If True, rebuild the knowledge graph from Confluence.
        """
        self.kg = None
        self.llm = None
        self.embeddings = None
        self.vector_index = None
        self._initialize(rebuild)
    
    def _initialize(self, rebuild: bool = False):
        """Initialize and setup all engine components."""
        load_dotenv(override=True)
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        
        # Connect to Neo4j (refresh_schema=False avoids the APOC dependency)
        self.kg = Neo4jGraph(
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD"),
            database=os.getenv("NEO4J_DATABASE"),
            refresh_schema=False,
        )
        logging.getLogger("neo4j").setLevel(logging.ERROR)
        logging.getLogger("neo4j.bolt").setLevel(logging.ERROR)
        logging.getLogger("neo4j.driver").setLevel(logging.ERROR)
        logging.getLogger("neo4j.graph").setLevel(logging.ERROR)
        # Build graph if requested
        if rebuild:
            self._build_graph_from_confluence()
        
        # Create vector index
        try:
            self.vector_index = Neo4jVector.from_existing_graph(
                embedding=self.embeddings,
                url=os.getenv("NEO4J_URI"),
                username=os.getenv("NEO4J_USERNAME"),
                password=os.getenv("NEO4J_PASSWORD"),
                database=os.getenv("NEO4J_DATABASE"),
                search_type="hybrid",
                node_label="Document",
                text_node_properties=["text"],
                embedding_node_property="embedding",
            )
        except Exception as e:
            self.vector_index = Neo4jVector(
                embedding=self.embeddings,
                url=os.getenv("NEO4J_URI"),
                username=os.getenv("NEO4J_USERNAME"),
                password=os.getenv("NEO4J_PASSWORD"),
                database=os.getenv("NEO4J_DATABASE"),
                index_name="document_embeddings",
                node_label="Document",
                text_node_property="text",
                embedding_node_property="embedding",
            )
        
        # Setup fulltext indexes
        self._setup_fulltext_indexes()
    
    def _build_graph_from_confluence(self):
        """Build knowledge graph from Confluence pages."""
        self.kg.query("MATCH (n) DETACH DELETE n")
        # add_graph_documents internally calls refresh_schema() which requires APOC.
        # We don't need schema introspection for ingestion, so patch it to a no-op.
        self.kg.refresh_schema = lambda: None
        
        confluence_loader = ConfluenceLoader(
            url=os.getenv("CONFLUENCE_URL", "https://upalyk.atlassian.net/wiki"),
            username=os.getenv("CONFLUENCE_USERNAME"),
            api_key=os.getenv("CONFLUENCE_API_TOKEN"),
            space_key=os.getenv("CONFLUENCE_SPACE_KEY"),
            page_ids=[
                os.getenv("CONFLUENCE_PAGE_ID_1"),
                os.getenv("CONFLUENCE_PAGE_ID_2"),
                os.getenv("CONFLUENCE_PAGE_ID_3"),
                os.getenv("CONFLUENCE_PAGE_ID_4"),
                os.getenv("CONFLUENCE_PAGE_ID_5"),
                os.getenv("CONFLUENCE_PAGE_ID_6"),
            ],
            include_attachments=False,
        )
        
        raw_documents = confluence_loader.load()
        text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
        documents = text_splitter.split_documents(raw_documents)
        
        llm_transformer = LLMGraphTransformer(llm=self.llm)
        graph_documents = llm_transformer.convert_to_graph_documents(documents)
        
        self.kg.add_graph_documents(
            graph_documents,
            include_source=True,
            baseEntityLabel=True,
        )
    
    def _setup_fulltext_indexes(self):
        """Setup fulltext indexes for entity search."""
        entity_count = self.kg.query("MATCH (e:__Entity__) RETURN count(e) as count")[0]['count']
        
        if entity_count > 0:
            try:
                self.kg.query("DROP INDEX entity IF EXISTS")
            except:
                pass
            
            self.kg.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
            
            for i in range(30):
                result = self.kg.query("SHOW FULLTEXT INDEXES WHERE name = 'entity'")
                if result and result[0].get('state') == 'ONLINE':
                    break
                time.sleep(1)
        
        self.kg.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
    
    def _extract_entities_simple(self, question: str) -> List[str]:
        """Extract business-domain entities from text using LLM."""
        try:
            response = self.llm.invoke(
                f"Extract all business-domain entities from this text. Focus on: "
                f"workflow names, process names, system components, business objects, "
                f"statuses, roles, and domain-specific concepts. "
                f"Ignore generic task words like 'generate', 'test cases', 'workflow', 'process'. "
                f"Return ONLY the entity names as a comma-separated list, nothing else.\n\n"
                f"Text: {question}"
            )
            entities = [e.strip() for e in response.content.split(',') if e.strip()]
            return entities[:10]
        except Exception as e:
            return []
    
    def _generate_full_text_query(self, input: str) -> str:
        """Generate a full-text search query with fuzzy matching."""
        full_text_query = ""
        words = [el for el in remove_lucene_chars(input).split() if el]
        if not words:
            return ""
        for word in words[:-1]:
            full_text_query += f" {word}~2 AND"
        full_text_query += f" {words[-1]}~2"
        return full_text_query.strip()
    
    def _structured_retriever(self, question: str) -> str:
        """Retrieve graph context via entity search and relationship traversal."""
        result = ""
        entities = self._extract_entities_simple(question)

        if not entities:
            return result

        for entity in entities:
            query = self._generate_full_text_query(entity)
            if not query:
                continue

            try:
                response = self.kg.query(
                    """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
                    YIELD node, score
                    CALL (node) {
                        MATCH (node)-[r:!MENTIONS]->(neighbor)
                        RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
                        UNION ALL
                        MATCH (node)<-[r:!MENTIONS]-(neighbor)
                        RETURN neighbor.id + ' - ' + type(r) + ' -> ' + node.id AS output
                    }
                    RETURN output LIMIT 50
                    """,
                    {"query": query},
                )
                relationships = [el["output"] for el in response if el.get("output")]
                result += "\n".join(relationships)
            except Exception as e:
                print(f"  Graph search error: {e}")

        return result
    
    def _retriever(self, question: str) -> str:
        """Hybrid retriever combining graph traversal and vector similarity."""
        # Graph search
        structured_data = self._structured_retriever(question)

        # Vector search — k=8 to capture broader page coverage
        try:
            unstructured_results = self.vector_index.similarity_search(question, k=8)
            unstructured_data = [doc.page_content for doc in unstructured_results]
        except Exception as e:
            unstructured_data = []

        # Combine
        final_data = f"""=== Structured Graph Data ===
{structured_data if structured_data else "No structured data found"}

=== Unstructured Vector Data ===
{"#Document ".join(unstructured_data) if unstructured_data else "No unstructured data found"}
"""

        return final_data
    
    def retrieve_raw_context(self, question: str) -> str:
        """Return raw hybrid retrieval results without any LLM synthesis.

        This is the right call for pipeline Node 1 — it passes factual knowledge-base
        content (graph relationships + document chunks) to downstream agents unchanged,
        so no information is lost or pre-interpreted by a generation step.
        """
        return self._retriever(question)

    def ask_question(self, question: str) -> str:
        """Ask a question and return the answer.
        
        Args:
            question: The question to ask
            
        Returns:
            str: The answer from the RAG pipeline
        """
        rag_template = """Answer the question based only on the following context:

{context}

Question: {question}

Instructions:
- Use natural language and be concise
- If the context doesn't contain relevant information, say so
- Cite specific facts from the context when possible

Answer:"""

        rag_prompt = ChatPromptTemplate.from_template(rag_template)

        rag_chain = (
            RunnableParallel(
                {
                    "context": self._retriever,
                    "question": RunnablePassthrough(),
                }
            )
            | rag_prompt
            | self.llm
            | StrOutputParser()
        )

        try:
            response = rag_chain.invoke(question)
            return response
        except Exception as e:
            return f"Error: {e}"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RequirementGraphEngine CLI")
    parser.add_argument("--rebuild", action="store_true", help="Wipe and rebuild the Neo4j graph from Confluence")
    args = parser.parse_args()

    if args.rebuild:
        print("Rebuilding GraphRAG from Confluence — this will wipe and re-ingest all data...")
        engine = RequirementGraphEngine(rebuild=True)
        print("Rebuild complete. Neo4j graph is ready.")
    else:
        engine = RequirementGraphEngine(rebuild=False)
        answer = engine.ask_question("Give me the list of Error Codes?")
        print(answer)








