"""
Moniteur de performance pour l'Assistant Vocal
"""

import time
import psutil
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class PerformanceMetrics:
    """Métriques de performance pour une session"""
    timestamp: float
    vad_latency: float = 0.0
    stt_latency: float = 0.0
    analysis_latency: float = 0.0
    llm_latency: float = 0.0
    tts_latency: float = 0.0
    audio_init_latency: float = 0.0
    total_latency: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    additional_metrics: Dict[str, float] = field(default_factory=dict)


class PerformanceMonitor:
    """Moniteur de performance pour mesurer les latences et ressources"""
    
    def __init__(self):
        self.timers: Dict[str, float] = {}
        self.current_metrics = PerformanceMetrics(timestamp=time.time())
        self.history: List[PerformanceMetrics] = []
        self._lock = threading.Lock()
        
    def start_timer(self, name: str) -> None:
        """Démarre un timer pour une opération"""
        with self._lock:
            self.timers[name] = time.perf_counter()
    
    def stop_timer(self, name: str) -> float:
        """Arrête un timer et retourne la durée"""
        with self._lock:
            if name not in self.timers:
                raise ValueError(f"Timer '{name}' n'a pas été démarré")
            
            duration = time.perf_counter() - self.timers[name]
            del self.timers[name]
            return duration
    
    def record_metric(self, metric_name: str, value: float) -> None:
        """Enregistre une métrique personnalisée"""
        with self._lock:
            if hasattr(self.current_metrics, metric_name):
                setattr(self.current_metrics, metric_name, value)
            else:
                self.current_metrics.additional_metrics[metric_name] = value
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Obtient les métriques système actuelles"""
        process = psutil.Process()
        
        return {
            'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
            'cpu_usage_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent()
        }
    
    def finalize_recording(self) -> None:
        """Finalise l'enregistrement des métriques actuelles"""
        with self._lock:
            # Calculer la latence totale
            total = (
                self.current_metrics.vad_latency +
                self.current_metrics.stt_latency +
                self.current_metrics.analysis_latency +
                self.current_metrics.llm_latency +
                self.current_metrics.tts_latency +
                self.current_metrics.audio_init_latency
            )
            self.current_metrics.total_latency = total
            
            # Ajouter les métriques système
            system_metrics = self.get_system_metrics()
            self.current_metrics.memory_usage_mb = system_metrics['memory_usage_mb']
            self.current_metrics.cpu_usage_percent = system_metrics['cpu_usage_percent']
            
            # Ajouter à l'historique
            self.history.append(self.current_metrics)
            
            # Réinitialiser pour la prochaine session
            self.current_metrics = PerformanceMetrics(timestamp=time.time())
    
    def get_latest_metrics(self) -> Optional[PerformanceMetrics]:
        """Retourne les dernières métriques enregistrées"""
        return self.history[-1] if self.history else None
    
    def get_average_metrics(self, last_n: Optional[int] = None) -> Dict[str, float]:
        """Calcule la moyenne des métriques sur les N dernières sessions"""
        if not self.history:
            return {}
        
        sessions = self.history[-last_n:] if last_n else self.history
        if not sessions:
            return {}
        
        averages = {}
        metrics_to_average = [
            'vad_latency', 'stt_latency', 'analysis_latency', 
            'llm_latency', 'tts_latency', 'audio_init_latency',
            'total_latency', 'memory_usage_mb', 'cpu_usage_percent'
        ]
        
        for metric in metrics_to_average:
            values = [getattr(session, metric) for session in sessions]
            averages[metric] = sum(values) / len(values)
        
        return averages
    
    def export_metrics(self, file_path: str) -> None:
        """Exporte les métriques vers un fichier JSON"""
        data = {
            'sessions': [
                {
                    'timestamp': session.timestamp,
                    'vad_latency': session.vad_latency,
                    'stt_latency': session.stt_latency,
                    'analysis_latency': session.analysis_latency,
                    'llm_latency': session.llm_latency,
                    'tts_latency': session.tts_latency,
                    'audio_init_latency': session.audio_init_latency,
                    'total_latency': session.total_latency,
                    'memory_usage_mb': session.memory_usage_mb,
                    'cpu_usage_percent': session.cpu_usage_percent,
                    'additional_metrics': session.additional_metrics
                }
                for session in self.history
            ],
            'averages': self.get_average_metrics(),
            'export_timestamp': time.time()
        }
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def clear_history(self) -> None:
        """Efface l'historique des métriques"""
        with self._lock:
            self.history.clear()
    
    def benchmark_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Benchmark une opération et retourne le résultat et la durée"""
        self.start_timer(operation_name)
        try:
            result = operation_func(*args, **kwargs)
            return result
        finally:
            duration = self.stop_timer(operation_name)
            self.record_metric(f"{operation_name}_latency", duration)


# Instance globale pour utilisation simple
global_performance_monitor = PerformanceMonitor()


def benchmark(operation_name: str):
    """Décorateur pour benchmarker automatiquement une fonction"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return global_performance_monitor.benchmark_operation(
                operation_name, func, *args, **kwargs
            )
        return wrapper
    return decorator