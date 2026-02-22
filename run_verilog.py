#!/usr/bin/env python3
"""
VGA Sphere Verilog Simulation Runner
=====================================

This script builds and runs the actual Verilog simulation using Icarus Verilog,
then captures VGA frames from the simulation output.

Prerequisites:
- Icarus Verilog (iverilog, vvp): http://bleyer.org/icarus/
- Python 3.8+
- Pillow (pip install Pillow)

Usage:
    python run_verilog.py --check      # Check if tools are installed
    python run_verilog.py --install    # Show installation instructions
    python run_verilog.py --build      # Build the Verilog simulation
    python run_verilog.py --run        # Run simulation and capture frames
    python run_verilog.py              # Do all of the above
"""

import os
import sys
import subprocess
import shutil
import argparse
import struct
import time

# Paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_DIR, 'src')
TEST_DIR = os.path.join(PROJECT_DIR, 'test')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')
BUILD_DIR = os.path.join(PROJECT_DIR, 'build')

# VGA timing
H_DISPLAY = 640
H_TOTAL = 800
V_DISPLAY = 480
V_TOTAL = 525

# Verilog source files for sphere renderer
SPHERE_SOURCES = [
    'vgasphere.v',
    'sphere.v',
    'spherehit.v',
    'cordic2step.v',
    'cordic3step.v',
    'step3vec.v',
]


def check_tool(name, test_arg='--version'):
    """Check if a tool is installed and return its path"""
    path = shutil.which(name)
    if path:
        try:
            result = subprocess.run([path, test_arg], capture_output=True, text=True, timeout=5)
            return path
        except:
            return path
    return None


def check_tools():
    """Check all required tools"""
    print("=== Checking Required Tools ===\n")
    
    tools = {
        'iverilog': ('Icarus Verilog compiler', 'Required'),
        'vvp': ('Icarus Verilog simulator', 'Required'),
        'gtkwave': ('Waveform viewer', 'Optional'),
    }
    
    all_ok = True
    for tool, (desc, req) in tools.items():
        path = check_tool(tool)
        if path:
            print(f"  [OK] {tool}: {path}")
        else:
            status = "MISSING" if req == 'Required' else "not found"
            print(f"  [{'!!' if req == 'Required' else '--'}] {tool}: {status} ({desc})")
            if req == 'Required':
                all_ok = False
    
    # Check Python packages
    print("\n=== Checking Python Packages ===\n")
    
    try:
        from PIL import Image
        print("  [OK] Pillow (PIL)")
    except ImportError:
        print("  [!!] Pillow: MISSING (pip install Pillow)")
        all_ok = False
    
    return all_ok


def show_install_instructions():
    """Show installation instructions for Windows"""
    print("""
=== Installation Instructions for Windows ===

1. ICARUS VERILOG (Required)
   - Download from: http://bleyer.org/icarus/
   - Or use Chocolatey: choco install iverilog
   - After install, add to PATH:
     C:\\iverilog\\bin (or wherever you installed it)

2. PILLOW (Required for frame capture)
   - Run: pip install Pillow

3. GTKWAVE (Optional, for viewing waveforms)
   - Download from: http://gtkwave.sourceforge.net/
   - Or use Chocolatey: choco install gtkwave

After installation, restart your terminal and run:
   python run_verilog.py --check

""")


def create_verilog_testbench():
    """Create a Verilog testbench that outputs VGA data to a file"""
    os.makedirs(BUILD_DIR, exist_ok=True)
    
    tb_content = '''`timescale 1ns / 1ps

// Testbench for VGA Sphere - outputs pixel data to file
module tb_vgasphere_capture;

    // Parameters
    parameter H_DISPLAY = 640;
    parameter H_TOTAL = 800;
    parameter V_DISPLAY = 480;
    parameter V_TOTAL = 525;
    parameter NUM_FRAMES = 40;
    
    // Clock and reset
    reg clk;
    reg rst_n;
    
    // VGA outputs
    wire hsync, vsync;
    wire [1:0] r_out, g_out, b_out;
    
    // Counters
    integer h_count, v_count, frame_count;
    integer pixel_file;
    
    // Instantiate DUT
    vgasphere dut (
        .clk(clk),
        .rst_n(rst_n),
        .hsync(hsync),
        .vsync(vsync),
        .r_out(r_out),
        .g_out(g_out),
        .b_out(b_out)
    );
    
    // Clock generation (25 MHz = 40ns period)
    initial begin
        clk = 0;
        forever #20 clk = ~clk;
    end
    
    // Main test
    initial begin
        // Open output file
        pixel_file = $fopen("vga_output.raw", "wb");
        if (pixel_file == 0) begin
            $display("ERROR: Could not open output file");
            $finish;
        end
        
        // Initialize
        rst_n = 0;
        h_count = 0;
        v_count = 0;
        frame_count = 0;
        
        // Reset
        #100;
        rst_n = 1;
        $display("Starting VGA capture simulation...");
        $display("Capturing %0d frames at %0dx%0d", NUM_FRAMES, H_DISPLAY, V_DISPLAY);
        
        // Run simulation
        while (frame_count < NUM_FRAMES) begin
            @(posedge clk);
            
            // Write pixel if in visible area
            if (h_count < H_DISPLAY && v_count < V_DISPLAY) begin
                // Write R, G, B as bytes (2-bit extended to 8-bit)
                $fwrite(pixel_file, "%c%c%c", 
                    {r_out, r_out, r_out, r_out},
                    {g_out, g_out, g_out, g_out},
                    {b_out, b_out, b_out, b_out});
            end
            
            // Update counters
            h_count = h_count + 1;
            if (h_count >= H_TOTAL) begin
                h_count = 0;
                v_count = v_count + 1;
                if (v_count >= V_TOTAL) begin
                    v_count = 0;
                    frame_count = frame_count + 1;
                    $display("Frame %0d/%0d complete", frame_count, NUM_FRAMES);
                end
            end
        end
        
        $fclose(pixel_file);
        $display("Simulation complete! Output written to vga_output.raw");
        $finish;
    end

endmodule
'''
    
    tb_path = os.path.join(BUILD_DIR, 'tb_capture.v')
    with open(tb_path, 'w') as f:
        f.write(tb_content)
    
    print(f"Created testbench: {tb_path}")
    return tb_path


