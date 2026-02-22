#!/usr/bin/env python3
"""
VGA Sphere Verilator Simulation Runner
=======================================

This script builds and runs Verilog simulations using Verilator instead of Icarus Verilog.
Verilator compiles to C++ and is significantly faster (10-100x) than Icarus.

Prerequisites:
- Verilator: https://verilator.org/guide/latest/install.html
- Python 3.8+
- Pillow (pip install Pillow)
- C++ compiler (MSVC on Windows, GCC/Clang on Linux/Mac)

Installation:
    Windows (with Chocolatey): choco install verilator
    Windows (with vcpkg): vcpkg install verilator
    Linux (Ubuntu/Debian): sudo apt-get install verilator
    macOS (Homebrew): brew install verilator

Usage:
    python run_verilator.py --check      # Check if tools are installed
    python run_verilator.py --install    # Show installation instructions
    python run_verilator.py --build      # Build the Verilog simulation
    python run_verilator.py --run        # Run simulation and capture frames
    python run_verilator.py              # Do all of the above
    
    # Advanced options:
    python run_verilator.py --frames 60  # Capture 60 frames instead of default 40
    python run_verilator.py --trace      # Enable VCD waveform tracing (slower)
    python run_verilator.py --optimize   # Enable aggressive optimizations
"""

import os
import sys
import subprocess
import shutil
import argparse
import time
import platform

# Paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_DIR, 'src')
TEST_DIR = os.path.join(PROJECT_DIR, 'test')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')
BUILD_DIR = os.path.join(PROJECT_DIR, 'build', 'verilator')

# VGA timing
H_DISPLAY = 640
H_TOTAL = 800
V_DISPLAY = 480
V_TOTAL = 525

# Default simulation parameters
DEFAULT_NUM_FRAMES = 40


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
        'verilator': ('Verilator HDL simulator', 'Required'),
        'gtkwave': ('Waveform viewer', 'Optional'),
    }
    
    all_ok = True
    for tool, (desc, req) in tools.items():
        path = check_tool(tool)
        if path:
            # Get version info
            try:
                result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                version = result.stdout.split('\n')[0] if result.stdout else ''
                print(f"  [OK] {tool}: {path}")
                if version:
                    print(f"       {version}")
            except:
                print(f"  [OK] {tool}: {path}")
        else:
            status = "MISSING" if req == 'Required' else "not found"
            print(f"  [{'!!' if req == 'Required' else '--'}] {tool}: {status} ({desc})")
            if req == 'Required':
                all_ok = False
    
    # Check for C++ compiler
    print("\n=== Checking C++ Compiler ===\n")
    cpp_compilers = ['g++', 'clang++', 'cl.exe']
    cpp_found = False
    for compiler in cpp_compilers:
        if check_tool(compiler, '--version' if compiler != 'cl.exe' else ''):
            print(f"  [OK] C++ compiler: {compiler}")
            cpp_found = True
            break
    
    if not cpp_found:
        print("  [!!] C++ compiler: MISSING (Required for Verilator)")
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
    """Show installation instructions based on platform"""
    system = platform.system()
    
    print(f"""
=== Installation Instructions for {system} ===

1. VERILATOR (Required)
""")
    
    if system == "Windows":
        print("""   Option A - Chocolatey (Recommended):
     choco install verilator
   
   Option B - vcpkg:
     vcpkg install verilator
   
   Option C - Manual:
     Download from: https://verilator.org/guide/latest/install.html
     Follow Windows installation guide
   
   Note: You'll also need Visual Studio or MinGW for C++ compilation
""")
    elif system == "Linux":
        print("""   Ubuntu/Debian:
     sudo apt-get update
     sudo apt-get install verilator
   
   Fedora/RHEL:
     sudo dnf install verilator
   
   Or build from source:
     git clone https://github.com/verilator/verilator
     cd verilator
     autoconf && ./configure && make && sudo make install
""")
    elif system == "Darwin":  # macOS
        print("""   Homebrew:
     brew install verilator
   
   MacPorts:
     sudo port install verilator
""")
    
    print("""
2. PILLOW (Required for frame capture)
   pip install Pillow

3. GTKWAVE (Optional, for viewing waveforms)
""")
    
    if system == "Windows":
        print("   choco install gtkwave")
    elif system == "Linux":
        print("   sudo apt-get install gtkwave")
    elif system == "Darwin":
        print("   brew install gtkwave")
    
    print("""
After installation, restart your terminal and run:
   python run_verilator.py --check
""")


