#!/usr/bin/env python3
"""
Test script per verificare il calcolo MOS e debugging del sistema
"""

from mos_calculator import MOSCalculator
from call_manager import CallManager
import json

def test_mos_calculation():
    """Test del calcolo MOS con parametri diversi"""
    print("=== TEST CALCOLO MOS ===")
    
    mos_calc = MOSCalculator()
    
    # Test con parametri diversi
    test_cases = [
        {"packet_loss": 0, "jitter": 5, "delay": 50, "codec": "G.711", "desc": "Qualità ottima"},
        {"packet_loss": 5, "jitter": 10, "delay": 100, "codec": "G.711", "desc": "Qualità buona"},
        {"packet_loss": 10, "jitter": 20, "delay": 150, "codec": "G.729", "desc": "Qualità media"},
        {"packet_loss": 20, "jitter": 50, "delay": 300, "codec": "G.711", "desc": "Qualità scarsa"},
        {"packet_loss": 0, "jitter": 0, "delay": 20, "codec": "G.729", "desc": "Qualità perfetta G.729"}
    ]
    
    for i, test in enumerate(test_cases, 1):
        mos_score = mos_calc.calculate_mos(
            packet_loss_rate=test["packet_loss"],
            jitter=test["jitter"],
            delay=test["delay"],
            codec=test["codec"]
        )
        
        quality = mos_calc.calculate_quality_category(mos_score)
        
        print(f"\nTest {i}: {test['desc']}")
        print(f"  Parametri: Loss={test['packet_loss']}%, Jitter={test['jitter']}ms, Delay={test['delay']}ms, Codec={test['codec']}")
        print(f"  MOS Score: {mos_score}")
        print(f"  Qualità: {quality}")

def test_call_manager_stats():
    """Test delle statistiche del Call Manager"""
    print("\n=== TEST CALL MANAGER STATS ===")
    
    call_manager = CallManager()
    
    # Simula alcune chiamate per testare le statistiche
    test_calls = [
        {
            "call_id": "test-001",
            "start_time": "2025-06-26T12:00:00",
            "end_time": "2025-06-26T12:05:00",
            "duration": 300,
            "avg_mos": 4.2,
            "packet_loss_rate": 2.5,
            "avg_jitter": 8.0
        },
        {
            "call_id": "test-002", 
            "start_time": "2025-06-26T12:10:00",
            "end_time": "2025-06-26T12:15:00", 
            "duration": 300,
            "avg_mos": 3.8,
            "packet_loss_rate": 5.0,
            "avg_jitter": 15.0
        }
    ]
    
    # Aggiungi chiamate di test alla cronologia
    call_manager.call_history = test_calls
    
    stats = call_manager.get_summary_stats()
    
    print("Statistiche Call Manager:")
    print(f"  Total calls: {stats['total_calls']}")
    print(f"  Active calls: {stats['active_calls']}")
    if stats.get('last_24h'):
        print(f"  Last 24h calls: {stats['last_24h']['call_count']}")
        print(f"  Last 24h avg MOS: {stats['last_24h']['avg_mos']:.2f}")
        print(f"  Last 24h avg packet loss: {stats['last_24h']['avg_packet_loss']:.2f}%")

if __name__ == "__main__":
    test_mos_calculation()
    test_call_manager_stats()
    print("\n=== TEST COMPLETATO ===")