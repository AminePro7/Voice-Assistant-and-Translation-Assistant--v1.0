from unittest.mock import MagicMock, patch, mock_open
import tempfile
import numpy as np  
import  unittest

# -*- coding: utf-8 -*-
"""
Tests unitaires pour les utilitaires
"""



class TestNormalization(unittest.TestCase):
    """Tests pour les fonctions de normalisation audio"""
    
    def test_normalize_audio_simple_empty(self):
        """Test la normalisation simple avec audio vide"""
        from voice_assistant.utils.normalization import normalize_audio_simple
        
        empty_audio = np.array([], dtype=np.int16)
        result = normalize_audio_simple(empty_audio)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)
    
    def test_normalize_audio_simple_with_data(self):
        """Test la normalisation simple avec données"""
        from voice_assistant.utils.normalization import normalize_audio_simple
        
        # Créer un signal avec des valeurs connues
        audio = np.array([16384, -16384, 8192, -8192], dtype=np.int16)
        result = normalize_audio_simple(audio)
        
        # Vérifier que les valeurs sont normalisées
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        # Le pic devrait être proche de 0.9 * 32768
        max_val = np.max(np.abs(result))
        self.assertAlmostEqual(max_val / 32768, 0.9, places=1)
    
    def test_normalize_audio_advanced(self):
        """Test la normalisation avancée"""
        from voice_assistant.utils.normalization import normalize_audio_advanced
        
        # Signal avec DC offset
        audio = np.array([1000, 2000, 3000, 4000], dtype=np.int16)
        result = normalize_audio_advanced(audio)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        
        # Vérifier que le DC offset est supprimé
        result_float = result.astype(np.float32) / 32768.0
        mean_val = np.mean(result_float)
        self.assertAlmostEqual(mean_val, 0, places=2)
    
    @patch('scipy.signal.butter')
    @patch('scipy.signal.lfilter')
    def test_apply_bandpass_filter(self, mock_lfilter, mock_butter):
        """Test l'application d'un filtre passe-bande"""
        from voice_assistant.utils.normalization import apply_bandpass_filter
        
        # Mock du filtre
        mock_butter.return_value = (np.array([1]), np.array([1]))
        mock_lfilter.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        
        audio = np.array([1000, 2000, 3000, 4000], dtype=np.int16)
        result = apply_bandpass_filter(audio, 16000)
        
        self.assertIsNotNone(result)
        mock_butter.assert_called_once()
        mock_lfilter.assert_called_once()


class TestTextUtils(unittest.TestCase):
    """Tests pour les utilitaires de texte"""
    
    def test_simple_spell_correction(self):
        """Test la correction orthographique simple"""
        from voice_assistant.utils.text_utils import simple_spell_correction
        
        # Test des corrections prédéfinies
        test_cases = [
            ("imprimente", "imprimante"),
            ("modeme", "modem"),
            ("marche pas", "ne marche pas"),
            ("Imprimente", "Imprimante"),  # Test avec majuscule
        ]
        
        for input_text, expected in test_cases:
            result = simple_spell_correction(input_text)
            self.assertEqual(result.lower(), expected.lower())
    
    def test_preprocess_user_query(self):
        """Test le prétraitement des requêtes utilisateur"""
        from voice_assistant.utils.text_utils import preprocess_user_query
        
        # Test l'expansion des abréviations
        self.assertIn("problème", preprocess_user_query("pb"))
        self.assertIn("ordinateur", preprocess_user_query("pc"))
        
        # Test l'ajout de contexte pour requêtes courtes
        result = preprocess_user_query("ok")
        self.assertIn("J'ai une question", result)
    
    @patch('thefuzz.fuzz.ratio')
    def test_identify_problem_signature(self, mock_fuzz):
        """Test l'identification de signature de problème"""
        from voice_assistant.utils.text_utils import identify_problem_signature
        
        problem_patterns = [
            r"ne\s+marche\s+pas",
            r"problème"
        ]
        
        device_keywords = {
            "imprimante": ["imprimante", "impriment"],
            "wifi": ["wifi", "wi-fi"]
        }
        
        # Test avec correspondance exacte
        mock_fuzz.ratio.return_value = 100
        
        signature = identify_problem_signature(
            "mon imprimante ne marche pas",
            problem_patterns,
            device_keywords,
            80
        )
        
        self.assertEqual(signature, "imprimante_generic_problem")
        
        # Test sans problème détecté
        signature = identify_problem_signature(
            "mon imprimante fonctionne bien",
            problem_patterns,
            device_keywords,
            80
        )
        
        self.assertIsNone(signature)
    
    def test_format_history_as_string_for_prompt(self):
        """Test le formatage de l'historique de conversation"""
        from voice_assistant.utils.text_utils import format_history_as_string_for_prompt
        from langchain.schema import HumanMessage, AIMessage
        
        messages = [
            HumanMessage(content="Bonjour"),
            AIMessage(content="Bonjour! Comment puis-je vous aider?"),
            HumanMessage(content="J'ai un problème"),
            AIMessage(content="Je vous écoute")
        ]
        
        result = format_history_as_string_for_prompt(messages)
        
        self.assertIn("Utilisateur: Bonjour", result)
        self.assertIn("Assistant: Bonjour! Comment puis-je vous aider?", result)
        self.assertIn("Utilisateur: J'ai un problème", result)
        self.assertIn("Assistant: Je vous écoute", result)
    
    def test_format_history_empty(self):
        """Test le formatage avec historique vide"""
        from voice_assistant.utils.text_utils import format_history_as_string_for_prompt
        
        result = format_history_as_string_for_prompt([])
        self.assertEqual(result, "Pas d'historique de conversation.")