def create_verilator_testbench(num_frames=DEFAULT_NUM_FRAMES, enable_trace=False):
    """Create a C++ testbench for Verilator"""
    os.makedirs(BUILD_DIR, exist_ok=True)
    
    # Create Verilog wrapper module
    wrapper_v = '''`timescale 1ns / 1ps

// Wrapper module for Verilator testbench
module vga_sphere_wrapper (
    input wire clk,
    input wire rst_n,
    output wire hsync,
    output wire vsync,
    output wire [1:0] r_out,
    output wire [1:0] g_out,
    output wire [1:0] b_out
);

    // Instantiate the actual VGA sphere module
    vga_sphere dut (
        .clk(clk),
        .rst_n(rst_n),
        .hsync(hsync),
        .vsync(vsync),
        .r_out(r_out),
        .g_out(g_out),
        .b_out(b_out)
    );

endmodule
'''
    
    wrapper_path = os.path.join(BUILD_DIR, 'vga_sphere_wrapper.v')
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_v)
    
    # Create C++ testbench
    cpp_content = f'''// Verilator C++ testbench for VGA Sphere
#include "Vvga_sphere_wrapper.h"
#include "verilated.h"
{"#include <verilated_vcd_c.h>" if enable_trace else ""}
#include <iostream>
#include <fstream>
#include <vector>

// VGA timing constants
const int H_DISPLAY = {H_DISPLAY};
const int H_TOTAL = {H_TOTAL};
const int V_DISPLAY = {V_DISPLAY};
const int V_TOTAL = {V_TOTAL};
const int NUM_FRAMES = {num_frames};

// Extend 2-bit color to 8-bit
inline unsigned char extend_2bit(unsigned char val) {{
    val &= 0x3;
    return (val << 6) | (val << 4) | (val << 2) | val;
}}

int main(int argc, char** argv) {{
    Verilated::commandArgs(argc, argv);
    
    // Create instance
    Vvga_sphere_wrapper* top = new Vvga_sphere_wrapper;
    
    {"// Enable tracing" if enable_trace else ""}
    {"VerilatedVcdC* tfp = nullptr;" if enable_trace else ""}
    {"if (Verilated::commandArgs().find(\"--trace\") != std::string::npos) {" if enable_trace else ""}
    {"    Verilated::traceEverOn(true);" if enable_trace else ""}
    {"    tfp = new VerilatedVcdC;" if enable_trace else ""}
    {"    top->trace(tfp, 99);" if enable_trace else ""}
    {"    tfp->open(\"vga_sphere.vcd\");" if enable_trace else ""}
    {"    std::cout << \"VCD tracing enabled: vga_sphere.vcd\" << std::endl;" if enable_trace else ""}
    {"}" if enable_trace else ""}
    
    // Open output file
    std::ofstream outfile("vga_output.raw", std::ios::binary);
    if (!outfile) {{
        std::cerr << "ERROR: Could not open output file" << std::endl;
        return 1;
    }}
    
    std::cout << "Starting Verilator VGA simulation..." << std::endl;
    std::cout << "Capturing " << NUM_FRAMES << " frames at " 
              << H_DISPLAY << "x" << V_DISPLAY << std::endl;
    
    // Initialize
    top->clk = 0;
    top->rst_n = 0;
    
    // Reset sequence
    for (int i = 0; i < 10; i++) {{
        top->clk = 0;
        top->eval();
        {"if (tfp) tfp->dump(2*i);" if enable_trace else ""}
        top->clk = 1;
        top->eval();
        {"if (tfp) tfp->dump(2*i + 1);" if enable_trace else ""}
    }}
    
    top->rst_n = 1;
    
    // Simulation loop
    int h_count = 0;
    int v_count = 0;
    int frame_count = 0;
    unsigned long long sim_time = 0;
    
    std::vector<unsigned char> frame_buffer;
    frame_buffer.reserve(H_DISPLAY * V_DISPLAY * 3);
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    while (frame_count < NUM_FRAMES) {{
        // Clock low
        top->clk = 0;
        top->eval();
        {"if (tfp) tfp->dump(sim_time++);" if enable_trace else ""}
        
        // Clock high
        top->clk = 1;
        top->eval();
        {"if (tfp) tfp->dump(sim_time++);" if enable_trace else ""}
        
        // Capture pixel if in visible area
        if (h_count < H_DISPLAY && v_count < V_DISPLAY) {{
            unsigned char r = extend_2bit(top->r_out);
            unsigned char g = extend_2bit(top->g_out);
            unsigned char b = extend_2bit(top->b_out);
            
            frame_buffer.push_back(r);
            frame_buffer.push_back(g);
            frame_buffer.push_back(b);
        }}
        
        // Update counters
        h_count++;
        if (h_count >= H_TOTAL) {{
            h_count = 0;
            v_count++;
            if (v_count >= V_TOTAL) {{
                v_count = 0;
                frame_count++;
                
                // Write frame to file
                outfile.write(reinterpret_cast<const char*>(frame_buffer.data()), 
                            frame_buffer.size());
                frame_buffer.clear();
                
                std::cout << "Frame " << frame_count << "/" << NUM_FRAMES 
                         << " complete" << std::endl;
            }}
        }}
    }}
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_time - start_time).count();
    
    std::cout << "\\nSimulation completed in " << (duration / 1000.0) 
              << " seconds" << std::endl;
    std::cout << "Performance: " << (sim_time / (duration / 1000.0) / 1e6) 
              << " MHz simulation rate" << std::endl;
    
    // Cleanup
    {"if (tfp) {" if enable_trace else ""}
    {"    tfp->close();" if enable_trace else ""}
    {"    delete tfp;" if enable_trace else ""}
    {"}" if enable_trace else ""}
    outfile.close();
    delete top;
    
    std::cout << "Output written to vga_output.raw" << std::endl;
    return 0;
}}
'''
    
    cpp_path = os.path.join(BUILD_DIR, 'tb_verilator.cpp')
    with open(cpp_path, 'w') as f:
        f.write(cpp_content)
    
    print(f"Created Verilator testbench:")
    print(f"  Verilog wrapper: {wrapper_path}")
    print(f"  C++ testbench: {cpp_path}")
    
    return wrapper_path, cpp_path


