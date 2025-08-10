import pytest
from unittest.mock import patch, MagicMock
from autobook_ai.rag import create_retriever
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.documents import Document

@patch('autobook_ai.rag.RecursiveCharacterTextSplitter')
@patch('autobook_ai.rag.TextLoader')
@patch('autobook_ai.rag.GoogleGenerativeAIEmbeddings')
def test_create_and_use_retriever(mock_embeddings, mock_loader, mock_splitter):
    """
    A focused unit test for the create_retriever function to debug mocking issues.
    """
    # --- Setup Mocks ---

    # Mock the document loading and splitting process
    mock_docs = [Document(page_content="doc1"), Document(page_content="doc2")]
    mock_loader.return_value.load.return_value = mock_docs
    mock_splitter.return_value.split_documents.return_value = mock_docs

    # Mock the embedding model
    mock_embedding_instance = MagicMock()
    mock_embedding_instance.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]
    mock_embedding_instance.embed_query.return_value = [0.1, 0.2]
    mock_embeddings.return_value = mock_embedding_instance

    # --- Test ---

    # 1. Create the retriever
    retriever = create_retriever()

    # 2. Assert that the retriever was created and is the correct type
    assert isinstance(retriever, VectorStoreRetriever)

    # 3. Use the retriever, which will trigger the underlying embedding methods
    # This is the part that was failing before.
    try:
        relevant_docs = retriever.get_relevant_documents("test query")
    except Exception as e:
        pytest.fail(f"retriever.get_relevant_documents() failed with an unexpected exception: {e}")

    # --- Assertions ---

    # Check that our mocks were called
    mock_loader.return_value.load.assert_called_once()
    mock_splitter.return_value.split_documents.assert_called_once()
    mock_embeddings.assert_called_once()
    mock_embedding_instance.embed_documents.assert_called_once()
    mock_embedding_instance.embed_query.assert_called_once_with("test query")

    # Check that the retriever returned documents
    # The mock FAISS store should return the documents we gave it.
    assert len(relevant_docs) > 0
    assert relevant_docs[0].page_content in ["doc1", "doc2"]
