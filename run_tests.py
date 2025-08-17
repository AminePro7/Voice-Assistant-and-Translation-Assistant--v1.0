"""
run_tests.py - Script de lancement des tests pour l'Assistant Vocal
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
import json
import time

# Ajouter le répertoire racine au path Python
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

class TestRunner:
    """Gestionnaire de lancement des tests"""
    
    def __init__(self):
        self.root_dir = ROOT_DIR
        self.tests_dir = self.root_dir / "tests"
        self.results = {}
        
    def check_dependencies(self):
        """Vérifie que les dépendances de test sont installées"""
        print("Verification des dependances de test...")
        
        required_packages = [
            'pytest',
            'pytest-cov',
            'pytest-mock',
            'unittest',
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"[OK] {package}")
            except ImportError:
                print(f"[MISSING] {package}")
                missing.append(package)
        
        if missing:
            print(f"\nPackages manquants: {', '.join(missing)}")
            print(f"Installez-les avec: pip install {' '.join(missing)}")
            return False
        
        print("[OK] Toutes les dependances sont installees\n")
        return True
    
    def run_unit_tests(self, verbose=False, specific_file=None):
        """Lance les tests unitaires"""
        print("\n" + "="*60)
        print("TESTS UNITAIRES")
        print("="*60)
        
        if specific_file:
            test_path = self.tests_dir / "test_unit" / specific_file
            if not test_path.exists():
                print(f"[ERROR] Fichier non trouve: {test_path}")
                return False
        else:
            test_path = self.tests_dir / "test_unit"
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v" if verbose else "",
            "--tb=short",
            "-p", "no:warnings"  # Supprimer les warnings
        ]
        
        # Filtrer les arguments vides
        cmd = [arg for arg in cmd if arg]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=str(self.root_dir))
        elapsed = time.time() - start_time
        
        self.results['unit'] = {
            'success': result.returncode == 0,
            'time': elapsed
        }
        
        print(f"\nTemps d'execution: {elapsed:.2f}s")
        return result.returncode == 0
    
    def run_integration_tests(self, verbose=False):
        """Lance les tests d'intégration"""
        print("\n" + "="*60)
        print("TESTS D'INTEGRATION")
        print("="*60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "test_integration"),
            "-v" if verbose else "",
            "--tb=short",
            "-p", "no:warnings"
        ]
        
        cmd = [arg for arg in cmd if arg]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=str(self.root_dir))
        elapsed = time.time() - start_time
        
        self.results['integration'] = {
            'success': result.returncode == 0,
            'time': elapsed
        }
        
        print(f"\nTemps d'execution: {elapsed:.2f}s")
        return result.returncode == 0
    
    def run_performance_tests(self, verbose=False):
        """Lance les tests de performance"""
        print("\n" + "="*60)
        print("TESTS DE PERFORMANCE")
        print("="*60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "test_performance"),
            "-v" if verbose else "",
            "--tb=short",
            "-p", "no:warnings"
        ]
        
        cmd = [arg for arg in cmd if arg]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=str(self.root_dir))
        elapsed = time.time() - start_time
        
        self.results['performance'] = {
            'success': result.returncode == 0,
            'time': elapsed
        }
        
        print(f"\nTemps d'execution: {elapsed:.2f}s")
        return result.returncode == 0
    
    def run_e2e_tests(self, verbose=False):
        """Lance les tests end-to-end"""
        print("\n" + "="*60)
        print("TESTS END-TO-END")
        print("="*60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "test_e2e"),
            "-v" if verbose else "",
            "--tb=short",
            "-p", "no:warnings"
        ]
        
        cmd = [arg for arg in cmd if arg]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=str(self.root_dir))
        elapsed = time.time() - start_time
        
        self.results['e2e'] = {
            'success': result.returncode == 0,
            'time': elapsed
        }
        
        print(f"\nTemps d'execution: {elapsed:.2f}s")
        return result.returncode == 0
    
    def run_with_coverage(self):
        """Lance tous les tests avec rapport de couverture"""
        print("\n" + "="*60)
        print("TESTS AVEC COUVERTURE DE CODE")
        print("="*60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "--cov=voice_assistant",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--tb=short",
            "-p", "no:warnings"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=str(self.root_dir))
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print("\n[OK] Rapport de couverture HTML genere dans: htmlcov/index.html")
        
        print(f"\nTemps total: {elapsed:.2f}s")
        return result.returncode == 0
    
    def run_specific_test(self, test_name, verbose=True):
        """Lance un test spécifique"""
        print(f"\nLancement du test: {test_name}")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "-k", test_name,
            "-v" if verbose else "",
            "--tb=short",
            "-p", "no:warnings"
        ]
        
        result = subprocess.run(cmd, cwd=str(self.root_dir))
        return result.returncode == 0
    
    def run_all_tests(self, verbose=False):
        """Lance tous les tests"""
        print("\n" + "="*70)
        print("LANCEMENT DE TOUS LES TESTS")
        print("="*70)
        
        all_success = True
        
        # Tests unitaires
        if not self.run_unit_tests(verbose):
            all_success = False
        
        # Tests d'intégration
        if not self.run_integration_tests(verbose):
            all_success = False
        
        # Tests de performance
        if not self.run_performance_tests(verbose):
            all_success = False
        
        # Tests E2E
        if not self.run_e2e_tests(verbose):
            all_success = False
        
        # Résumé
        self.print_summary()
        
        return all_success
    
    def print_summary(self):
        """Affiche un résumé des résultats"""
        print("\n" + "="*70)
        print("RESUME DES TESTS")
        print("="*70)
        
        total_time = 0
        for test_type, result in self.results.items():
            status = "[OK] SUCCES" if result['success'] else "[ERROR] ECHEC"
            print(f"{test_type.upper():15} {status:10} ({result['time']:.2f}s)")
            total_time += result['time']
        
        print("-"*70)
        print(f"{'TOTAL':15} {'':10} ({total_time:.2f}s)")
        
        # Statistiques globales
        success_count = sum(1 for r in self.results.values() if r['success'])
        total_count = len(self.results)
        
        print(f"\nTaux de réussite: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            print("\n[OK] TOUS LES TESTS SONT PASSES AVEC SUCCES!")
        else:
            print(f"\n[WARNING] {total_count - success_count} type(s) de tests ont echoue")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Lanceur de tests pour l'Assistant Vocal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python run_tests.py --all              # Lance tous les tests
  python run_tests.py --unit             # Lance seulement les tests unitaires
  python run_tests.py --unit test_rag.py # Lance un fichier de test spécifique
  python run_tests.py --coverage         # Lance avec rapport de couverture
  python run_tests.py -k test_translation # Lance les tests contenant 'translation'
  python run_tests.py --check            # Vérifie les dépendances
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Lance tous les tests')
    parser.add_argument('--unit', nargs='?', const=True, default=False,
                       help='Lance les tests unitaires (optionnel: nom du fichier)')
    parser.add_argument('--integration', action='store_true',
                       help='Lance les tests d\'intégration')
    parser.add_argument('--performance', action='store_true',
                       help='Lance les tests de performance')
    parser.add_argument('--e2e', action='store_true',
                       help='Lance les tests end-to-end')
    parser.add_argument('--coverage', action='store_true',
                       help='Lance tous les tests avec rapport de couverture')
    parser.add_argument('-k', '--keyword', type=str,
                       help='Lance les tests contenant ce mot-clé')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Mode verbose')
    parser.add_argument('--check', action='store_true',
                       help='Vérifie les dépendances de test')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Si aucun argument, afficher l'aide
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    # Vérification des dépendances
    if args.check:
        return 0 if runner.check_dependencies() else 1
    
    # Toujours vérifier les dépendances avant de lancer les tests
    if not runner.check_dependencies():
        return 1
    
    # Lancement des tests selon les options
    success = True
    
    if args.coverage:
        success = runner.run_with_coverage()
    elif args.all:
        success = runner.run_all_tests(args.verbose)
    elif args.keyword:
        success = runner.run_specific_test(args.keyword, args.verbose)
    else:
        if args.unit:
            if isinstance(args.unit, str):
                success = runner.run_unit_tests(args.verbose, args.unit)
            else:
                success = runner.run_unit_tests(args.verbose)
        
        if args.integration:
            success = success and runner.run_integration_tests(args.verbose)
        
        if args.performance:
            success = success and runner.run_performance_tests(args.verbose)
        
        if args.e2e:
            success = success and runner.run_e2e_tests(args.verbose)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