def build_simulation(enable_trace=False, optimize=False):
    """Build the Verilog simulation with Verilator"""
    print("\n=== Building with Verilator ===\n")
    
    os.makedirs(BUILD_DIR, exist_ok=True)
    
    # Create testbench files
    wrapper_path, cpp_path = create_verilator_testbench(enable_trace=enable_trace)
    
    # Collect Verilog source files
    verilog_sources = [
        os.path.join(SRC_DIR, 'vga_sphere.v'),
        os.path.join(SRC_DIR, 'sphere_core.v'),
        os.path.join(SRC_DIR, 'ray_sphere.v'),
        os.path.join(SRC_DIR, 'vec_rotate2.v'),
        os.path.join(SRC_DIR, 'vec_rotate3.v'),
        os.path.join(SRC_DIR, 'dist_scale3d.v'),
        wrapper_path
    ]
    
    # Check all files exist
    for src in verilog_sources:
        if not os.path.exists(src):
            print(f"ERROR: Source file not found: {src}")
            return False
    
    # Build Verilator command
    cmd = [
        'verilator',
        '--cc',  # Generate C++ output
        '--exe',  # Create executable
        '--build',  # Build the executable
        '-Wall',  # Enable warnings
        '--top-module', 'vga_sphere_wrapper',
        '-I' + SRC_DIR,
        '--Mdir', BUILD_DIR,
    ]
    
    # Add optimization flags
    if optimize:
        cmd.extend([
            '-O3',  # Aggressive optimization
            '--x-assign', 'fast',
            '--x-initial', 'fast',
            '--noassert',
        ])
        print("Optimization: ENABLED (O3)")
    else:
        cmd.extend(['-O2'])  # Standard optimization
        print("Optimization: Standard (O2)")
    
    # Add tracing if requested
    if enable_trace:
        cmd.append('--trace')
        print("VCD Tracing: ENABLED (will be slower)")
    else:
        print("VCD Tracing: DISABLED")
    
    # Add source files
    cmd.extend(verilog_sources)
    cmd.append(cpp_path)
    
    print(f"\nRunning Verilator...")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("BUILD FAILED!")
        print(result.stderr)
        return False
    
    if result.stderr:
        print("Build output:")
        print(result.stderr)
    
    # Find the executable
    exe_name = 'Vvga_sphere_wrapper.exe' if platform.system() == 'Windows' else 'Vvga_sphere_wrapper'
    exe_path = os.path.join(BUILD_DIR, exe_name)
    
    if os.path.exists(exe_path):
        print(f"\n✓ Build successful: {exe_path}")
        return True
    else:
        print(f"\nERROR: Executable not found at {exe_path}")
        return False


