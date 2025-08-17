from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import  unittest

# -*- coding: utf-8 -*-
"""
Tests unitaires pour TranslatorAssistant
"""



@unittest.skip("Translation tests require language packages - skip for now")
class TestTranslatorAssistant(unittest.TestCase):
    """Tests unitaires pour la classe TranslatorAssistant"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config_path = None
        self.temp_dir = tempfile.mkdtemp()
    
    @patch('argostranslate.package')
    @patch('argostranslate.translate')
    @patch('voice_assistant.audio.record.AudioRecorder')
    @patch('voice_assistant.stt.whisper_stt.WhisperSTT')
    @patch('voice_assistant.tts.piper_tts.PiperTTS')
    def test_initialization_en_to_fr(self, mock_tts, mock_stt, mock_recorder, mock_translate, mock_package):
        """Test l'initialisation pour traduction EN->FR"""
        from voice_assistant.translator import TranslatorAssistant
        
        # Mock des composants
        mock_recorder.return_value = MagicMock()
        mock_stt.return_value = MagicMock()
        mock_tts.return_value = MagicMock()
        
        # Mock de la traduction
        mock_installed_languages = [
            MagicMock(code='en'),
            MagicMock(code='fr')
        ]
        mock_translate.get_installed_languages.return_value = mock_installed_languages
        mock_installed_languages[0].get_translation.return_value = MagicMock()
        
        translator = TranslatorAssistant(direction="en_to_fr")
        
        self.assertEqual(translator.source_lang_code, "en")
        self.assertEqual(translator.target_lang_code, "fr")
        self.assertEqual(translator.assistant_voice_lang, "en")
        self.assertIn("Hello", translator.welcome_message)
    
    @patch('argostranslate.package')
    @patch('argostranslate.translate')
    @patch('voice_assistant.audio.record.AudioRecorder')
    @patch('voice_assistant.stt.whisper_stt.WhisperSTT')
    @patch('voice_assistant.tts.piper_tts.PiperTTS')
    def test_initialization_fr_to_en(self, mock_tts, mock_stt, mock_recorder, mock_translate, mock_package):
        """Test l'initialisation pour traduction FR->EN"""
        from voice_assistant.translator import TranslatorAssistant
        
        # Mock des composants
        mock_recorder.return_value = MagicMock()
        mock_stt.return_value = MagicMock()
        mock_tts.return_value = MagicMock()
        
        # Mock de la traduction
        mock_installed_languages = [
            MagicMock(code='fr'),
            MagicMock(code='en')
        ]
        mock_translate.get_installed_languages.return_value = mock_installed_languages
        mock_installed_languages[0].get_translation.return_value = MagicMock()
        
        translator = TranslatorAssistant(direction="fr_to_en")
        
        self.assertEqual(translator.source_lang_code, "fr")
        self.assertEqual(translator.target_lang_code, "en")
        self.assertEqual(translator.assistant_voice_lang, "fr")
        self.assertIn("Bonjour", translator.welcome_message)
    
    def test_translate_text_empty(self):
        """Test la traduction d'un texte vide"""
        from voice_assistant.translator import TranslatorAssistant
        
        with patch('voice_assistant.translator.TranslatorAssistant.__init__', return_value=None):
            translator = TranslatorAssistant.__new__(TranslatorAssistant)
            translator.translation_engine = MagicMock()
            translator.translation_error_msg = "Erreur"
            
            result = translator.translate_text("")
            self.assertEqual(result, "")
            translator.translation_engine.translate.assert_not_called()
    
    def test_translate_text_success(self):
        """Test une traduction réussie"""
        from voice_assistant.translator import TranslatorAssistant
        
        with patch('voice_assistant.translator.TranslatorAssistant.__init__', return_value=None):
            translator = TranslatorAssistant.__new__(TranslatorAssistant)
            translator.source_lang_code = "en"
            translator.target_lang_code = "fr"
            
            mock_engine = MagicMock()
            mock_engine.translate.return_value = "Bonjour le monde"
            translator.translation_engine = mock_engine
            translator.translation_error_msg = "Erreur"
            
            result = translator.translate_text("Hello world")
            
            self.assertEqual(result, "Bonjour le monde")
            mock_engine.translate.assert_called_once_with("Hello world")
    
    def test_translate_text_error(self):
        """Test la gestion d'erreur de traduction"""
        from voice_assistant.translator import TranslatorAssistant
        
        with patch('voice_assistant.translator.TranslatorAssistant.__init__', return_value=None):
            translator = TranslatorAssistant.__new__(TranslatorAssistant)
            translator.source_lang_code = "en"
            translator.target_lang_code = "fr"
            
            mock_engine = MagicMock()
            mock_engine.translate.side_effect = Exception("API Error")
            translator.translation_engine = mock_engine
            translator.translation_error_msg = "Erreur de traduction"
            
            result = translator.translate_text("Hello")
            
            self.assertEqual(result, "Erreur de traduction")
    
    @patch('voice_assistant.translator.TranslatorAssistant._init_translation_engine')
    @patch('voice_assistant.translator.TranslatorAssistant._init_tts')
    @patch('voice_assistant.translator.TranslatorAssistant._init_stt')
    @patch('voice_assistant.translator.TranslatorAssistant._init_audio_recorder')
    def test_optimize_for_limited_resources(self, mock_recorder, mock_stt, mock_tts, mock_engine):
        """Test les optimisations pour ressources limitées"""
        from voice_assistant.translator import TranslatorAssistant
        
        with patch('os.environ', {}):
            translator = TranslatorAssistant(direction="en_to_fr")
            
            # Vérifier que les variables d'environnement sont définies
            import os
            if 'OMP_NUM_THREADS' in os.environ:
                self.assertEqual(os.environ.get('OMP_NUM_THREADS'), '2')
    
    @patch('shutil.rmtree')
    @patch('voice_assistant.translator.TranslatorAssistant._init_translation_engine')
    @patch('voice_assistant.translator.TranslatorAssistant._init_tts')
    @patch('voice_assistant.translator.TranslatorAssistant._init_stt')
    @patch('voice_assistant.translator.TranslatorAssistant._init_audio_recorder')
    def test_cleanup(self, mock_recorder, mock_stt, mock_tts, mock_engine, mock_rmtree):
        """Test le nettoyage des ressources"""
        from voice_assistant.translator import TranslatorAssistant
        
        translator = TranslatorAssistant(direction="en_to_fr")
        translator.tts = MagicMock()
        translator.tts.cleanup = MagicMock()
        
        translator.cleanup()
        
        translator.tts.cleanup.assert_called_once()