def build_simulation():
    """Build the Verilog simulation"""
    print("\n=== Building Verilog Simulation ===\n")
    
    os.makedirs(BUILD_DIR, exist_ok=True)
    
    # Create testbench
    tb_path = create_verilog_testbench()
    
    # Collect source files
    sources = [os.path.join(SRC_DIR, f) for f in SPHERE_SOURCES]
    sources.append(tb_path)
    
    # Check all files exist
    for src in sources:
        if not os.path.exists(src):
            print(f"ERROR: Source file not found: {src}")
            return False
    
    # Build with iverilog
    output_file = os.path.join(BUILD_DIR, 'vgasphere.vvp')
    cmd = ['iverilog', '-o', output_file, '-I', SRC_DIR] + sources
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("BUILD FAILED!")
        print(result.stderr)
        return False
    
    if result.stderr:
        print("Warnings:")
        print(result.stderr)
    
    print(f"Build successful: {output_file}")
    return True


def run_simulation():
    """Run the Verilog simulation"""
    print("\n=== Running Verilog Simulation ===\n")
    
    vvp_file = os.path.join(BUILD_DIR, 'vgasphere.vvp')
    if not os.path.exists(vvp_file):
        print("ERROR: Simulation not built. Run with --build first.")
        return False
    
    # Change to build directory for output file
    old_cwd = os.getcwd()
    os.chdir(BUILD_DIR)
    
    try:
        cmd = ['vvp', 'vgasphere.vvp']
        print(f"Running: {' '.join(cmd)}")
        print("This may take a few minutes...")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode != 0:
            print("SIMULATION FAILED!")
            return False
        
        print(f"\nSimulation completed in {elapsed:.1f} seconds")
        return True
        
    finally:
        os.chdir(old_cwd)


def convert_raw_to_frames():
    """Convert raw VGA output to PNG frames"""
    print("\n=== Converting to PNG Frames ===\n")
    
    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow not installed. Run: pip install Pillow")
        return False
    
    raw_file = os.path.join(BUILD_DIR, 'vga_output.raw')
    if not os.path.exists(raw_file):
        print(f"ERROR: Raw output not found: {raw_file}")
        return False
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Read raw file
    with open(raw_file, 'rb') as f:
        data = f.read()
    
    frame_size = H_DISPLAY * V_DISPLAY * 3
    num_frames = len(data) // frame_size
    
    print(f"Found {num_frames} frames in raw data")
    
    images = []
    for i in range(num_frames):
        start = i * frame_size
        end = start + frame_size
        frame_data = data[start:end]
        
        img = Image.frombytes('RGB', (H_DISPLAY, V_DISPLAY), frame_data)
        filename = os.path.join(OUTPUT_DIR, f'frame_{i:04d}.png')
        img.save(filename)
        images.append(img)
        print(f"  Saved frame {i}: {filename}")
    
    # Create GIF
    if images:
        gif_path = os.path.join(OUTPUT_DIR, 'sphere_verilog.gif')
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=50,
            loop=0
        )
        print(f"\nCreated GIF: {gif_path}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='VGA Sphere Verilog Simulation Runner')
    parser.add_argument('--check', action='store_true', help='Check if tools are installed')
    parser.add_argument('--install', action='store_true', help='Show installation instructions')
    parser.add_argument('--build', action='store_true', help='Build the simulation')
    parser.add_argument('--run', action='store_true', help='Run simulation')
    parser.add_argument('--convert', action='store_true', help='Convert raw output to frames')
    args = parser.parse_args()
    
    print("=" * 50)
    print("  VGA Sphere - Verilog Simulation Runner")
    print("=" * 50)
    
    # If no specific action, do everything
    do_all = not (args.check or args.install or args.build or args.run or args.convert)
    
    if args.install:
        show_install_instructions()
        return
    
    if args.check or do_all:
        if not check_tools():
            print("\n[!!] Some required tools are missing.")
            print("     Run: python run_verilog.py --install")
            if do_all:
                sys.exit(1)
            return
    
    if args.build or do_all:
        if not build_simulation():
            print("\n[!!] Build failed!")
            sys.exit(1)
    
    if args.run or do_all:
        if not run_simulation():
            print("\n[!!] Simulation failed!")
            sys.exit(1)
    
    if args.convert or do_all:
        if not convert_raw_to_frames():
            print("\n[!!] Frame conversion failed!")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("  Done!")
    print("=" * 50)
    print(f"\nView results: {os.path.join(OUTPUT_DIR, 'viewer.html')}")


if __name__ == '__main__':
    main()
