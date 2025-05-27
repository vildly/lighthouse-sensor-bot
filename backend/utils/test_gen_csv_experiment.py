import pandas as pd
from langchain_community.document_loaders import DirectoryLoader
import os
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from ragas.testset import TestsetGenerator
from ragas.testset.graph import KnowledgeGraph, Node, NodeType
from ragas.testset.transforms import default_transforms, apply_transforms
from langchain.docstore.document import Document
import json

# Load CSV data
df = pd.read_csv("data/ferry_trips_data.csv")

# Load semantic model
with open("data/semantic_model.json", "r") as f:
    semantic_model = json.load(f)

# Create LangChain documents
docs = []
for index, row in df.iterrows():
    content = ", ".join([f"{col}: {val}" for col, val in row.items()])
    metadata = {"row_index": index, "route_id": row["route_id"], "ferry_name": row["ferry_name"]}
    docs.append(Document(page_content=content, metadata=metadata))

# Prepare LLM and embeddings
generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4"))
generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

# Create and populate knowledge graph
kg = KnowledgeGraph()
for doc in docs:
    kg.nodes.append(
        Node(
            type=NodeType.DOCUMENT,
            properties={"page_content": doc.page_content, "document_metadata": doc.metadata}
        )
    )

# Apply transformations to enrich the knowledge graph
trans = default_transforms(documents=docs, llm=generator_llm, embedding_model=generator_embeddings)
apply_transforms(kg, trans)

# Save the knowledge graph
kg.save("data/ragas/knowledge_graph.json")

# Load the knowledge graph
loaded_kg = KnowledgeGraph.load("data/ragas/knowledge_graph.json")

# Generate Testset with knowledge graph
generator = TestsetGenerator(
    llm=generator_llm,
    embedding_model=generator_embeddings,
    knowledge_graph=loaded_kg
)
dataset = generator.generate_with_langchain_docs(docs, testset_size=3)
test_pd = dataset.to_pandas()
test_pd.to_csv("data/ragas/testset_synthetic.csv")