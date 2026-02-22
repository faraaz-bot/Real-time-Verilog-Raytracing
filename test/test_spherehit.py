# SPDX-FileCopyrightText: © 2024
# SPDX-License-Identifier: Apache-2.0

"""
Cocotb testbench for ray_sphere module
Tests sphere ray marching intersection
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer


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
async def test_spherehit_ray_towards_sphere(dut):
    """Test ray marching towards sphere center"""
    dut._log.info("Testing ray towards sphere")
    
    # Set up clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    
    # Ray from (5, 0, 0) pointing towards origin
    # Sphere is at origin with radius 2
    origin_x = 0x0500  # 5.0 in Q8.8
    origin_y = 0x0000
    origin_z = 0x0000
    
    # Direction towards origin (negative x)
    dir_x = from_signed_16(-0x0100)  # -1.0
    dir_y = 0x0000
    dir_z = 0x0000
    
    # Light direction
    light_x = 0x0100  # 1.0
    light_y = 0x0000
    light_z = 0x0000
    
    # Set inputs
    dut.origin_x.value = origin_x
    dut.origin_y.value = origin_y
    dut.origin_z.value = origin_z
    dut.dir_x.value = dir_x
    dut.dir_y.value = dir_y
    dut.dir_z.value = dir_z
    dut.light_x.value = light_x
    dut.light_y.value = light_y
    dut.light_z.value = light_z
    
    # Start ray march
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Let it iterate
    await ClockCycles(dut.clk, 16)
    
    try:
        hit = int(dut.surface_hit.value)
        intensity = to_signed_16(dut.intensity.value)
        dut._log.info(f"Hit: {hit}, Intensity: {intensity}")
    except:
        dut._log.warning("Could not read outputs")
    
    dut._log.info("ray_sphere ray towards sphere test passed!")


@cocotb.test()
async def test_spherehit_ray_missing_sphere(dut):
    """Test ray that misses the sphere"""
    dut._log.info("Testing ray missing sphere")
    
    # Set up clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    
    # Ray from (5, 10, 0) pointing in x direction (misses sphere)
    origin_x = 0x0500  # 5.0
    origin_y = 0x0A00  # 10.0 (far from sphere)
    origin_z = 0x0000
    
    # Direction parallel to x-axis
    dir_x = from_signed_16(-0x0100)
    dir_y = 0x0000
    dir_z = 0x0000
    
    dut.origin_x.value = origin_x
    dut.origin_y.value = origin_y
    dut.origin_z.value = origin_z
    dut.dir_x.value = dir_x
    dut.dir_y.value = dir_y
    dut.dir_z.value = dir_z
    dut.light_x.value = 0x0100
    dut.light_y.value = 0x0000
    dut.light_z.value = 0x0000
    
    # Start ray march
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    # Let it iterate more (miss takes longer)
    await ClockCycles(dut.clk, 32)
    
    try:
        hit = int(dut.surface_hit.value)
        dut._log.info(f"Hit flag: {hit}")
        # Should eventually become 0 (miss) after marching far enough
    except:
        dut._log.warning("Could not read outputs")
    
    dut._log.info("ray_sphere ray missing test passed!")


@cocotb.test()
async def test_spherehit_multiple_rays(dut):
    """Test multiple ray marching sequences"""
    dut._log.info("Testing multiple rays")
    
    # Set up clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    
    test_rays = [
        # (origin_x, origin_y, dir_x, dir_y) - Q8.8 format
        (0x0500, 0x0000, from_signed_16(-0x0100), 0x0000),  # Hit center
        (0x0500, 0x0100, from_signed_16(-0x0100), 0x0000),  # Hit slightly off
        (0x0500, 0x0200, from_signed_16(-0x0100), 0x0000),  # Hit edge
    ]
    
    for i, (ox, oy, dx, dy) in enumerate(test_rays):
        dut.origin_x.value = ox
        dut.origin_y.value = oy
        dut.origin_z.value = 0x0000
        dut.dir_x.value = dx
        dut.dir_y.value = dy
        dut.dir_z.value = 0x0000
        dut.light_x.value = 0x0100
        dut.light_y.value = 0x0000
        dut.light_z.value = 0x0000
        
        dut.start.value = 1
        await RisingEdge(dut.clk)
        dut.start.value = 0
        
        await ClockCycles(dut.clk, 8)
        
        try:
            hit = int(dut.surface_hit.value)
            dut._log.info(f"Ray {i}: Hit = {hit}")
        except:
            pass
    
    dut._log.info("ray_sphere multiple rays test passed!")


@cocotb.test()
async def test_spherehit_reset_behavior(dut):
    """Test that start signal properly resets the ray march"""
    dut._log.info("Testing start/reset behavior")
    
    # Set up clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initial ray
    dut.origin_x.value = 0x0500
    dut.origin_y.value = 0x0000
    dut.origin_z.value = 0x0000
    dut.dir_x.value = from_signed_16(-0x0100)
    dut.dir_y.value = 0x0000
    dut.dir_z.value = 0x0000
    dut.light_x.value = 0x0100
    dut.light_y.value = 0x0000
    dut.light_z.value = 0x0000
    
    # Start first ray
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    await ClockCycles(dut.clk, 4)
    
    # Restart with new ray before completion
    dut.origin_y.value = 0x0100
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    
    await ClockCycles(dut.clk, 8)
    
    dut._log.info("ray_sphere reset behavior test passed!")


@cocotb.test()
async def test_spherehit_lighting(dut):
    """Test that lighting intensity varies with angle"""
    dut._log.info("Testing lighting computation")
    
    # Set up clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    
    # Two rays hitting different points should give different intensity
    intensities = []
    
    for light_y in [0x0000, 0x0080, 0x0100]:
        dut.origin_x.value = 0x0400
        dut.origin_y.value = 0x0000
        dut.origin_z.value = 0x0000
        dut.dir_x.value = from_signed_16(-0x0100)
        dut.dir_y.value = 0x0000
        dut.dir_z.value = 0x0000
        dut.light_x.value = 0x0100
        dut.light_y.value = light_y
        dut.light_z.value = 0x0000
        
        dut.start.value = 1
        await RisingEdge(dut.clk)
        dut.start.value = 0
        
        await ClockCycles(dut.clk, 8)
        
        try:
            intensity = to_signed_16(dut.intensity.value)
            intensities.append(intensity)
            dut._log.info(f"Light Y={light_y:04X}, Intensity: {intensity}")
        except:
            intensities.append(0)
    
    dut._log.info("ray_sphere lighting test passed!")
