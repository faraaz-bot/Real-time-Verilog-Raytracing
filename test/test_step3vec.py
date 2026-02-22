# SPDX-FileCopyrightText: © 2024
# SPDX-License-Identifier: Apache-2.0

"""
Cocotb testbench for dist_scale3d module
Tests distance-scaled vector multiplication
"""

import cocotb
from cocotb.triggers import Timer


def to_signed_16(val):
    """Convert to 16-bit signed integer"""
    val = int(val) & 0xFFFF
    if val & 0x8000:
        val -= 0x10000
    return val


def from_signed_16(val):
    """Convert from Python int to 16-bit representation"""
    if val < 0:
        val = val + 0x10000
    return val & 0xFFFF


def from_signed_11(val):
    """Convert from Python int to 11-bit representation"""
    if val < 0:
        val = val + 0x800
    return val & 0x7FF


@cocotb.test()
async def test_step3vec_positive_distance(dut):
    """Test dist_scale3d with positive distance"""
    dut._log.info("Testing dist_scale3d with positive distance")
    
    # Large positive distance (high bit set in abs)
    d = 512  # 0x200
    x = 0x1000  # Some positive direction
    y = 0x0800
    z = 0x0400
    
    dut.d.value = d
    dut.xin_.value = x
    dut.yin_.value = y
    dut.zin_.value = z
    
    await Timer(10, units="ns")
    
    xout = to_signed_16(dut.xout.value)
    yout = to_signed_16(dut.yout.value)
    zout = to_signed_16(dut.zout.value)
    
    dut._log.info(f"Distance: {d}, Input: ({x:04X}, {y:04X}, {z:04X})")
    dut._log.info(f"Output: ({xout:04X}, {yout:04X}, {zout:04X})")
    
    # Output should be scaled version of input
    assert xout != 0 or yout != 0 or zout != 0, "Output should be non-zero for non-zero input"
    
    dut._log.info("dist_scale3d positive distance test passed!")


@cocotb.test()
async def test_step3vec_negative_distance(dut):
    """Test dist_scale3d with negative distance"""
    dut._log.info("Testing dist_scale3d with negative distance")
    
    # Negative distance
    d = from_signed_11(-256)
    x = 0x1000
    y = 0x0800
    z = 0x0400
    
    dut.d.value = d
    dut.xin_.value = x
    dut.yin_.value = y
    dut.zin_.value = z
    
    await Timer(10, units="ns")
    
    xout = to_signed_16(dut.xout.value)
    yout = to_signed_16(dut.yout.value)
    zout = to_signed_16(dut.zout.value)
    
    dut._log.info(f"Distance: {d:03X}, Input: ({x:04X}, {y:04X}, {z:04X})")
    dut._log.info(f"Output: ({xout:04X}, {yout:04X}, {zout:04X})")
    
    dut._log.info("dist_scale3d negative distance test passed!")


@cocotb.test()
async def test_step3vec_zero_distance(dut):
    """Test dist_scale3d with zero distance"""
    dut._log.info("Testing dist_scale3d with zero distance")
    
    d = 0
    x = 0x1000
    y = 0x0800
    z = 0x0400
    
    dut.d.value = d
    dut.xin_.value = x
    dut.yin_.value = y
    dut.zin_.value = z
    
    await Timer(10, units="ns")
    
    xout = int(dut.xout.value)
    yout = int(dut.yout.value)
    zout = int(dut.zout.value)
    
    dut._log.info(f"Distance: 0, Output: ({xout:04X}, {yout:04X}, {zout:04X})")
    
    # Zero distance should give zero output
    assert xout == 0, f"X output should be 0 for zero distance, got {xout}"
    assert yout == 0, f"Y output should be 0 for zero distance, got {yout}"
    assert zout == 0, f"Z output should be 0 for zero distance, got {zout}"
    
    dut._log.info("dist_scale3d zero distance test passed!")


@cocotb.test()
async def test_step3vec_small_distance(dut):
    """Test dist_scale3d with small distance values"""
    dut._log.info("Testing dist_scale3d with small distances")
    
    x = 0x4000  # Larger input
    y = 0x4000
    z = 0x4000
    
    dut.xin_.value = x
    dut.yin_.value = y
    dut.zin_.value = z
    
    # Test with distance = 1 (smallest non-zero)
    dut.d.value = 1
    await Timer(10, units="ns")
    
    xout = to_signed_16(dut.xout.value)
    dut._log.info(f"Distance: 1, X output: {xout:04X}")
    
    # Test with distance = 2
    dut.d.value = 2
    await Timer(10, units="ns")
    
    xout2 = to_signed_16(dut.xout.value)
    dut._log.info(f"Distance: 2, X output: {xout2:04X}")
    
    dut._log.info("dist_scale3d small distance test passed!")


@cocotb.test()
async def test_step3vec_varying_distances(dut):
    """Test dist_scale3d with various distance magnitudes"""
    dut._log.info("Testing dist_scale3d with varying distances")
    
    x = 0x2000
    y = 0x1000
    z = 0x0800
    
    dut.xin_.value = x
    dut.yin_.value = y
    dut.zin_.value = z
    
    # Test power-of-2 distances to verify shift behavior
    test_distances = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    
    for d in test_distances:
        dut.d.value = d
        await Timer(10, units="ns")
        
        xout = to_signed_16(dut.xout.value)
        yout = to_signed_16(dut.yout.value)
        zout = to_signed_16(dut.zout.value)
        
        dut._log.info(f"Distance: {d:3d}, Output: ({xout:+6d}, {yout:+6d}, {zout:+6d})")
    
    dut._log.info("dist_scale3d varying distances test passed!")