def run_simulation():
    """Run the Verilator simulation"""
    print("\n=== Running Verilator Simulation ===\n")
    
    exe_name = 'Vvga_sphere_wrapper.exe' if platform.system() == 'Windows' else 'Vvga_sphere_wrapper'
    exe_path = os.path.join(BUILD_DIR, exe_name)
    
    if not os.path.exists(exe_path):
        print("ERROR: Simulation not built. Run with --build first.")
        return False
    
    # Change to build directory for output file
    old_cwd = os.getcwd()
    os.chdir(BUILD_DIR)
    
    try:
        cmd = [f'./{exe_name}' if platform.system() != 'Windows' else exe_name]
        print(f"Running: {' '.join(cmd)}")
        print("This should be much faster than Icarus Verilog...\n")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode != 0:
            print("SIMULATION FAILED!")
            return False
        
        print(f"\n✓ Simulation completed in {elapsed:.2f} seconds")
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
    
    # Create timestamped output directory
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    frames_dir = os.path.join(OUTPUT_DIR, 'frames', f'sphere_verilator_{timestamp}')
    gifs_dir = os.path.join(OUTPUT_DIR, 'gifs')
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(gifs_dir, exist_ok=True)
    
    # Read raw file
    with open(raw_file, 'rb') as f:
        data = f.read()
    
    frame_size = H_DISPLAY * V_DISPLAY * 3
    num_frames = len(data) // frame_size
    
    print(f"Found {num_frames} frames in raw data")
    print(f"Output directory: {frames_dir}\n")
    
    images = []
    for i in range(num_frames):
        start = i * frame_size
        end = start + frame_size
        frame_data = data[start:end]
        
        img = Image.frombytes('RGB', (H_DISPLAY, V_DISPLAY), frame_data)
        filename = os.path.join(frames_dir, f'frame_{i:04d}.png')
        img.save(filename)
        images.append(img)
        print(f"  Saved frame {i}: {filename}")
    
    # Create GIFs
    if images:
        gif_path = os.path.join(gifs_dir, f'sphere_verilator_{timestamp}.gif')
        gif_latest = os.path.join(gifs_dir, 'sphere_verilator_latest.gif')
        
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=50,
            loop=0
        )
        print(f"\n✓ Created GIF: {gif_path}")
        
        # Copy to latest
        shutil.copy2(gif_path, gif_latest)
        print(f"✓ Updated: {gif_latest}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='VGA Sphere Verilator Simulation Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_verilator.py                    # Build and run with defaults
  python run_verilator.py --optimize         # Enable aggressive optimizations
  python run_verilator.py --trace            # Enable VCD waveform tracing
  python run_verilator.py --frames 100       # Capture 100 frames
        """
    )
    
    parser.add_argument('--check', action='store_true', 
                       help='Check if tools are installed')
    parser.add_argument('--install', action='store_true', 
                       help='Show installation instructions')
    parser.add_argument('--build', action='store_true', 
                       help='Build the simulation')
    parser.add_argument('--run', action='store_true', 
                       help='Run simulation')
    parser.add_argument('--convert', action='store_true', 
                       help='Convert raw output to frames')
    parser.add_argument('--frames', type=int, default=DEFAULT_NUM_FRAMES,
                       help=f'Number of frames to capture (default: {DEFAULT_NUM_FRAMES})')
    parser.add_argument('--trace', action='store_true',
                       help='Enable VCD waveform tracing (slower)')
    parser.add_argument('--optimize', action='store_true',
                       help='Enable aggressive optimizations (O3)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  VGA Sphere - Verilator Simulation Runner")
    print("  (10-100x faster than Icarus Verilog)")
    print("=" * 60)
    
    # If no specific action, do everything
    do_all = not (args.check or args.install or args.build or args.run or args.convert)
    
    if args.install:
        show_install_instructions()
        return
    
    if args.check or do_all:
        if not check_tools():
            print("\n[!!] Some required tools are missing.")
            print("     Run: python run_verilator.py --install")
            if do_all:
                sys.exit(1)
            return
    
    if args.build or do_all:
        if not build_simulation(enable_trace=args.trace, optimize=args.optimize):
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
    
    print("\n" + "=" * 60)
    print("  ✓ Done!")
    print("=" * 60)
    print(f"\nView results in: {os.path.join(OUTPUT_DIR, 'gifs')}")
    print("\nSpeed comparison:")
    print("  - Icarus Verilog: ~30-60 seconds for 40 frames")
    print("  - Verilator: ~1-5 seconds for 40 frames (10-60x faster!)")


if __name__ == '__main__':
    main()
