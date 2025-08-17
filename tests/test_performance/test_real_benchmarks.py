"""
Tests de benchmarks réels pour l'Assistant Vocal
"""

import unittest
import time
import tempfile
import numpy as np
from pathlib import Path
import json
import psutil
import os

from voice_assistant.utils.performance import PerformanceMonitor


class TestRealBenchmarks(unittest.TestCase):
    """Tests de performance avec métriques réelles"""
    
    def setUp(self):
        """Configuration du moniteur de performance"""
        self.perf_monitor = PerformanceMonitor()
        self.test_data_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Nettoyage après les tests"""
        # Sauvegarder les métriques
        metrics_file = self.test_data_dir / "benchmark_results.json"
        self.perf_monitor.export_metrics(str(metrics_file))
        print(f"\nMétriques sauvegardées dans: {metrics_file}")
    
    def test_system_performance_baseline(self):
        """Test de performance de base du système"""
        print("\n=== BENCHMARK BASELINE SYSTÈME ===")
        
        # Mesurer les performances système
        process = psutil.Process()
        
        # Mesure mémoire initiale
        memory_before = process.memory_info().rss / 1024 / 1024
        print(f"Mémoire initiale: {memory_before:.2f} MB")
        
        # Mesure CPU
        cpu_percent = process.cpu_percent(interval=1)
        print(f"Utilisation CPU: {cpu_percent:.2f}%")
        
        # Test de traitement de données audio simulées
        self.perf_monitor.start_timer('audio_processing')
        
        # Simuler traitement audio (16 kHz, 10 secondes)
        sample_rate = 16000
        duration = 10
        audio_data = np.random.randn(sample_rate * duration).astype(np.float32)
        
        # Opérations de traitement audio
        for i in range(5):
            # Simulation VAD
            windowed = audio_data[i*sample_rate:(i+1)*sample_rate]
            energy = np.sum(windowed ** 2)
            
            # Simulation normalisation
            normalized = windowed / np.max(np.abs(windowed)) if np.max(np.abs(windowed)) > 0 else windowed
        
        audio_processing_time = self.perf_monitor.stop_timer('audio_processing')
        print(f"Temps traitement audio (10s): {audio_processing_time:.3f}s")
        
        # Mesure mémoire finale
        memory_after = process.memory_info().rss / 1024 / 1024
        memory_diff = memory_after - memory_before
        print(f"Mémoire finale: {memory_after:.2f} MB (diff: {memory_diff:+.2f} MB)")
        
        # Enregistrer les métriques
        self.perf_monitor.record_metric('audio_processing_latency', audio_processing_time)
        self.perf_monitor.record_metric('memory_usage_mb', memory_after)
        self.perf_monitor.record_metric('memory_diff_mb', memory_diff)
        self.perf_monitor.record_metric('cpu_usage_percent', cpu_percent)
        
        # Assertions
        self.assertLess(audio_processing_time, 2.0, "Traitement audio trop lent")
        self.assertLess(memory_diff, 100, "Utilisation mémoire excessive")
        
        self.perf_monitor.finalize_recording()
    
    def test_concurrent_operations_performance(self):
        """Test de performance avec opérations concurrentes"""
        print("\n=== BENCHMARK OPÉRATIONS CONCURRENTES ===")
        
        import threading
        import concurrent.futures
        
        def simulate_component_work(component_name, work_duration):
            """Simule le travail d'un composant"""
            self.perf_monitor.start_timer(f'{component_name}_work')
            
            # Simulation de travail CPU intensif
            start = time.perf_counter()
            while time.perf_counter() - start < work_duration:
                # Opération CPU intensive
                np.random.randn(1000).sum()
            
            duration = self.perf_monitor.stop_timer(f'{component_name}_work')
            return component_name, duration
        
        # Tester les performances avec plusieurs "composants" concurrents
        components = [
            ('vad', 0.1),
            ('stt', 0.3),
            ('llm', 0.8),
            ('tts', 0.2),
            ('audio_player', 0.05)
        ]
        
        start_total = time.perf_counter()
        
        # Exécution concurrente
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(simulate_component_work, name, duration)
                for name, duration in components
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_concurrent_time = time.perf_counter() - start_total
        
        print(f"Temps total concurrent: {total_concurrent_time:.3f}s")
        
        # Calculer le temps séquentiel théorique
        sequential_time = sum(duration for _, duration in components)
        print(f"Temps séquentiel théorique: {sequential_time:.3f}s")
        
        # Facteur d'amélioration
        speedup = sequential_time / total_concurrent_time
        print(f"Facteur d'amélioration: {speedup:.2f}x")
        
        # Enregistrer les métriques
        for component_name, actual_duration in results:
            self.perf_monitor.record_metric(f'{component_name}_latency', actual_duration)
        
        self.perf_monitor.record_metric('total_concurrent_time', total_concurrent_time)
        self.perf_monitor.record_metric('speedup_factor', speedup)
        
        # Assertions
        self.assertGreater(speedup, 1.5, "Parallélisation insuffisante")
        self.assertLess(total_concurrent_time, sequential_time * 0.8, "Pas d'amélioration significative")
        
        self.perf_monitor.finalize_recording()
    
    def test_memory_stress_test(self):
        """Test de stress mémoire"""
        print("\n=== BENCHMARK STRESS MÉMOIRE ===")
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        peak_memory = initial_memory
        
        # Allouer progressivement de la mémoire
        data_chunks = []
        
        for i in range(10):
            self.perf_monitor.start_timer(f'memory_allocation_{i}')
            
            # Allouer 50MB de données audio simulées
            chunk_size = 50 * 1024 * 1024 // 4  # 50MB en float32
            chunk = np.random.randn(chunk_size).astype(np.float32)
            data_chunks.append(chunk)
            
            alloc_time = self.perf_monitor.stop_timer(f'memory_allocation_{i}')
            
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            peak_memory = max(peak_memory, current_memory)
            
            print(f"Chunk {i+1}: {alloc_time:.3f}s, Mémoire: {current_memory:.1f}MB")
            
            # Vérifier que l'allocation ne prend pas trop de temps
            self.assertLess(alloc_time, 1.0, f"Allocation {i} trop lente")
        
        # Test de libération mémoire
        self.perf_monitor.start_timer('memory_cleanup')
        del data_chunks
        import gc
        gc.collect()
        cleanup_time = self.perf_monitor.stop_timer('memory_cleanup')
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        print(f"Mémoire pic: {peak_memory:.1f}MB")
        print(f"Mémoire finale: {final_memory:.1f}MB")
        print(f"Temps nettoyage: {cleanup_time:.3f}s")
        
        # Enregistrer métriques
        self.perf_monitor.record_metric('peak_memory_mb', peak_memory)
        self.perf_monitor.record_metric('memory_cleanup_time', cleanup_time)
        self.perf_monitor.record_metric('memory_freed_mb', peak_memory - final_memory)
        
        # Assertions
        self.assertLess(cleanup_time, 2.0, "Nettoyage mémoire trop lent")
        self.assertLess(final_memory, peak_memory * 0.3, "Mémoire non libérée correctement")
        
        self.perf_monitor.finalize_recording()
    
    def test_io_performance(self):
        """Test de performance I/O"""
        print("\n=== BENCHMARK PERFORMANCE I/O ===")
        
        # Test écriture fichier
        test_file = self.test_data_dir / "io_test.dat"
        data_size_mb = 10
        test_data = np.random.bytes(data_size_mb * 1024 * 1024)
        
        self.perf_monitor.start_timer('file_write')
        with open(test_file, 'wb') as f:
            f.write(test_data)
        write_time = self.perf_monitor.stop_timer('file_write')
        
        write_speed = data_size_mb / write_time
        print(f"Écriture {data_size_mb}MB: {write_time:.3f}s ({write_speed:.1f} MB/s)")
        
        # Test lecture fichier
        self.perf_monitor.start_timer('file_read')
        with open(test_file, 'rb') as f:
            read_data = f.read()
        read_time = self.perf_monitor.stop_timer('file_read')
        
        read_speed = data_size_mb / read_time
        print(f"Lecture {data_size_mb}MB: {read_time:.3f}s ({read_speed:.1f} MB/s)")
        
        # Vérifier intégrité
        self.assertEqual(len(read_data), len(test_data), "Données corrompues")
        
        # Enregistrer métriques
        self.perf_monitor.record_metric('io_write_speed_mbps', write_speed)
        self.perf_monitor.record_metric('io_read_speed_mbps', read_speed)
        self.perf_monitor.record_metric('io_write_time', write_time)
        self.perf_monitor.record_metric('io_read_time', read_time)
        
        # Assertions
        self.assertGreater(write_speed, 10, "Vitesse écriture trop lente")
        self.assertGreater(read_speed, 20, "Vitesse lecture trop lente")
        
        self.perf_monitor.finalize_recording()
        
        # Nettoyage
        test_file.unlink()


if __name__ == '__main__':
    # Exécuter avec output détaillé
    unittest.main(verbosity=2, buffer=False)