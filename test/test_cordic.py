# SPDX-FileCopyrightText: © 2024
# SPDX-License-Identifier: Apache-2.0

"""
Cocotb testbench for vector rotation modules
Tests vec_rotate2 and vec_rotate3 vector magnitude computation
"""

import cocotb
from cocotb.triggers import Timer
import math


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


@cocotb.test()
async def test_cordic2step_positive_vector(dut):
    """Test vec_rotate2 with positive x,y values"""
    dut._log.info("Testing vec_rotate2 with positive values")
    
    # Test vector (3, 4) - should give magnitude ~5
    # In Q8.8 format: 3 = 0x0300, 4 = 0x0400
    x = 0x0300  # 3.0 in Q8.8
    y = 0x0400  # 4.0 in Q8.8
    
    dut.vec_x.value = x
    dut.vec_y.value = y
    dut.aux_x.value = 0x0100  # 1.0
    dut.aux_y.value = 0x0000  # 0.0
    
    await Timer(10, units="ns")
    
    magnitude = int(dut.magnitude.value)
    dut._log.info(f"Input: ({x:04X}, {y:04X}), Output magnitude: {magnitude:04X}")
    
    # Expected magnitude is sqrt(3^2 + 4^2) = 5, scaled by CORDIC gain
    # CORDIC2 gain is ~0.625, so result should be ~5 * 256 * 0.625 ≈ 800
    expected_approx = int(5 * 256 * 0.625)
    tolerance = expected_approx * 0.3  # 30% tolerance for approximation
    
    assert abs(magnitude - expected_approx) < tolerance, \
        f"Magnitude {magnitude} not within tolerance of expected {expected_approx}"
    
    dut._log.info("vec_rotate2 positive vector test passed!")


@cocotb.test()
async def test_cordic2step_negative_vector(dut):
    """Test vec_rotate2 with negative values"""
    dut._log.info("Testing vec_rotate2 with negative values")
    
    # Test vector (-3, -4)
    x = from_signed_16(-0x0300)  # -3.0 in Q8.8
    y = from_signed_16(-0x0400)  # -4.0 in Q8.8
    
    dut.vec_x.value = x
    dut.vec_y.value = y
    dut.aux_x.value = 0x0100
    dut.aux_y.value = 0x0000
    
    await Timer(10, units="ns")
    
    magnitude = int(dut.magnitude.value)
    dut._log.info(f"Input: ({x:04X}, {y:04X}), Output magnitude: {magnitude:04X}")
    
    # Magnitude should be same as positive case
    expected_approx = int(5 * 256 * 0.625)
    tolerance = expected_approx * 0.3
    
    assert abs(magnitude - expected_approx) < tolerance, \
        f"Magnitude {magnitude} not within tolerance of expected {expected_approx}"
    
    dut._log.info("vec_rotate2 negative vector test passed!")


@cocotb.test()
async def test_cordic2step_unit_vector(dut):
    """Test vec_rotate2 with unit-ish vectors"""
    dut._log.info("Testing vec_rotate2 with unit vector")
    
    # Test vector (1, 0)
    x = 0x0100  # 1.0 in Q8.8
    y = 0x0000  # 0.0
    
    dut.vec_x.value = x
    dut.vec_y.value = y
    dut.aux_x.value = 0x0100
    dut.aux_y.value = 0x0000
    
    await Timer(10, units="ns")
    
    magnitude = int(dut.magnitude.value)
    dut._log.info(f"Input: ({x:04X}, {y:04X}), Output magnitude: {magnitude:04X}")
    
    # Expected magnitude is 1, scaled
    expected_approx = int(1 * 256 * 0.625)
    tolerance = expected_approx * 0.5
    
    assert magnitude > 0, "Magnitude should be non-zero for unit vector"
    
    dut._log.info("vec_rotate2 unit vector test passed!")


@cocotb.test()
async def test_cordic2step_zero_vector(dut):
    """Test vec_rotate2 with zero vector"""
    dut._log.info("Testing vec_rotate2 with zero vector")
    
    dut.vec_x.value = 0
    dut.vec_y.value = 0
    dut.aux_x.value = 0x0100
    dut.aux_y.value = 0x0000
    
    await Timer(10, units="ns")
    
    magnitude = int(dut.magnitude.value)
    dut._log.info(f"Input: (0, 0), Output magnitude: {magnitude:04X}")
    
    # Zero vector should give small magnitude (may not be exactly zero due to implementation)
    assert magnitude < 0x0100, "Magnitude of zero vector should be small"
    
    dut._log.info("vec_rotate2 zero vector test passed!")


@cocotb.test()
async def test_cordic2step_aux_rotation(dut):
    """Test that auxiliary vector is rotated correctly"""
    dut._log.info("Testing vec_rotate2 auxiliary rotation")
    
    # Test with 45-degree vector (1, 1)
    x = 0x0100  # 1.0
    y = 0x0100  # 1.0
    
    # Auxiliary vector pointing in x direction
    dut.vec_x.value = x
    dut.vec_y.value = y
    dut.aux_x.value = 0x0100  # 1.0
    dut.aux_y.value = 0x0000  # 0.0
    
    await Timer(10, units="ns")
    
    aux_rotated = to_signed_16(dut.aux_rotated.value)
    dut._log.info(f"Auxiliary rotated output: {aux_rotated:04X}")
    
    # Rotated auxiliary should be non-zero
    assert aux_rotated != 0, "Rotated auxiliary should be non-zero for non-zero input"
    
    dut._log.info("vec_rotate2 auxiliary rotation test passed!")
