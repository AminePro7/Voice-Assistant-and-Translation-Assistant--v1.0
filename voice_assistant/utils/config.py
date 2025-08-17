# -*- coding: utf-8 -*-
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union


class Config:
    """Gestionnaire de configuration pour l'assistant vocal"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialise la configuration à partir d'un fichier YAML
        
        Args:
            config_path: Chemin vers le fichier de configuration YAML.
                         Si None, utilise le fichier de configuration par défaut.
        """
        if config_path is None:
            # Utilise le fichier de configuration par défaut
            root_dir = Path(__file__).parent.parent.parent
            config_path = root_dir / "voice_assistant" / "config" / "default_config.yaml"
        
        self.config_path = Path(config_path)
        self.config_data = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                return config_data
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            return {}
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration
        
        Args:
            section: Section de configuration (ex: 'audio', 'stt', etc.)
            key: Clé de configuration dans la section
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            La valeur de configuration ou la valeur par défaut
        """
        try:
            return self.config_data.get(section, {}).get(key, default)
        except (KeyError, AttributeError):
            return default
    
    def get_section(self, section: str, default: Any = None) -> Dict[str, Any]:
        """
        Récupère une section entière de configuration
        
        Args:
            section: Section de configuration (ex: 'audio', 'stt', etc.)
            default: Valeur par défaut si la section n'existe pas
            
        Returns:
            La section de configuration ou la valeur par défaut
        """
        return self.config_data.get(section, default or {})
    
    def save(self) -> bool:
        """
        Sauvegarde la configuration actuelle dans le fichier YAML
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def update(self, section: str, key: str, value: Any) -> None:
        """
        Met à jour une valeur de configuration
        
        Args:
            section: Section de configuration (ex: 'audio', 'stt', etc.)
            key: Clé de configuration dans la section
            value: Nouvelle valeur
        """
        if section not in self.config_data:
            self.config_data[section] = {}
        self.config_data[section][key] = value
    
    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """
        Met à jour une section entière de configuration
        
        Args:
            section: Section de configuration (ex: 'audio', 'stt', etc.)
            values: Dictionnaire des nouvelles valeurs
        """
        if section not in self.config_data:
            self.config_data[section] = {}
        self.config_data[section].update(values)


# Instance singleton de configuration
_config_instance = None

def get_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Récupère l'instance singleton de configuration
    
    Args:
        config_path: Chemin vers le fichier de configuration YAML.
                     Si None, utilise le fichier de configuration par défaut.
                     
    Returns:
        L'instance singleton de configuration
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance 