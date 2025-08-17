from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import  unittest
class TestMemoryUsage(unittest.TestCase):
    """Tests d'utilisation mémoire"""
    
    def test_memory_leak_detection(self):
        """Test pour détecter les fuites mémoire"""
        import gc
        import tracemalloc
        
        tracemalloc.start()
        
        # Snapshot initial
        snapshot1 = tracemalloc.take_snapshot()
        
        # Exécuter plusieurs cycles d'opérations
        for _ in range(10):
            # Simuler des opérations gourmandes en mémoire
            data = np.random.randn(16000 * 10)  # 10 secondes d'audio
            processed = data * 0.5
            del data, processed
            gc.collect()
        
        # Snapshot final
        snapshot2 = tracemalloc.take_snapshot()
        
        # Analyser les différences
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # Vérifier qu'il n'y a pas de croissance excessive
        total_diff = sum(stat.size_diff for stat in top_stats)
        
        # Tolérance de 10MB
        self.assertLess(total_diff, 10 * 1024 * 1024)
        
        tracemalloc.stop()