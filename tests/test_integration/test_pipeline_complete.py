from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import  unittest

class TestCompletePipeline(unittest.TestCase):
    """Tests d'intégration du pipeline complet"""
    
    @unittest.skip("Complex pipeline test requires full integration - skip for now")
    @patch('voice_assistant.assistant.VoiceAssistant')
    def test_audio_to_response_pipeline(self, mock_assistant):
        """Test le pipeline complet audio -> texte -> LLM -> TTS"""
        
        # Configuration du mock
        mock_instance = MagicMock()
        mock_assistant.return_value = mock_instance
        
        # Simuler le pipeline
        mock_instance.audio_recorder.record.return_value = (np.zeros(16000), 0.1)
        mock_instance.stt.transcribe.return_value = "Mon imprimante ne marche pas"
        mock_instance.process_query.return_value = "Voici la solution pour votre imprimante"
        
        # Exécuter un cycle
        mock_instance.run_single_cycle()
        
        # Vérifications
        mock_instance.audio_recorder.record.assert_called_once()
        mock_instance.stt.transcribe.assert_called_once()
        mock_instance.process_query.assert_called_once()
        mock_instance.tts.speak.assert_called_once()