class TestConfig(unittest.TestCase):
    """Tests pour la gestion de configuration"""
    
    def setUp(self):
        """Préparation des tests"""
        self.test_config = {
            'general': {
                'device_type': 'cpu',
                'temp_dir': '/tmp/test'
            },
            'audio': {
                'rate': 16000,
                'chunk': 2048
            }
        }
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_config(self, mock_yaml_load, mock_file):
        """Test le chargement de configuration"""
        from voice_assistant.utils.config import Config
        
        mock_yaml_load.return_value = self.test_config
        
        config = Config('test_config.yaml')
        
        mock_file.assert_called_once()
        mock_yaml_load.assert_called_once()
        self.assertEqual(config.config_data, self.test_config)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_get_value(self, mock_yaml_load, mock_file):
        """Test la récupération de valeur"""
        from voice_assistant.utils.config import Config
        
        mock_yaml_load.return_value = self.test_config
        
        config = Config('test_config.yaml')
        
        # Test récupération normale
        self.assertEqual(config.get('general', 'device_type'), 'cpu')
        self.assertEqual(config.get('audio', 'rate'), 16000)
        
        # Test avec valeur par défaut
        self.assertEqual(config.get('inexistant', 'key', 'default'), 'default')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_get_section(self, mock_yaml_load, mock_file):
        """Test la récupération de section"""
        from voice_assistant.utils.config import Config
        
        mock_yaml_load.return_value = self.test_config
        
        config = Config('test_config.yaml')
        
        audio_section = config.get_section('audio')
        self.assertEqual(audio_section['rate'], 16000)
        self.assertEqual(audio_section['chunk'], 2048)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    @patch('yaml.safe_load')
    def test_save_config(self, mock_yaml_load, mock_yaml_dump, mock_file):
        """Test la sauvegarde de configuration"""
        from voice_assistant.utils.config import Config
        
        mock_yaml_load.return_value = self.test_config
        
        config = Config('test_config.yaml')
        config.update('general', 'new_key', 'new_value')
        
        result = config.save()
        
        self.assertTrue(result)
        mock_yaml_dump.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_update_value(self, mock_yaml_load, mock_file):
        """Test la mise à jour de valeur"""
        from voice_assistant.utils.config import Config
        
        mock_yaml_load.return_value = self.test_config
        
        config = Config('test_config.yaml')
        config.update('general', 'device_type', 'cuda')
        
        self.assertEqual(config.get('general', 'device_type'), 'cuda')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_update_section(self, mock_yaml_load, mock_file):
        """Test la mise à jour de section"""
        from voice_assistant.utils.config import Config
        
        mock_yaml_load.return_value = self.test_config
        
        config = Config('test_config.yaml')
        new_values = {
            'rate': 48000,
            'channels': 2
        }
        config.update_section('audio', new_values)
        
        self.assertEqual(config.get('audio', 'rate'), 48000)
        self.assertEqual(config.get('audio', 'channels'), 2)
    
    def test_get_config_singleton(self):
        """Test le singleton de configuration"""
        from voice_assistant.utils.config import get_config
        
        # Premier appel
        config1 = get_config()
        # Deuxième appel
        config2 = get_config()
        
        # Devrait être la même instance (singleton)
        self.assertIs(config1, config2)


if __name__ == '__main__':
    unittest.main()