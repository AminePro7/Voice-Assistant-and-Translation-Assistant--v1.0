from unittest.mock import MagicMock, patch, mock_open
import tempfile
import numpy as np  
import  unittest
@unittest.skip("RAG integration tests require heavy dependencies - skip for now")
class TestRAGWorkflow(unittest.TestCase):
    """Tests d'intégration du workflow RAG"""
    
    def setUp(self):
        self.test_doc_content = """
        # Documentation de test
        
        ## Problème d'imprimante
        Solution: Vérifier le câble USB et redémarrer l'imprimante.
        
        ## Problème de WiFi
        Solution: Redémarrer le routeur et vérifier le mot de passe.
        """
    
    @patch('langchain_huggingface.HuggingFaceEmbeddings')
    @patch('langchain_community.vectorstores.FAISS')
    def test_rag_retrieval(self, mock_faiss, mock_embeddings):
        """Test la récupération RAG"""
        from voice_assistant.rag.faiss_rag import FaissRAG
        
        # Configuration des mocks
        mock_embeddings_instance = MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        mock_vectorstore = MagicMock()
        mock_faiss.from_documents.return_value = mock_vectorstore
        
        # Mock du retriever
        mock_retriever = MagicMock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        
        # Mock LLM
        mock_llm = MagicMock()
        
        with patch('builtins.open', mock_open(read_data=self.test_doc_content)):
            with patch('pathlib.Path.exists', return_value=True):
                config = {
                    'embedding_model': 'test-model',
                    'vectorstore_dir': 'test_store',
                    'doc_path': 'test.md',
                    'retriever_k': 2
                }
                
                rag = FaissRAG(config, mock_llm)
                
                # Test de récupération
                mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
                    (MagicMock(page_content="Solution imprimante"), 0.9)
                ]
                
                # Simuler une requête
                response = rag.get_llm_stream_generator("problème imprimante", use_rag_initial=True)
                
                self.assertIsNotNone(response)
