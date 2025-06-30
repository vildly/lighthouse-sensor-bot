#!/usr/bin/env python3
"""
Simple script to test that Python and Pandas tools are properly integrated
Run this to verify the enhanced agent is working correctly
"""

import sys
import requests
from pathlib import Path

def test_tools_endpoint():
    """Test the /test-tools endpoint"""
    try:
        response = requests.get("http://localhost:5001/api/test-tools", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Tools Integration Test Results:")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Tools Count: {data.get('tools_count')}")
            print(f"   Tool Types: {data.get('tool_types')}")
            print(f"   DuckDB Tools: {'✅' if data.get('duck_tools') else '❌'}")
            print(f"   Python Tools: {'✅' if data.get('python_tools') else '❌'}")
            print(f"   Pandas Tools: {'✅' if data.get('pandas_tools') else '❌'}")
            print(f"   Agent Initialized: {'✅' if data.get('agent_initialized') else '❌'}")
            
            if data.get('status') == 'success':
                print("\n🎉 All tools are working correctly!")
                return True
            else:
                print(f"\n⚠️  Partial success or issues detected")
                if 'agent_error' in data:
                    print(f"   Agent Error: {data['agent_error']}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure Docker containers are running:")
        print("   docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_basic_connectivity():
    """Test basic backend connectivity"""
    try:
        response = requests.get("http://localhost:5001/api/test", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"❌ Backend responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connectivity test failed: {e}")
        return False

def main():
    print("🔧 Testing Enhanced Agent with Python and Pandas Tools")
    print("=" * 60)
    
    # Test basic connectivity first
    if not test_basic_connectivity():
        print("\n💡 Make sure your backend is running with: docker-compose up -d")
        sys.exit(1)
    
    print()
    
    # Test tools integration
    if test_tools_endpoint():
        print("\n✅ All tests passed! Your enhanced agent is ready to use.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 