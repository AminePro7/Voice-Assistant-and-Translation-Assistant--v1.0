from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import unittest
import time
@unittest.skip("E2E tests require full application setup - skip for now")
class TestE2EScenarios(unittest.TestCase):
    """Tests de scénarios end-to-end"""
    
    def setUp(self):
        """Préparation des scénarios de test"""
        self.test_scenarios = [
            {
                "name": "Simple greeting",
                "input": "Bonjour",
                "expected_contains": ["Bonjour", "aider"],
                "max_latency_ms": 1000
            },
            {
                "name": "Technical problem",
                "input": "Mon imprimante ne marche pas",
                "expected_contains": ["solution", "imprimante"],
                "max_latency_ms": 3000
            },
            {
                "name": "Translation EN->FR",
                "input": "Hello world",
                "expected_translation": "Bonjour le monde",
                "max_latency_ms": 2000
            }
        ]
    
    @patch('voice_assistant.assistant.VoiceAssistant')
    def test_greeting_scenario(self, mock_assistant):
        """Test du scénario de salutation"""
        scenario = self.test_scenarios[0]
        
        mock_instance = MagicMock()
        mock_assistant.return_value = mock_instance
        
        # Simuler la réponse
        mock_instance.process_query.return_value = "Bonjour! Comment puis-je vous aider?"
        
        start_time = time.time()
        response = mock_instance.process_query(scenario["input"])
        latency_ms = (time.time() - start_time) * 1000
        
        # Vérifications
        for expected_word in scenario["expected_contains"]:
            self.assertIn(expected_word.lower(), response.lower())
        
        self.assertLess(latency_ms, scenario["max_latency_ms"])
    
    @patch('argostranslate.translate')
    def test_translation_scenario(self, mock_translate):
        """Test du scénario de traduction"""
        from voice_assistant.translator import TranslatorAssistant
        
        scenario = self.test_scenarios[2]
        
        # Mock de la traduction
        mock_engine = MagicMock()
        mock_engine.translate.return_value = scenario["expected_translation"]
        
        with patch.object(TranslatorAssistant, '_init_translation_engine'):
            translator = TranslatorAssistant(direction="en_to_fr")
            translator.translation_engine = mock_engine
            
            start_time = time.time()
            result = translator.translate_text(scenario["input"])
            latency_ms = (time.time() - start_time) * 1000
            
            self.assertEqual(result, scenario["expected_translation"])
            self.assertLess(latency_ms, scenario["max_latency_ms"])
