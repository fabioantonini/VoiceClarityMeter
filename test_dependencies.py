#!/usr/bin/env python3
"""
Test script per verificare le dipendenze di VoIP Quality Monitor
"""

import sys
import subprocess

def test_python_version():
    """Verifica versione Python"""
    print(f"Python version: {sys.version}")
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 11:
        print("✓ Python 3.11+ installato correttamente")
        return True
    else:
        print("✗ Richiede Python 3.11 o superiore")
        return False

def test_module_import(module_name, package_name=None):
    """Testa l'importazione di un modulo"""
    try:
        __import__(module_name)
        print(f"✓ {package_name or module_name} disponibile")
        return True
    except ImportError as e:
        print(f"✗ {package_name or module_name} non disponibile: {e}")
        return False

def test_specific_imports():
    """Testa importazioni specifiche per l'applicazione"""
    tests = [
        ("flask", "Flask"),
        ("flask_socketio", "Flask-SocketIO"),
        ("flask_login", "Flask-Login"), 
        ("cryptography", "Cryptography"),
        ("numpy", "NumPy"),
        ("threading", "Threading (builtin)"),
        ("socket", "Socket (builtin)"),
        ("ssl", "SSL (builtin)"),
        ("json", "JSON (builtin)"),
        ("datetime", "DateTime (builtin)")
    ]
    
    success_count = 0
    for module, name in tests:
        if test_module_import(module, name):
            success_count += 1
    
    return success_count, len(tests)

def test_flask_app():
    """Testa l'importazione dei moduli dell'applicazione"""
    try:
        # Test importazioni moduli applicazione
        import certificate_manager
        import call_manager
        import mos_calculator
        import sip_registrar
        import config_helper
        print("✓ Tutti i moduli dell'applicazione sono importabili")
        return True
    except ImportError as e:
        print(f"✗ Errore importazione moduli applicazione: {e}")
        return False

def main():
    print("=" * 50)
    print("Test Dipendenze VoIP Quality Monitor")
    print("=" * 50)
    
    # Test Python version
    if not test_python_version():
        sys.exit(1)
    
    print()
    
    # Test module imports
    success, total = test_specific_imports()
    print(f"\nModuli testati: {success}/{total}")
    
    print()
    
    # Test applicazione
    test_flask_app()
    
    print("\n" + "=" * 50)
    if success == total:
        print("✓ Tutti i test superati! L'applicazione dovrebbe funzionare.")
        print("\nPer avviare l'applicazione:")
        print("python app_simple.py")
    else:
        print("✗ Alcuni test falliti. Installa le dipendenze mancanti:")
        print("pip install -r requirements-local.txt")
    print("=" * 50)

if __name__ == "__main__":
    main()