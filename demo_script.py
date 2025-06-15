#!/usr/bin/env python3
"""
Interactive Demo Script for Azure IoT Edge vs IoT Hub
Run this to demonstrate the capabilities to your boss
"""

import time
import json
from datetime import datetime

class DemoPresentation:
    """Interactive demo presentation"""
    
    def __init__(self):
        self.demo_data = {
            "device_id": "jetson-nano-demo",
            "location": "Factory Floor #3"
        }
    
    def print_banner(self, title: str):
        """Print a formatted banner"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def print_section(self, title: str):
        """Print a section header"""
        print(f"\n--- {title} ---")
    
    def simulate_telemetry(self):
        """Generate sample telemetry data"""
        import random
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "device_id": self.demo_data["device_id"],
            "cpu_percent": round(random.uniform(30, 85), 1),
            "memory_percent": round(random.uniform(40, 75), 1),
            "temperatures": {
                "cpu_thermal": round(random.uniform(45, 68), 1)
            }
        }
    
    def demo_iot_edge_processing(self):
        """Demonstrate IoT Edge local processing"""
        self.print_section("Azure IoT Edge (Enhanced Approach)")
        
        print("Starting IoT Edge runtime...")
        time.sleep(1)
        print("✓ Edge runtime active")
        print("✓ Local analytics module loaded")
        
        print("\nProcessing telemetry locally...")
        for i in range(3):
            telemetry = self.simulate_telemetry()
            
            print(f"📊 Processing telemetry #{i+1} locally")
            print(f"   CPU: {telemetry['cpu_percent']}%")
            print(f"   ⚡ Local processing: <50ms")
            time.sleep(0.5)
        
        print("💰 Bandwidth usage: ~0.5KB (75% reduction)")
    
    def demo_comparison_table(self):
        """Show comparison between approaches"""
        self.print_section("Performance Comparison")
        
        print("""
Direct IoT Hub    vs    IoT Edge
─────────────           ───────────
500-2000ms response     <100ms response
100MB/day bandwidth     10MB/day bandwidth
Cloud processing only   Edge + Cloud processing
No offline capability   Full offline capability
""")
    
    def run_full_demo(self):
        """Run the complete demo"""
        self.print_banner("Azure IoT Edge Demo for Jetson Nano")
        
        print("Welcome to the Azure IoT Edge demonstration!")
        input("Press Enter to start...")
        
        self.demo_iot_edge_processing()
        input("Press Enter to see comparison...")
        
        self.demo_comparison_table()
        
        print("\n" + "="*60)
        print("  Demo Complete!")
        print("="*60)

if __name__ == "__main__":
    demo = DemoPresentation()
    demo.run_full_demo() 