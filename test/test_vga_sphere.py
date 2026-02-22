# SPDX-FileCopyrightText: © 2024 
# SPDX-License-Identifier: Apache-2.0

"""
Cocotb testbench for VGA Sphere ray marcher
Captures VGA frames and saves them as images
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
import os

# Try to import PIL for PNG output
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# VGA timing parameters
H_DISPLAY = 640
H_TOTAL = 800
V_DISPLAY = 480
V_TOTAL = 525


def extend_2bit_to_8bit(val):
    """Extend 2-bit color to 8-bit"""
    val = int(val) & 0x3
    return (val << 6) | (val << 4) | (val << 2) | val


def save_frame(filename, pixels, width, height):
    """Save frame as image"""
    if HAS_PIL:
        img = Image.frombytes('RGB', (width, height), bytes(pixels))
        img.save(filename)
    else:
        # Fallback to PPM
        ppm_name = filename.replace('.png', '.ppm')
        with open(ppm_name, 'wb') as f:
            f.write(f"P6\n{width} {height}\n255\n".encode())
            f.write(bytes(pixels))
        filename = ppm_name
    return filename


@cocotb.test()
async def test_vga_sphere_frames(dut):
    """Capture multiple frames from VGA sphere renderer"""
    dut._log.info("Starting VGA Sphere frame capture test")
    
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up clock (25 MHz for standard VGA timing)
    clock = Clock(dut.clk, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock.start())
    
    # Reset
    dut._log.info("Resetting design...")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 10)
    
    num_frames = 5  # Number of frames to capture
    
    for frame_num in range(num_frames):
        dut._log.info(f"Capturing frame {frame_num + 1}/{num_frames}...")
        
        pixels = []
        
        # Capture one complete frame
        for v in range(V_TOTAL):
            for h in range(H_TOTAL):
                await RisingEdge(dut.clk)
                
                # Capture pixel if in visible area
                if h < H_DISPLAY and v < V_DISPLAY:
                    try:
                        r = extend_2bit_to_8bit(dut.r_out.value)
                        g = extend_2bit_to_8bit(dut.g_out.value)
                        b = extend_2bit_to_8bit(dut.b_out.value)
                    except:
                        r, g, b = 0, 0, 0
                    pixels.extend([r, g, b])
        
        # Save frame
        if len(pixels) == H_DISPLAY * V_DISPLAY * 3:
            filename = os.path.join(output_dir, f"frame_{frame_num:04d}.png")
            saved_as = save_frame(filename, pixels, H_DISPLAY, V_DISPLAY)
            dut._log.info(f"Saved: {saved_as}")
        else:
            dut._log.warning(f"Incomplete frame: {len(pixels)} bytes")
    
    dut._log.info(f"Captured {num_frames} frames to {output_dir}/")


@cocotb.test()
async def test_vga_signals(dut):
    """Basic test to verify VGA signal generation"""
    dut._log.info("Testing VGA signal generation")
    
    # Set up clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 100)
    
    # Check that hsync and vsync are toggling
    hsync_values = []
    vsync_values = []
    
    for _ in range(H_TOTAL * 2):  # Two complete lines
        await RisingEdge(dut.clk)
        try:
            hsync_values.append(int(dut.hsync.value))
        except:
            hsync_values.append(0)
    
    # Count transitions
    hsync_transitions = sum(1 for i in range(len(hsync_values)-1) 
                           if hsync_values[i] != hsync_values[i+1])
    
    dut._log.info(f"HSYNC transitions in 2 lines: {hsync_transitions}")
    
    # Should have at least 2 transitions per line (going low and high)
    assert hsync_transitions >= 2, "HSYNC should be toggling"
    
    dut._log.info("✓ VGA signals test passed!")


@cocotb.test()
async def test_sphere_rendering(dut):
    """Test that sphere is being rendered (pixels vary)"""
    dut._log.info("Testing sphere rendering")
    
    # Set up clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    
    # Wait for first frame to start
    await ClockCycles(dut.clk, H_TOTAL * V_TOTAL)
    
    # Capture some pixels from center of screen
    pixels = set()
    center_y = V_DISPLAY // 2
    
    # Skip to center line
    await ClockCycles(dut.clk, H_TOTAL * center_y)
    
    for h in range(H_DISPLAY):
        await RisingEdge(dut.clk)
        try:
            r = int(dut.r_out.value) & 0x3
            g = int(dut.g_out.value) & 0x3
            b = int(dut.b_out.value) & 0x3
            pixels.add((r, g, b))
        except:
            pass
    
    dut._log.info(f"Unique colors in center line: {len(pixels)}")
    dut._log.info(f"Colors: {list(pixels)[:10]}...")  # Show first 10
    
    # Should have more than one color (sphere + background)
    assert len(pixels) > 1, "Should have multiple colors (sphere rendering)"
    
    dut._log.info("✓ Sphere rendering test passed!")
