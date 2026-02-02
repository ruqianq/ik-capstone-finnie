#!/usr/bin/env python3
"""
Test script for FinnIE API.
Run this script to test the FinnIE system after deployment.
"""
import sys
import requests
import json
from typing import Dict, Any


# API endpoint
API_BASE_URL = "http://localhost:8000"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def test_health() -> bool:
    """Test the health endpoint."""
    print_header("Testing Health Endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        result = response.json()
        print(f"✓ Health check passed")
        print(f"  Status: {result.get('status')}")
        print(f"  Observability: {result.get('observability')}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_list_agents() -> bool:
    """Test listing available agents."""
    print_header("Testing List Agents Endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/agents")
        response.raise_for_status()
        result = response.json()
        agents = result.get('agents', [])
        print(f"✓ Found {len(agents)} specialist agents:")
        for agent in agents:
            print(f"  - {agent.get('name')}: {agent.get('description')}")
        orchestrator = result.get('orchestrator', {})
        print(f"\n✓ Orchestrator: {orchestrator.get('name')}")
        return True
    except Exception as e:
        print(f"✗ List agents failed: {e}")
        return False


def test_query(query: str, user_id: str = "test_user") -> bool:
    """Test sending a query to the API."""
    print_header(f"Testing Query: {query[:50]}...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={
                "query": query,
                "user_id": user_id
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✓ Query processed successfully")
        print(f"  Routed to: {result.get('routed_to')}")
        print(f"  Reasoning: {result.get('reasoning')}")
        print(f"\n  Response:")
        response_text = result.get('response', '')
        # Print response with word wrap
        words = response_text.split()
        line = "    "
        for word in words:
            if len(line) + len(word) + 1 > 70:
                print(line)
                line = "    " + word
            else:
                line += " " + word if line != "    " else word
        if line.strip():
            print(line)
        
        return True
    except Exception as e:
        print(f"✗ Query failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  Error detail: {error_detail}")
            except:
                print(f"  Response text: {e.response.text}")
        return False


def run_all_tests() -> None:
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  FinnIE API Test Suite")
    print("=" * 70)
    print(f"\nTesting API at: {API_BASE_URL}")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    # Test 2: List agents
    results.append(("List Agents", test_list_agents()))
    
    # Test 3: Budget query
    results.append((
        "Budget Query",
        test_query("I make $5000 per month. How should I allocate my budget?")
    ))
    
    # Test 4: Investment query
    results.append((
        "Investment Query",
        test_query("I want to start investing $500 per month. What should I consider?")
    ))
    
    # Test 5: Debt management query
    results.append((
        "Debt Management Query",
        test_query("I have $10,000 in credit card debt. What's the best repayment strategy?")
    ))
    
    # Test 6: Financial planning query
    results.append((
        "Financial Planning Query",
        test_query("I'm 30 years old and want to retire at 60. How should I plan?")
    ))
    
    # Print summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! FinnIE is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
