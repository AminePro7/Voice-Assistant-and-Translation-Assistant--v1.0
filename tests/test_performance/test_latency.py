from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import unittest
import time
from voice_assistant.utils.performance import PerformanceMonitor

class TestLatencyMeasurement(unittest.TestCase):
    """Tests de mesure de latence"""
    
    def setUp(self):
        """Configuration du moniteur de performance"""
        self.perf_monitor = PerformanceMonitor()
    
    def test_latency_measurement_accuracy(self):
        """Test la précision des mesures de latence"""
        
        # Démarrer un timer
        self.perf_monitor.start_timer('test_operation')
        
        # Simuler une opération de 100ms
        time.sleep(0.1)
        
        # Arrêter le timer
        duration = self.perf_monitor.stop_timer('test_operation')
        
        # Vérifier la précision (tolérance de 10ms)
        self.assertAlmostEqual(duration, 0.1, delta=0.01)
    
    def test_component_latencies(self):
        """Test les latences individuelles des composants"""
        
        # Simuler les latences de chaque composant
        latencies = {
            'vad_latency': 0.5,
            'stt_latency': 0.3,
            'analysis_latency': 0.05,
            'llm_latency': 1.2,
            'tts_latency': 0.2,
            'audio_init_latency': 0.02
        }
        
        for metric_name, value in latencies.items():
            self.perf_monitor.record_metric(metric_name, value)
        
        # Finaliser l'enregistrement
        self.perf_monitor.finalize_recording()
        
        # Vérifier la latence totale
        expected_total = sum(latencies.values())
        actual_total = self.perf_monitor.history[-1].total_latency
        
        self.assertAlmostEqual(actual_total, expected_total, places=2)
    
    @patch('time.perf_counter')
    def test_streaming_latency(self, mock_perf_counter):
        """Test la latence du streaming TTS"""
        
        # Simuler le temps qui passe
        times = [0, 0.1, 0.2, 0.3]  # Temps simulés
        mock_perf_counter.side_effect = times
        
        self.perf_monitor.start_timer('first_chunk')
        # Simulation de génération du premier chunk
        first_chunk_latency = self.perf_monitor.stop_timer('first_chunk')
        
        self.assertEqual(first_chunk_latency, 0.1)
