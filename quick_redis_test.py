#!/usr/bin/env python3
"""
Quick Redis Test - Immediate Results
"""

import os
import socket
from dotenv import load_dotenv

load_dotenv(override=True)

def test_hostname_resolution():
    """Test if the hostname resolves."""
    hostname = "managed-managed-redis.eastus2.redis.azure.net"
    
    print(f"🔍 Testing hostname resolution: {hostname}")
    
    try:
        # Test DNS resolution
        ip = socket.gethostbyname(hostname)
        print(f"✅ Hostname resolves to: {ip}")
        return True, ip
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {e}")
        return False, None

def test_port_connectivity(hostname, port):
    """Test if we can connect to the port."""
    print(f"🔍 Testing port connectivity: {hostname}:{port}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is reachable")
            return True
        else:
            print(f"❌ Port {port} is not reachable (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Port test failed: {e}")
        return False

def main():
    print("🔍 Quick Redis Connectivity Test")
    print("=" * 40)
    
    # Test hostname resolution
    hostname_ok, ip = test_hostname_resolution()
    
    if hostname_ok:
        # Test common Redis ports
        ports_to_test = [6380, 10000, 6379]
        for port in ports_to_test:
            port_ok = test_port_connectivity(ip, port)
            if port_ok:
                print(f"✅ Found working port: {port}")
                break
    
    print("\n📋 Current Redis configuration:")
    redis_url = os.environ.get('REDIS_URL', 'NOT SET')
    print(f"REDIS_URL: {redis_url}")

if __name__ == "__main__":
    main()
