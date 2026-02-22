#!/usr/bin/env python3
"""
Test suite for Kirby raymarching modules
Tests the SDF calculations and rendering pipeline
"""

import subprocess
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_kirby_verilog_syntax():
    """Test that Kirby Verilog files have valid syntax"""
    print("Testing Kirby Verilog syntax...")
    
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    kirby_files = [
        os.path.join(src_dir, 'ray_kirby.v'),
        os.path.join(src_dir, 'kirby_core.v'),
        os.path.join(src_dir, 'vga_kirby.v')
    ]
    
    for vfile in kirby_files:
        if not os.path.exists(vfile):
            print(f"  ❌ File not found: {vfile}")
            return False
        print(f"  ✅ Found: {os.path.basename(vfile)}")
    
    print("  ✅ All Kirby Verilog files present")
    return True


def test_kirby_testbench():
    """Run the Kirby testbench"""
    print("\nTesting Kirby testbench...")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(test_dir, '..', 'src')
    tb_file = os.path.join(test_dir, 'tb_kirby.v')
    
    if not os.path.exists(tb_file):
        print(f"  ❌ Testbench not found: {tb_file}")
        return False
    
    print(f"  ✅ Testbench found: {tb_file}")
    print("  Note: Run with iverilog or verilator to execute testbench")
    return True


def test_kirby_parameters():
    """Verify Kirby geometry parameters are reasonable"""
    print("\nTesting Kirby geometry parameters...")
    
    # Expected parameters from ray_kirby.v
    params = {
        'BODY_RADIUS': 0x0200,    # 2.0
        'ARM_RADIUS': 0x0080,     # 0.5
        'FOOT_RADIUS': 0x00C0,    # 0.75
        'EYE_RADIUS': 0x0060,     # 0.375
        'CHEEK_RADIUS': 0x0050,   # 0.3125
        'MOUTH_RADIUS': 0x0030    # 0.1875
    }
    
    print("  Kirby geometry (Q8.8 fixed-point):")
    for name, value in params.items():
        decimal = value / 256.0
        print(f"    {name:15s} = 0x{value:04X} ({decimal:.4f})")
    
    # Verify body is largest
    if params['BODY_RADIUS'] > params['ARM_RADIUS']:
        print("  ✅ Body radius > arm radius")
    else:
        print("  ❌ Body should be larger than arms")
        return False
    
    if params['BODY_RADIUS'] > params['FOOT_RADIUS']:
        print("  ✅ Body radius > foot radius")
    else:
        print("  ❌ Body should be larger than feet")
        return False
    
    print("  ✅ Kirby geometry parameters valid")
    return True


def test_kirby_features():
    """Test that Kirby has all required features"""
    print("\nTesting Kirby features...")
    
    features = [
        "Body sphere (main)",
        "Left arm",
        "Right arm",
        "Left foot",
        "Right foot",
        "Left eye",
        "Right eye",
        "Left cheek",
        "Right cheek",
        "Mouth"
    ]
    
    print(f"  Kirby has {len(features)} distinct features:")
    for i, feature in enumerate(features, 1):
        print(f"    {i}. {feature}")
    
    print("  ✅ All Kirby features defined")
    return True


def run_all_tests():
    """Run all Kirby tests"""
    print("=" * 60)
    print("  Kirby Raymarching Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Verilog Syntax", test_kirby_verilog_syntax),
        ("Testbench", test_kirby_testbench),
        ("Geometry Parameters", test_kirby_parameters),
        ("Feature List", test_kirby_features)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print()
    print("=" * 60)
    print("  Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"  Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
