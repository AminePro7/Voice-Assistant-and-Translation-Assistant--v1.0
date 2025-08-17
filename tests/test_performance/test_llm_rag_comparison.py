"""
Test de comparaison des performances LLM vs RAG+LLM
"""

import unittest
import time
import tempfile
import os
from pathlib import Path
import json

from voice_assistant.utils.performance import PerformanceMonitor
from voice_assistant.utils.config import Config


class TestLLMvsRAGPerformance(unittest.TestCase):
    """Tests de comparaison entre LLM seul et pipeline RAG+LLM"""
    
    def setUp(self):
        """Configuration des tests"""
        self.perf_monitor = PerformanceMonitor()
        self.test_data_dir = Path(tempfile.mkdtemp())
        
        # Questions de test
        self.test_questions = [
            "Qu'est-ce que Python ?",
            "Comment installer une bibliothèque Python ?",
            "Expliquez les fonctions en Python",
            "Qu'est-ce qu'une variable ?",
            "Comment créer une liste en Python ?",
            "Expliquez les boucles for",
            "Qu'est-ce qu'un dictionnaire ?",
            "Comment lire un fichier en Python ?",
            "Expliquez les classes et objets",
            "Comment gérer les erreurs en Python ?"
        ]
        
        # Charger la configuration
        try:
            self.config = Config()
            print(f"Configuration chargée depuis: {self.config.config_path}")
        except Exception as e:
            print(f"Erreur chargement config: {e}")
            self.config = None
    
    def tearDown(self):
        """Nettoyage après tests"""
        metrics_file = self.test_data_dir / "llm_rag_comparison.json"
        self.perf_monitor.export_metrics(str(metrics_file))
        print(f"\nMétriques sauvegardées dans: {metrics_file}")
    
    def test_llm_standalone_performance(self):
        """Test de performance du LLM seul (sans RAG)"""
        print("\n=== BENCHMARK LLM STANDALONE ===")
        
        if not self.config:
            self.skipTest("Configuration non disponible")
        
        try:
            # Initialiser le LLM seulement
            from voice_assistant.llm.llama_cpp_llm import LlamaCppLLM
            
            llm = LlamaCppLLM(self.config)
            llm_type = "LlamaCpp"
            print(f"Utilisation de {llm_type} LLM")
            
            total_time = 0
            response_lengths = []
            
            for i, question in enumerate(self.test_questions):
                print(f"\nQuestion {i+1}: {question}")
                
                self.perf_monitor.start_timer(f'llm_standalone_{i}')
                
                try:
                    # Générer réponse avec LLM seul
                    response = llm.generate(question, max_tokens=150, temperature=0.7)
                    
                    duration = self.perf_monitor.stop_timer(f'llm_standalone_{i}')
                    total_time += duration
                    response_lengths.append(len(response))
                    
                    print(f"Temps: {duration:.3f}s, Longueur réponse: {len(response)} chars")
                    print(f"Réponse: {response[:100]}...")
                    
                except Exception as e:
                    print(f"Erreur génération: {e}")
                    # Continuer avec les autres questions
                    self.perf_monitor.stop_timer(f'llm_standalone_{i}')
                    continue
            
            # Calculer statistiques
            avg_time = total_time / len(self.test_questions)
            avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
            
            print(f"\n--- RÉSULTATS LLM STANDALONE ---")
            print(f"Temps total: {total_time:.3f}s")
            print(f"Temps moyen par question: {avg_time:.3f}s")
            print(f"Longueur moyenne réponse: {avg_response_length:.0f} chars")
            
            # Enregistrer métriques
            self.perf_monitor.record_metric('llm_standalone_total_time', total_time)
            self.perf_monitor.record_metric('llm_standalone_avg_time', avg_time)
            self.perf_monitor.record_metric('llm_standalone_avg_response_length', avg_response_length)
            self.perf_monitor.record_metric('llm_type_used', hash(llm_type))  # Identifier le type de LLM
            
            self.perf_monitor.finalize_recording()
            
            # Assertions
            self.assertLess(avg_time, 10.0, "LLM standalone trop lent")
            self.assertGreater(avg_response_length, 50, "Réponses trop courtes")
            
        except Exception as e:
            self.fail(f"Erreur dans test LLM standalone: {e}")
    
    def test_rag_pipeline_performance(self):
        """Test de performance du pipeline RAG complet"""
        print("\n=== BENCHMARK PIPELINE RAG ===")
        
        if not self.config:
            self.skipTest("Configuration non disponible")
        
        try:
            # Vérifier si les composants RAG sont disponibles
            from voice_assistant.rag.faiss_rag import FaissRAG
            from voice_assistant.llm.llama_cpp_llm import LlamaCppLLM
            
            # Initialiser le système RAG
            llm = LlamaCppLLM(self.config)
            llm_type = "LlamaCpp"
            
            # Créer un document de test pour RAG
            test_doc_path = self.test_data_dir / "test_knowledge.md"
            test_doc_content = """
# Documentation Python de base

## Variables
En Python, les variables sont créées en assignant une valeur avec le signe =.
Exemple: nom = "Alice", age = 25

## Listes
Les listes sont des collections ordonnées d'éléments.
Exemple: ma_liste = [1, 2, 3, "hello"]

## Dictionnaires
Les dictionnaires stockent des paires clé-valeur.
Exemple: personne = {"nom": "Alice", "age": 25}

## Fonctions
Les fonctions sont définies avec le mot-clé def.
Exemple: def ma_fonction(): return "Hello"

## Boucles
La boucle for permet d'itérer sur des éléments.
Exemple: for i in range(5): print(i)

## Classes
Les classes permettent de créer des objets.
Exemple: class Personne: def __init__(self, nom): self.nom = nom

## Gestion d'erreurs
Utilisez try/except pour gérer les erreurs.
Exemple: try: resultat = 10/0 except: print("Erreur")

## Installation
Utilisez pip pour installer des packages.
Exemple: pip install requests
            """
            
            test_doc_path.write_text(test_doc_content, encoding='utf-8')
            
            # Configurer RAG avec le document de test
            rag_config = self.config.get_section('rag', {})
            rag_config['doc_path'] = str(test_doc_path)
            rag_config['vectorstore_dir'] = str(self.test_data_dir / "test_vectorstore")
            
            print(f"Initialisation RAG avec document: {test_doc_path}")
            rag_system = FaissRAG(rag_config, llm)
            
            total_time = 0
            response_lengths = []
            search_times = []
            
            for i, question in enumerate(self.test_questions):
                print(f"\nQuestion {i+1}: {question}")
                
                self.perf_monitor.start_timer(f'rag_pipeline_{i}')
                
                try:
                    # Mesurer temps de recherche RAG séparément
                    search_start = time.perf_counter()
                    relevant_docs = rag_system.search(question, k=3)
                    search_time = time.perf_counter() - search_start
                    search_times.append(search_time)
                    
                    # Générer réponse avec contexte RAG
                    response = rag_system.generate_response(question)
                    
                    duration = self.perf_monitor.stop_timer(f'rag_pipeline_{i}')
                    total_time += duration
                    response_lengths.append(len(response))
                    
                    print(f"Temps total: {duration:.3f}s (dont recherche: {search_time:.3f}s)")
                    print(f"Docs trouvés: {len(relevant_docs)}, Longueur réponse: {len(response)} chars")
                    print(f"Réponse: {response[:100]}...")
                    
                except Exception as e:
                    print(f"Erreur pipeline RAG: {e}")
                    self.perf_monitor.stop_timer(f'rag_pipeline_{i}')
                    continue
            
            # Calculer statistiques
            avg_time = total_time / len(self.test_questions)
            avg_search_time = sum(search_times) / len(search_times) if search_times else 0
            avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
            
            print(f"\n--- RÉSULTATS PIPELINE RAG ---")
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
            self.assertLess(avg_time, 15.0, "Pipeline RAG trop lent")
            self.assertLess(avg_search_time, 1.0, "Recherche RAG trop lente")
            self.assertGreater(avg_response_length, 100, "Réponses RAG trop courtes")
            
        except Exception as e:
            self.fail(f"Erreur dans test pipeline RAG: {e}")
    
    def test_comparison_analysis(self):
        """Analyse comparative des performances"""
        print("\n=== ANALYSE COMPARATIVE ===")
        
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
        
        # Comparaison des temps
        llm_time = llm_metrics.additional_metrics.get('llm_standalone_avg_time', 0)
        rag_time = rag_metrics.additional_metrics.get('rag_pipeline_avg_time', 0)
        search_time = rag_metrics.additional_metrics.get('rag_search_avg_time', 0)
        
        # Comparaison des longueurs de réponse
        llm_length = llm_metrics.additional_metrics.get('llm_standalone_avg_response_length', 0)
        rag_length = rag_metrics.additional_metrics.get('rag_pipeline_avg_response_length', 0)
        
        # Calculs
        overhead_rag = rag_time - llm_time
        overhead_percent = (overhead_rag / llm_time * 100) if llm_time > 0 else 0
        search_percent = (search_time / rag_time * 100) if rag_time > 0 else 0
        
        print(f"Temps moyen LLM seul: {llm_time:.3f}s")
        print(f"Temps moyen RAG+LLM: {rag_time:.3f}s")
        print(f"Surcoût RAG: {overhead_rag:.3f}s ({overhead_percent:.1f}%)")
        print(f"Temps recherche: {search_time:.3f}s ({search_percent:.1f}% du total RAG)")
        print(f"Longueur réponse LLM: {llm_length:.0f} chars")
        print(f"Longueur réponse RAG: {rag_length:.0f} chars")
        
        # Enregistrer l'analyse comparative
        self.perf_monitor.record_metric('comparison_llm_time', llm_time)
        self.perf_monitor.record_metric('comparison_rag_time', rag_time)
        self.perf_monitor.record_metric('comparison_overhead_seconds', overhead_rag)
        self.perf_monitor.record_metric('comparison_overhead_percent', overhead_percent)
        self.perf_monitor.record_metric('comparison_search_percent', search_percent)
        
        self.perf_monitor.finalize_recording()
        
        # Assertions
        self.assertLess(overhead_percent, 200, "Surcoût RAG acceptable (< 200%)")
        self.assertLess(search_time, 1.0, "Temps de recherche acceptable")
        

if __name__ == '__main__':
    unittest.main(verbosity=2, buffer=False)