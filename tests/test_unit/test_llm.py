from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import  unittest
class TestLlamaCppLLM(unittest.TestCase):
    """Tests unitaires pour LlamaCppLLM"""
    
    def setUp(self):
        self.config = {
            'model_path': 'llm_models/test.gguf',
            'n_ctx': 512,
            'temperature': 0.1,
            'max_tokens': 256
        }
    
    @patch('langchain_community.llms.LlamaCpp')
    @patch('pathlib.Path.exists')
    def test_initialization(self, mock_exists, mock_llama):
        """Test l'initialisation du modèle LLM"""
        mock_exists.return_value = True
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = "Test"
        mock_llama.return_value = mock_llm_instance
        
        from voice_assistant.llm.llama_cpp_llm import LlamaCppLLM
        
        llm = LlamaCppLLM(self.config)
        
        self.assertEqual(llm.temperature, 0.1)
        self.assertEqual(llm.n_ctx, 512)
        mock_llama.assert_called_once()
    
    @patch('langchain_community.llms.LlamaCpp')
    @patch('pathlib.Path.exists')
    def test_invoke(self, mock_exists, mock_llama):
        """Test l'invocation du modèle"""
        mock_exists.return_value = True
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = "Réponse du modèle"
        mock_llama.return_value = mock_llm_instance
        
        from voice_assistant.llm.llama_cpp_llm import LlamaCppLLM
        
        llm = LlamaCppLLM(self.config)
        response = llm.invoke("Question de test")
        
        self.assertEqual(response, "Test")
        mock_llm_instance.invoke.assert_called_with("Question de test")
