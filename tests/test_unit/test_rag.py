from unittest.mock import MagicMock, patch, mock_open
import tempfile
import numpy as np  
import unittest


 # -*- coding: utf-8 -*-
"""
Tests unitaires pour le système RAG (FaissRAG)
"""



@unittest.skip("Tests RAG require heavy dependencies - skip for now")
class TestFaissRAG(unittest.TestCase):
    """Tests unitaires pour la classe FaissRAG"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config = {
            'embedding_model': 'paraphrase-multilingual-MiniLM-L12-v2',
            'vectorstore_dir': 'test_vectorstore',
            'chunk_size': 500,
            'chunk_overlap': 50,
            'retriever_k': 2,
            'doc_path': 'test_doc.md'
        }
        
        self.test_doc_content = """
        # Documentation Test
        ## Problème Imprimante
        Solution: Redémarrer l'imprimante
        """
        
        self.mock_llm = MagicMock()
    
    @patch('langchain_huggingface.HuggingFaceEmbeddings')
    @patch('langchain_community.vectorstores.FAISS')
    @patch('pathlib.Path.exists')
    def test_initialization(self, mock_exists, mock_faiss, mock_embeddings):
        """Test l'initialisation du système RAG"""
        mock_exists.return_value = True
        
        mock_embeddings_instance = MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        mock_vectorstore = MagicMock()
        mock_faiss.load_local.return_value = mock_vectorstore
        
        from voice_assistant.rag.faiss_rag import FaissRAG
        
        with patch('builtins.open', mock_open(read_data=self.test_doc_content)):
            rag = FaissRAG(self.config, self.mock_llm)
        
        self.assertIsNotNone(rag.embeddings)
        self.assertIsNotNone(rag.vectorstore)
        self.assertIsNotNone(rag.memory)
        mock_embeddings.assert_called_once()
    
    @patch('langchain_huggingface.HuggingFaceEmbeddings')
    @patch('langchain_community.vectorstores.FAISS')
    def test_create_vectorstore(self, mock_faiss, mock_embeddings):
        """Test la création d'un nouveau vectorstore"""
        from voice_assistant.rag.faiss_rag import FaissRAG
        
        mock_embeddings_instance = MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        
        # Simuler l'absence du vectorstore existant
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = [True, False]  # doc existe, vectorstore n'existe pas
            
            with patch('builtins.open', mock_open(read_data=self.test_doc_content)):
                rag = FaissRAG(self.config, self.mock_llm)
        
        mock_faiss.from_documents.assert_called_once()
    
    def test_load_markdown_document(self):
        """Test le chargement d'un document Markdown"""
        from voice_assistant.rag.faiss_rag import FaissRAG
        
        with patch('langchain_huggingface.HuggingFaceEmbeddings'):
            with patch('langchain_community.vectorstores.FAISS'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('builtins.open', mock_open(read_data=self.test_doc_content)):
                        rag = FaissRAG(self.config, self.mock_llm)
                        docs = rag._load_markdown_document('test.md')
        
        self.assertEqual(len(docs), 1)
        self.assertIn("Documentation Test", docs[0].page_content)
    
    def test_format_docs(self):
        """Test le formatage des documents"""
        from voice_assistant.rag.faiss_rag import FaissRAG
        from langchain_core.documents import Document
        
        with patch('langchain_huggingface.HuggingFaceEmbeddings'):
            with patch('langchain_community.vectorstores.FAISS'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('builtins.open', mock_open(read_data="")):
                        rag = FaissRAG(self.config, self.mock_llm)
        
        docs = [
            Document(page_content="Premier document"),
            Document(page_content="Deuxième document")
        ]
        
        formatted = rag._format_docs(docs)
        self.assertIn("Premier document", formatted)
        self.assertIn("Deuxième document", formatted)
        self.assertIn("---", formatted)
    
    def test_limited_size_dict(self):
        """Test le dictionnaire à taille limitée"""
        from voice_assistant.rag.faiss_rag import FaissRAG
        
        with patch('langchain_huggingface.HuggingFaceEmbeddings'):
            with patch('langchain_community.vectorstores.FAISS'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('builtins.open', mock_open(read_data="")):
                        rag = FaissRAG(self.config, self.mock_llm)
                        cache = rag._create_limited_size_dict(max_size=3)
        
        # Ajouter plus d'éléments que la taille max
        cache['key1'] = 'value1'
        cache['key2'] = 'value2'
        cache['key3'] = 'value3'
        cache['key4'] = 'value4'  # Devrait évincer key1
        
        self.assertEqual(len(cache), 3)
        self.assertNotIn('key1', cache)
        self.assertIn('key4', cache)
    
    @patch('langchain_huggingface.HuggingFaceEmbeddings')
    @patch('langchain_community.vectorstores.FAISS')
    def test_get_llm_stream_generator_with_rag(self, mock_faiss, mock_embeddings):
        """Test la génération de stream avec RAG"""
        from voice_assistant.rag.faiss_rag import FaissRAG
        
        mock_vectorstore = MagicMock()
        mock_faiss.load_local.return_value = mock_vectorstore
        
        # Simuler des documents trouvés
        mock_doc = MagicMock()
        mock_doc.page_content = "Solution pour imprimante"
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.9)
        ]
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="")):
                rag = FaissRAG(self.config, self.mock_llm)
                
                # Mock de la chaîne RAG
                mock_chain = MagicMock()
                mock_chain.stream.return_value = iter(["Voici", " la", " solution"])
                rag.rag_chain = mock_chain
                
                generator = rag.get_llm_stream_generator("problème imprimante", use_rag_initial=True)
                result = list(generator)
        
        self.assertEqual(result, ["Voici", " la", " solution"])
        mock_vectorstore.similarity_search_with_relevance_scores.assert_called_once()
    
    def test_save_to_memory(self):
        """Test la sauvegarde dans la mémoire de conversation"""
        from voice_assistant.rag.faiss_rag import FaissRAG
        
        with patch('langchain_huggingface.HuggingFaceEmbeddings'):
            with patch('langchain_community.vectorstores.FAISS'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('builtins.open', mock_open(read_data="")):
                        rag = FaissRAG(self.config, self.mock_llm)
                        
                        # Sauvegarder une interaction
                        rag.save_to_memory("Question test", "Réponse test")
                        
                        # Vérifier que la mémoire contient l'interaction
                        memory_vars = rag.memory.load_memory_variables({})
                        self.assertIsNotNone(memory_vars.get('history'))
    
    def test_cache_rag_solution(self):
        """Test la mise en cache des solutions RAG"""
        from voice_assistant.rag.faiss_rag import FaissRAG
        
        with patch('langchain_huggingface.HuggingFaceEmbeddings'):
            with patch('langchain_community.vectorstores.FAISS'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('builtins.open', mock_open(read_data="")):
                        rag = FaissRAG(self.config, self.mock_llm)
                        
                        # Mettre en cache une solution
                        rag.cache_rag_solution("imprimante_generic_problem", "Redémarrer l'imprimante")
                        
                        # Récupérer la solution
                        cached = rag.get_cached_rag_solution("imprimante_generic_problem")
                        self.assertEqual(cached, "Redémarrer l'imprimante")
                        
                        # Vérifier qu'une clé non existante retourne None
                        self.assertIsNone(rag.get_cached_rag_solution("inexistant"))
