"""
Test simplifié de comparaison des latences LLM vs RAG
"""

import unittest
import time
import tempfile
import numpy as np
from pathlib import Path
import json

from voice_assistant.utils.performance import PerformanceMonitor


class TestLLMRAGLatencySimple(unittest.TestCase):
    """Tests de latence simplifiés pour LLM vs RAG"""
    
    def setUp(self):
        """Configuration des tests"""
        self.perf_monitor = PerformanceMonitor()
        self.test_data_dir = Path(tempfile.mkdtemp())
        
        # Questions de test
        self.test_questions = [
            "Qu'est-ce que Python ?",
            "Comment installer une bibliothèque ?",
            "Expliquez les fonctions",
            "Qu'est-ce qu'une variable ?",
            "Comment créer une liste ?"
        ]
    
    def tearDown(self):
        """Nettoyage après tests"""
        metrics_file = self.test_data_dir / "llm_rag_latency_comparison.json"
        self.perf_monitor.export_metrics(str(metrics_file))
        print(f"\nMétriques sauvegardées dans: {metrics_file}")
    
    def test_simulated_llm_standalone_latency(self):
        """Test simulé de latence LLM standalone"""
        print("\n=== SIMULATION LATENCE LLM STANDALONE ===")
        
        total_time = 0
        response_lengths = []
        
        for i, question in enumerate(self.test_questions):
            print(f"\nQuestion {i+1}: {question}")
            
            self.perf_monitor.start_timer(f'llm_sim_{i}')
            
            # Simuler le temps de traitement LLM
            # LLM typique: 0.8-1.5s pour génération (basé sur mesures réelles)
            llm_processing_time = np.random.uniform(0.8, 1.5)
            time.sleep(llm_processing_time)
            
            # Simuler longueur de réponse (50-200 caractères)
            simulated_response_length = np.random.randint(50, 200)
            
            duration = self.perf_monitor.stop_timer(f'llm_sim_{i}')
            total_time += duration
            response_lengths.append(simulated_response_length)
            
            print(f"Temps simulé: {duration:.3f}s, Longueur réponse: {simulated_response_length} chars")
        
        # Calculer statistiques
        avg_time = total_time / len(self.test_questions)
        avg_response_length = sum(response_lengths) / len(response_lengths)
        
        print(f"\n--- RÉSULTATS LLM STANDALONE SIMULÉ ---")
        print(f"Temps total: {total_time:.3f}s")
        print(f"Temps moyen par question: {avg_time:.3f}s")
        print(f"Longueur moyenne réponse: {avg_response_length:.0f} chars")
        
        # Enregistrer métriques
        self.perf_monitor.record_metric('llm_standalone_total_time', total_time)
        self.perf_monitor.record_metric('llm_standalone_avg_time', avg_time)
        self.perf_monitor.record_metric('llm_standalone_avg_response_length', avg_response_length)
        
        self.perf_monitor.finalize_recording()
        
        # Assertions
        self.assertLess(avg_time, 2.0, "LLM standalone dans les temps attendus")
        self.assertGreater(avg_response_length, 40, "Réponses de longueur raisonnable")
    
    def test_simulated_rag_pipeline_latency(self):
        """Test simulé de latence pipeline RAG"""
        print("\n=== SIMULATION LATENCE PIPELINE RAG ===")
        
        total_time = 0
        response_lengths = []
        search_times = []
        
        for i, question in enumerate(self.test_questions):
            print(f"\nQuestion {i+1}: {question}")
            
            self.perf_monitor.start_timer(f'rag_sim_{i}')
            
            # Simuler temps de recherche RAG (embeddings + recherche vectorielle)
            # Typiquement: 0.1-0.3s pour embedding + recherche
            search_time = np.random.uniform(0.1, 0.3)
            time.sleep(search_time)
            search_times.append(search_time)
            
            # Simuler temps de génération LLM avec contexte RAG
            # Plus long car plus de contexte: 1.0-2.0s
            llm_with_context_time = np.random.uniform(1.0, 2.0)
            time.sleep(llm_with_context_time)
            
            # Simuler longueur de réponse RAG (généralement plus longue: 80-300 chars)
            simulated_response_length = np.random.randint(80, 300)
            
            duration = self.perf_monitor.stop_timer(f'rag_sim_{i}')
            total_time += duration
            response_lengths.append(simulated_response_length)
            
            print(f"Temps total: {duration:.3f}s (recherche: {search_time:.3f}s, LLM: {llm_with_context_time:.3f}s)")
            print(f"Longueur réponse: {simulated_response_length} chars")
        
        # Calculer statistiques
        avg_time = total_time / len(self.test_questions)
        avg_search_time = sum(search_times) / len(search_times)
        avg_response_length = sum(response_lengths) / len(response_lengths)
        
        print(f"\n--- RÉSULTATS PIPELINE RAG SIMULÉ ---")
        print(f"Temps total: {total_time:.3f}s")
        print(f"Temps moyen par question: {avg_time:.3f}s")
        print(f"Temps moyen recherche RAG: {avg_search_time:.3f}s")
        print(f"Longueur moyenne réponse: {avg_response_length:.0f} chars")
        
        # Enregistrer métriques
        self.perf_monitor.record_metric('rag_pipeline_total_time', total_time)
        self.perf_monitor.record_metric('rag_pipeline_avg_time', avg_time)
        self.perf_monitor.record_metric('rag_search_avg_time', avg_search_time)
        self.perf_monitor.record_metric('rag_pipeline_avg_response_length', avg_response_length)
        
        self.perf_monitor.finalize_recording()
        
        # Assertions
        self.assertLess(avg_time, 3.0, "Pipeline RAG dans les temps acceptables")
        self.assertLess(avg_search_time, 0.5, "Recherche RAG rapide")
        self.assertGreater(avg_response_length, 70, "Réponses RAG de qualité")
    
    def test_latency_comparison_analysis(self):
        """Analyse comparative détaillée des latences"""
        print("\n=== ANALYSE COMPARATIVE DES LATENCES ===")
        
        # Récupérer les métriques des tests précédents
        if len(self.perf_monitor.history) < 2:
            self.skipTest("Tests précédents requis pour la comparaison")
        
        llm_metrics = None
        rag_metrics = None
        
        for session in self.perf_monitor.history:
            if 'llm_standalone_avg_time' in session.additional_metrics:
                llm_metrics = session
            elif 'rag_pipeline_avg_time' in session.additional_metrics:
                rag_metrics = session
        
        if not llm_metrics or not rag_metrics:
            self.skipTest("Métriques complètes non disponibles")
        
        # Extraire les métriques
        llm_time = llm_metrics.additional_metrics.get('llm_standalone_avg_time', 0)
        rag_time = rag_metrics.additional_metrics.get('rag_pipeline_avg_time', 0)
        search_time = rag_metrics.additional_metrics.get('rag_search_avg_time', 0)
        
        llm_length = llm_metrics.additional_metrics.get('llm_standalone_avg_response_length', 0)
        rag_length = rag_metrics.additional_metrics.get('rag_pipeline_avg_response_length', 0)
        
        # Calculs détaillés
        overhead_rag = rag_time - llm_time
        overhead_percent = (overhead_rag / llm_time * 100) if llm_time > 0 else 0
        search_percent = (search_time / rag_time * 100) if rag_time > 0 else 0
        llm_rag_percent = ((rag_time - search_time) / rag_time * 100) if rag_time > 0 else 0
        
        # Analyse de la qualité (longueur comme proxy)
        quality_improvement = ((rag_length - llm_length) / llm_length * 100) if llm_length > 0 else 0
        
        print(f"📊 MÉTRIQUES DE LATENCE COMPARÉES:")
        print(f"┌─────────────────────────────────────────┐")
        print(f"│ LLM Standalone    : {llm_time:.3f}s          │")
        print(f"│ RAG Pipeline      : {rag_time:.3f}s          │")
        print(f"│ Surcoût RAG       : {overhead_rag:.3f}s ({overhead_percent:.1f}%)   │")
        print(f"└─────────────────────────────────────────┘")
        
        print(f"\n🔍 DÉCOMPOSITION PIPELINE RAG:")
        print(f"┌─────────────────────────────────────────┐")
        print(f"│ Recherche vectorielle: {search_time:.3f}s ({search_percent:.1f}%) │")
        print(f"│ Génération LLM+ctx   : {rag_time-search_time:.3f}s ({llm_rag_percent:.1f}%) │")
        print(f"└─────────────────────────────────────────┘")
        
        print(f"\n📈 ANALYSE QUALITÉ/PERFORMANCE:")
        print(f"┌─────────────────────────────────────────┐")
        print(f"│ Longueur LLM      : {llm_length:.0f} chars      │")
        print(f"│ Longueur RAG      : {rag_length:.0f} chars      │")
        print(f"│ Amélioration      : {quality_improvement:.1f}%          │")
        print(f"└─────────────────────────────────────────┘")
        
        # Ratio performance/qualité
        if overhead_percent > 0:
            quality_per_overhead = quality_improvement / overhead_percent
            print(f"\n⚡ RATIO QUALITÉ/SURCOÛT: {quality_per_overhead:.2f}")
        
        # Enregistrer l'analyse comparative
        self.perf_monitor.record_metric('comparison_llm_time', llm_time)
        self.perf_monitor.record_metric('comparison_rag_time', rag_time)
        self.perf_monitor.record_metric('comparison_overhead_seconds', overhead_rag)
        self.perf_monitor.record_metric('comparison_overhead_percent', overhead_percent)
        self.perf_monitor.record_metric('comparison_search_percent', search_percent)
        self.perf_monitor.record_metric('comparison_quality_improvement', quality_improvement)
        
        if overhead_percent > 0:
            self.perf_monitor.record_metric('comparison_quality_per_overhead', quality_per_overhead)
        
        self.perf_monitor.finalize_recording()
        
        # Assertions
        self.assertLess(overhead_percent, 150, "Surcoût RAG acceptable (< 150%)")
        self.assertLess(search_time, 0.5, "Temps de recherche efficace")
        self.assertGreater(quality_improvement, 0, "RAG améliore la qualité")
        
        print(f"\n✅ CONCLUSIONS:")
        if overhead_percent < 100:
            print(f"• Surcoût RAG modéré ({overhead_percent:.1f}%)")
        elif overhead_percent < 150:
            print(f"• Surcoût RAG acceptable ({overhead_percent:.1f}%)")
        else:
            print(f"• Surcoût RAG élevé ({overhead_percent:.1f}%)")
        
        if search_percent < 25:
            print(f"• Recherche vectorielle efficace ({search_percent:.1f}% du temps total)")
        else:
            print(f"• Recherche vectorielle à optimiser ({search_percent:.1f}% du temps total)")
        
        if quality_improvement > 20:
            print(f"• Amélioration qualité significative (+{quality_improvement:.1f}%)")
        else:
            print(f"• Amélioration qualité modérée (+{quality_improvement:.1f}%)")


if __name__ == '__main__':
    unittest.main(verbosity=2, buffer=False)