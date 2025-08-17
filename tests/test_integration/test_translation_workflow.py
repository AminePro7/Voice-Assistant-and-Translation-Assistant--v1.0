from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import  unittest

# -*- coding: utf-8 -*-
"""
Tests d'intégration pour le workflow de traduction complet
"""

import unittest
import numpy as np 
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path
import time


class TestTranslationWorkflow(unittest.TestCase):
    """Tests d'intégration du workflow de traduction"""
    
    def setUp(self):
        """Configuration des tests"""
        self.test_config = {
            'general': {
                'device_type': 'cpu',
                'temp_dir': tempfile.mkdtemp()
            },
            'audio': {
                'format': 'paInt16',
                'channels': 1,
                'rate': 16000,
                'chunk': 2048
            },
            'stt': {
                'model_size': 'tiny',
                'language': 'en'
            },
            'tts': {
                'piper_exe': 'piper/piper.exe',
                'model': 'models/en_US-amy-medium.onnx'
            }
        }
    
    @patch('argostranslate.translate')
    @patch('argostranslate.package')
    @patch('voice_assistant.stt.whisper_stt.WhisperSTT')
    @patch('voice_assistant.tts.piper_tts.PiperTTS')
    @patch('voice_assistant.audio.record.AudioRecorder')
    def test_complete_translation_pipeline_en_to_fr(self, mock_recorder, mock_tts, mock_stt, mock_package, mock_translate):
        """Test du pipeline complet de traduction EN->FR"""
        from voice_assistant.translator import TranslatorAssistant
        
        # Configuration des mocks
        mock_recorder_instance = MagicMock()
        mock_recorder.return_value = mock_recorder_instance
        mock_recorder_instance.record.return_value = (np.zeros(16000), 0.1)
        
        mock_stt_instance = MagicMock()
        mock_stt.return_value = mock_stt_instance
        mock_stt_instance.transcribe_audio_data.return_value = "Hello, how are you?"
        
        mock_tts_instance = MagicMock()
        mock_tts.return_value = mock_tts_instance
        
        # Mock de la traduction
        mock_translation = MagicMock()
        mock_translation.translate.return_value = "Bonjour, comment allez-vous ?"
        
        # Mesure de latence
        start_time = time.perf_counter()
        
        with patch.object(TranslatorAssistant, '_init_translation_engine'):
            translator = TranslatorAssistant(direction="en_to_fr", config_path=None)
            translator.translation_engine = mock_translation
            
            # Simuler un cycle de traduction
            audio_data, rms = mock_recorder_instance.record()
            text = mock_stt_instance.transcribe_audio_data(audio_data)
            translated = translator.translate_text(text)
            
        latency = (time.perf_counter() - start_time) * 1000
        
        # Vérifications
        self.assertEqual(translated, "Bonjour, comment allez-vous ?")
        self.assertLess(latency, 2000)  # Moins de 2 secondes
        mock_stt_instance.transcribe_audio_data.assert_called_once()
        mock_translation.translate.assert_called_once_with("Hello, how are you?")
    
    @patch('argostranslate.translate')
    def test_translation_with_empty_input(self, mock_translate):
        """Test de la traduction avec une entrée vide"""
        from voice_assistant.translator import TranslatorAssistant
        
        with patch.object(TranslatorAssistant, '_init_translation_engine'):
            translator = TranslatorAssistant(direction="fr_to_en")
            translator.translation_engine = MagicMock()
            
            result = translator.translate_text("")
            
            self.assertEqual(result, "")
            translator.translation_engine.translate.assert_not_called()
    
    @patch('argostranslate.translate')
    def test_translation_error_handling(self, mock_translate):
        """Test de la gestion d'erreur dans la traduction"""
        from voice_assistant.translator import TranslatorAssistant
        
        mock_engine = MagicMock()
        mock_engine.translate.side_effect = Exception("Translation API error")
        
        with patch.object(TranslatorAssistant, '_init_translation_engine'):
            translator = TranslatorAssistant(direction="en_to_fr")
            translator.translation_engine = mock_engine
            translator.translation_error_msg = "Erreur de traduction"
            
            result = translator.translate_text("Test text")
            
            self.assertEqual(result, "Erreur de traduction")
    
    @patch('voice_assistant.audio.record.AudioRecorder')
    @patch('voice_assistant.stt.whisper_stt.WhisperSTT')
    @patch('voice_assistant.tts.piper_tts.PiperTTS')
    def test_language_switching(self, mock_tts, mock_stt, mock_recorder):
        """Test du changement de langue pour STT et TTS"""
        from voice_assistant.translator import TranslatorAssistant
        
        # Test EN->FR
        with patch.object(TranslatorAssistant, '_init_translation_engine'):
            translator_en_fr = TranslatorAssistant(direction="en_to_fr")
            self.assertEqual(translator_en_fr.source_lang_code, "en")
            self.assertEqual(translator_en_fr.target_lang_code, "fr")
            self.assertEqual(translator_en_fr.assistant_voice_lang, "en")
        
        # Test FR->EN
        with patch.object(TranslatorAssistant, '_init_translation_engine'):
            translator_fr_en = TranslatorAssistant(direction="fr_to_en")
            self.assertEqual(translator_fr_en.source_lang_code, "fr")
            self.assertEqual(translator_fr_en.target_lang_code, "en")
            self.assertEqual(translator_fr_en.assistant_voice_lang, "fr")
    
    def test_batch_translation_performance(self):
        """Test de performance pour traductions multiples"""
        from voice_assistant.translator import TranslatorAssistant
        
        test_phrases = [
            "Hello world",
            "How are you today?",
            "The weather is nice",
            "I love programming",
            "This is a test"
        ]
        
        mock_engine = MagicMock()
        mock_engine.translate.side_effect = [
            "Bonjour le monde",
            "Comment allez-vous aujourd'hui ?",
            "Il fait beau",
            "J'aime programmer",
            "Ceci est un test"
        ]
        
        with patch.object(TranslatorAssistant, '_init_translation_engine'):
            translator = TranslatorAssistant(direction="en_to_fr")
            translator.translation_engine = mock_engine
            
            start_time = time.perf_counter()
            results = [translator.translate_text(phrase) for phrase in test_phrases]
            total_time = (time.perf_counter() - start_time) * 1000
            
            # Vérifications
            self.assertEqual(len(results), 5)
            self.assertLess(total_time / len(test_phrases), 500)  # Moins de 500ms par phrase
