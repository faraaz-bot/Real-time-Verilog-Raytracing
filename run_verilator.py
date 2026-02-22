#!/usr/bin/env python3
"""
VGA Sphere Ray Marcher - Interactive Simulation Runner (Verilator Edition)
===========================================================================

Features:
- Interactive menu for selecting simulation type
- Multiple frame count options (5/10/30/140)
- Detailed completion report with statistics
- Local server to display results
- 10-100x faster than Icarus Verilog using Verilator

Prerequisites:
- Verilator: https://verilator.org/guide/latest/install.html
- Python 3.8+
- Pillow (pip install Pillow)
- C++ compiler (g++/clang++)
"""

import os
import sys
import subprocess
import shutil
import time
import platform
import http.server
import socketserver
import webbrowser
from datetime import datetime

# Paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
BUILD_DIR = os.path.join(ROOT_DIR, 'build', 'verilator')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')

# VGA timing constants
H_DISPLAY = 640
V_DISPLAY = 480
H_TOTAL = 800
V_TOTAL = 525
PIXEL_CLOCK_MHZ = 25.175

# Source files for each version
SOURCES_SPHERE = ['vga_sphere.v', 'sphere_core.v', 'ray_sphere.v', 'vec_rotate2.v', 'vec_rotate3.v', 'dist_scale3d.v']
SOURCES_FLOOR = ['vga_scene_sphere.v', 'scene_sphere.v', 'sphere_core.v', 'ray_sphere.v', 'vec_rotate2.v', 'vec_rotate3.v', 'dist_scale3d.v']
SOURCES_COIN = ['vga_scene_coin.v', 'scene_coin.v', 'coin_core.v', 'ray_coin.v', 'vec_rotate2.v', 'vec_rotate3.v', 'dist_scale3d.v']
SOURCES_CUBE = ['vga_cube.v', 'cube_core.v', 'ray_cube.v', 'vec_rotate2.v', 'vec_rotate3.v']
SOURCES_KIRBY = ['vga_kirby.v', 'kirby_core.v', 'ray_kirby.v', 'dist_scale3d.v']


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    print("=" * 60)
    print("  🌐 VGA Sphere Ray Marcher - Interactive Runner")
    print("=" * 60)
    print()


def check_tools():
    """Check for required tools"""
    tools = {'verilator': False, 'g++': False, 'pillow': False}
    
    if shutil.which('verilator'):
        tools['verilator'] = True
    if shutil.which('g++') or shutil.which('clang++') or shutil.which('cl.exe'):
        tools['g++'] = True
    try:
        from PIL import Image
        tools['pillow'] = True
    except ImportError:
        pass
    
    return tools


def display_menu():
    """Display interactive menu and get user choice"""
    tools = check_tools()
    
    print("📋 Available Simulations:")
    print()
    print("  [1] Sphere Only (blue background)")
    print("  [2] Sphere + Checkerboard Floor")
    print("  [3] Mario Coin + Floor (golden coin)")
    print("  [4] Rotating Cube (orange cube)")
    print("  [5] Kirby (NEW - pink with features)")
    print()
    print("📊 Frame Count Options:")
    print("  [a] Quick Preview - 10 frames (~1 sec)")
    print("  [b] Standard - 30 frames (~2 sec)")
    print("  [c] Full Rotation - 140 frames (~8 sec)")
    print()
    print("🔧 Other Options:")
    print("  [p] Python-only simulation (fast preview)")
    print("  [s] Start local server to view results")
    print("  [t] Check tool status")
    print("  [q] Quit")
    print()
    
    # Show tool status
    print("─" * 40)
    verilator_status = "✅" if tools['verilator'] else "❌ (install verilator)"
    pillow_status = "✅" if tools['pillow'] else "❌ (pip install Pillow)"
    print(f"  verilator: {verilator_status}")
    print(f"  Pillow:    {pillow_status}")
    print()
    
    return input("Enter your choice: ").strip().lower()


def get_frame_count():
    """Get frame count from user"""
    print()
    print("Select frame count:")
    print("  [x] 5 frames (super quick ~0.5 sec)")
    print("  [a] 10 frames (quick ~1 sec)")
    print("  [b] 30 frames (standard ~2 sec)")
    print("  [c] 140 frames (full rotation ~8 sec)")
    print()
    choice = input("Enter choice [x/a/b/c]: ").strip().lower()
    
    if choice == 'x':
        return 5
    elif choice == 'a':
        return 10
    elif choice == 'c':
        return 140
    else:
        return 30


def create_verilator_wrapper(top_module, wrapper_name):
    """Create Verilog wrapper for Verilator"""
    wrapper_v = f'''`timescale 1ns / 1ps

module {wrapper_name} (
    input wire clk,
    input wire rst_n,
    output wire hsync,
    output wire vsync,
    output wire [1:0] r_out,
    output wire [1:0] g_out,
    output wire [1:0] b_out
);

    {top_module} dut (
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
    
    wrapper_path = os.path.join(BUILD_DIR, f'{wrapper_name}.v')
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_v)
    
    return wrapper_path


def create_cpp_testbench(num_frames, wrapper_name):
    """Create C++ testbench for Verilator"""
    cpp_content = f'''#include "V{wrapper_name}.h"
#include "verilated.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>

const int H_DISPLAY = {H_DISPLAY};
const int H_TOTAL = {H_TOTAL};
const int V_DISPLAY = {V_DISPLAY};
const int V_TOTAL = {V_TOTAL};
const int NUM_FRAMES = {num_frames};

inline unsigned char extend_2bit(unsigned char val) {{
    val &= 0x3;
    return (val << 6) | (val << 4) | (val << 2) | val;
}}

int main(int argc, char** argv) {{
    Verilated::commandArgs(argc, argv);
    V{wrapper_name}* top = new V{wrapper_name};
    
    std::ofstream outfile("vga_output.raw", std::ios::binary);
    if (!outfile) {{
        std::cerr << "ERROR: Could not open output file" << std::endl;
        return 1;
    }}
    
    std::cout << "Starting VGA capture simulation..." << std::endl;
    std::cout << "Capturing " << NUM_FRAMES << " frames at " 
              << H_DISPLAY << "x" << V_DISPLAY << std::endl;
    
    top->clk = 0;
    top->rst_n = 0;
    
    for (int i = 0; i < 10; i++) {{
        top->clk = 0; top->eval();
        top->clk = 1; top->eval();
    }}
    
    top->rst_n = 1;
    
    int h_count = 0, v_count = 0, frame_count = 0;
    std::vector<unsigned char> frame_buffer;
    frame_buffer.reserve(H_DISPLAY * V_DISPLAY * 3);
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    while (frame_count < NUM_FRAMES) {{
        top->clk = 0; top->eval();
        top->clk = 1; top->eval();
        
        if (h_count < H_DISPLAY && v_count < V_DISPLAY) {{
            frame_buffer.push_back(extend_2bit(top->r_out));
            frame_buffer.push_back(extend_2bit(top->g_out));
            frame_buffer.push_back(extend_2bit(top->b_out));
        }}
        
        h_count++;
        if (h_count >= H_TOTAL) {{
            h_count = 0;
            v_count++;
            if (v_count >= V_TOTAL) {{
                v_count = 0;
                frame_count++;
                outfile.write(reinterpret_cast<const char*>(frame_buffer.data()), frame_buffer.size());
                frame_buffer.clear();
                std::cout << "Frame " << frame_count << "/" << NUM_FRAMES << " complete" << std::endl;
            }}
        }}
    }}
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count();
    
    std::cout << "Simulation complete! Output written to vga_output.raw" << std::endl;
    
    outfile.close();
    delete top;
    return 0;
}}
'''
    
    cpp_path = os.path.join(BUILD_DIR, 'tb_verilator.cpp')
    with open(cpp_path, 'w') as f:
        f.write(cpp_content)
    
    return cpp_path


def build_simulation(sources, top_module, num_frames):
    """Build the Verilog simulation with Verilator"""
    print("\n📦 Building Verilog Simulation...")
    print("-" * 40)
    
    os.makedirs(BUILD_DIR, exist_ok=True)
    
    wrapper_name = f'{top_module}_wrapper'
    
    # Create wrapper and testbench
    wrapper_path = create_verilator_wrapper(top_module, wrapper_name)
    cpp_path = create_cpp_testbench(num_frames, wrapper_name)
    
    # Collect source files
    source_files = [os.path.join(SRC_DIR, f) for f in sources]
    source_files.append(wrapper_path)
    
    # Check all files exist
    for src in source_files:
        if not os.path.exists(src):
            print(f"❌ Source file not found: {src}")
            return None
    
    # Build with Verilator
    cmd = [
        'verilator',
        '--cc', '--exe', '--build',
        '-Wall', '-Wno-fatal',
        '--top-module', wrapper_name,
        '-I' + SRC_DIR,
        '--Mdir', BUILD_DIR,
        '-O2',
    ]
    
    cmd.extend(source_files)
    cmd.append(cpp_path)
    
    print(f"Compiling: {top_module}.vvp")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ BUILD FAILED!")
        print(result.stderr)
        return None
    
    if result.stderr:
        print("⚠️  Warnings:")
        print(result.stderr)
    
    exe_name = f'V{wrapper_name}.exe' if platform.system() == 'Windows' else f'V{wrapper_name}'
    exe_path = os.path.join(BUILD_DIR, exe_name)
    
    print(f"✅ Build successful: {exe_path}")
    return exe_path


def run_simulation(exe_path, num_frames):
    """Run the Verilator simulation"""
    print("\n🚀 Running Verilog Simulation...")
    print("-" * 40)
    print(f"Simulating {num_frames} frames at 640x480")
    print("This may take a few seconds...")
    print()
    
    # Change to build directory
    old_cwd = os.getcwd()
    os.chdir(BUILD_DIR)
    
    start_time = time.time()
    
    try:
        cmd = [f'./{os.path.basename(exe_path)}' if platform.system() != 'Windows' else os.path.basename(exe_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            print("\n❌ SIMULATION FAILED!")
            print(result.stderr)
            return None, 0
        
        print(result.stdout)
        return elapsed, num_frames
        
    finally:
        os.chdir(old_cwd)


def convert_raw_to_frames(num_frames, output_name='sphere'):
    """Convert raw VGA output to PNG frames and GIF"""
    print("\n🎨 Converting to PNG Frames...")
    print("-" * 40)
    
    try:
        from PIL import Image
    except ImportError:
        print("❌ Pillow not installed. Run: pip install Pillow")
        return None
    
    raw_file = os.path.join(BUILD_DIR, 'vga_output.raw')
    if not os.path.exists(raw_file):
        print(f"❌ Raw output not found: {raw_file}")
        return None
    
    # Generate timestamp for this run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    timestamped_name = f'{output_name}_{timestamp}'
    
    # Create organized output directories with timestamp
    frames_dir = os.path.join(OUTPUT_DIR, 'frames', timestamped_name)
    gifs_dir = os.path.join(OUTPUT_DIR, 'gifs')
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(gifs_dir, exist_ok=True)
    
    with open(raw_file, 'rb') as f:
        data = f.read()
    
    frame_size = H_DISPLAY * V_DISPLAY * 3
    actual_frames = len(data) // frame_size
    
    print(f"Found {actual_frames} frames in raw data")
    print(f"Saving frames to: {frames_dir}")
    
    images = []
    for i in range(actual_frames):
        start = i * frame_size
        end = start + frame_size
        frame_data = data[start:end]
        
        img = Image.frombytes('RGB', (H_DISPLAY, V_DISPLAY), frame_data)
        filename = os.path.join(frames_dir, f'frame_{i:04d}.png')
        img.save(filename)
        images.append(img)
        
        if (i + 1) % 10 == 0 or i == actual_frames - 1:
            print(f"  Saved frame {i + 1}/{actual_frames}")
    
    # Create GIF in gifs directory with timestamp
    gif_path = os.path.join(gifs_dir, f'{timestamped_name}.gif')
    if images:
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=50,
            loop=0
        )
        print(f"\n✅ Created GIF: {gif_path}")
    
    # Also create a "latest" symlink/copy for the viewer
    latest_gif = os.path.join(gifs_dir, f'{output_name}_latest.gif')
    try:
        if os.path.exists(latest_gif):
            os.remove(latest_gif)
        shutil.copy(gif_path, latest_gif)
        print(f"✅ Updated latest: {latest_gif}")
    except Exception as e:
        print(f"⚠️  Could not create latest copy: {e}")
    
    return gif_path, actual_frames


def print_completion_report(elapsed_time, num_frames, sim_type):
    """Print detailed completion report"""
    print()
    print("=" * 60)
    print("  📊 SIMULATION COMPLETION REPORT")
    print("=" * 60)
    print()
    
    # Basic stats
    total_pixels = H_DISPLAY * V_DISPLAY * num_frames
    pixels_per_frame = H_DISPLAY * V_DISPLAY
    
    # Verilog clock cycles
    clocks_per_frame = H_TOTAL * V_TOTAL
    total_clocks = clocks_per_frame * num_frames
    
    # Ray marching steps (8 steps per pixel, but processed in parallel)
    ray_steps_per_pixel = 8
    total_ray_steps = pixels_per_frame * ray_steps_per_pixel * num_frames
    
    # Time calculations
    time_per_frame = elapsed_time / num_frames if num_frames > 0 else 0
    pixels_per_second = total_pixels / elapsed_time if elapsed_time > 0 else 0
    
    # FPGA performance (at 25.175 MHz)
    fpga_time_per_frame = clocks_per_frame / (PIXEL_CLOCK_MHZ * 1_000_000)  # seconds
    fpga_fps = 1 / fpga_time_per_frame  # frames per second
    
    print(f"📐 Resolution:           {H_DISPLAY} x {V_DISPLAY} pixels")
    print(f"🎬 Frames Rendered:      {num_frames}")
    print(f"📺 Simulation Type:      {sim_type}")
    print()
    print("─" * 40)
    print("  PIXEL STATISTICS")
    print("─" * 40)
    print(f"  Pixels per frame:      {pixels_per_frame:,}")
    print(f"  Total pixels:          {total_pixels:,}")
    print(f"  Ray steps per pixel:   {ray_steps_per_pixel}")
    print(f"  Total ray steps:       {total_ray_steps:,}")
    print()
    print("─" * 40)
    print("  VERILOG CLOCK CYCLES")
    print("─" * 40)
    print(f"  H_TOTAL × V_TOTAL:     {H_TOTAL} × {V_TOTAL} = {clocks_per_frame:,}")
    print(f"  Clocks per frame:      {clocks_per_frame:,}")
    print(f"  Total clock cycles:    {total_clocks:,}")
    print()
    print("─" * 40)
    print("  SIMULATION PERFORMANCE")
    print("─" * 40)
    print(f"  Total time:            {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} min)")
    print(f"  Time per frame:        {time_per_frame:.2f} seconds")
    print(f"  Pixels per second:     {pixels_per_second:,.0f}")
    print(f"  Effective clock rate:  {total_clocks/elapsed_time/1e6:.2f} MHz (simulated)")
    print()
    print("─" * 40)
    print("  FPGA vs CPU COMPARISON")
    print("─" * 40)
    print(f"  ⚡ FPGA Clock:          {PIXEL_CLOCK_MHZ} MHz (real hardware)")
    print(f"  ⚡ FPGA time/frame:     {fpga_time_per_frame*1000:.2f} ms")
    print(f"  ⚡ FPGA frame rate:     {fpga_fps:.1f} FPS (real-time VGA!)")
    print()
    print(f"  💻 CPU Simulation:     {total_clocks/elapsed_time/1e6:.4f} MHz")
    print(f"  💻 CPU time/frame:     {time_per_frame*1000:.0f} ms")
    print(f"  💻 CPU frame rate:     {1/time_per_frame:.2f} FPS")
    print()
    print(f"  📈 FPGA Speedup:       {time_per_frame/fpga_time_per_frame:.0f}x faster than simulation")
    print()
    print("═" * 60)


def start_local_server(port=8080):
    """Start a local HTTP server to view results"""
    os.chdir(OUTPUT_DIR)
    
    handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"\n🌐 Server running at http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        print()
        
        # Open browser
        webbrowser.open(f'http://localhost:{port}')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


def create_viewer_html():
    """Create HTML viewer for the output that shows all GIFs with improved layout"""
    
    # Find all GIF files in the gifs directory
    gifs_dir = os.path.join(OUTPUT_DIR, 'gifs')
    gif_files = []
    if os.path.exists(gifs_dir):
        gif_files = sorted([f for f in os.listdir(gifs_dir) if f.endswith('.gif')], reverse=True)
    
    # Categorize GIFs
    latest_gifs = []
    coin_gifs = []
    floor_gifs = []
    sphere_gifs = []
    cube_gifs = []
    kirby_gifs = []
    
    for gif in gif_files:
        if 'latest' in gif.lower():
            latest_gifs.append(gif)
        elif 'mario_coin' in gif.lower() or 'coin' in gif.lower():
            coin_gifs.append(gif)
        elif 'sphere_floor' in gif.lower() or 'floor' in gif.lower():
            floor_gifs.append(gif)
        elif 'cube' in gif.lower():
            cube_gifs.append(gif)
        elif 'kirby' in gif.lower():
            kirby_gifs.append(gif)
        elif 'sphere' in gif.lower():
            sphere_gifs.append(gif)
    
    def get_frame_count_from_name(gif_name):
        """Extract frame count from GIF by checking the frames directory"""
        import re
        # Try to extract the timestamped name
        match = re.search(r'(.+)_\d{8}_\d{6}\.gif$', gif_name)
        if match:
            base_name = match.group(0).replace('.gif', '')
            frames_dir = os.path.join(OUTPUT_DIR, 'frames', base_name)
            if os.path.exists(frames_dir):
                frame_files = [f for f in os.listdir(frames_dir) if f.startswith('frame_') and f.endswith('.png')]
                return f"{len(frame_files)} frames"
        return ''
    
    def get_type_name(gif_name):
        """Get display name for GIF type"""
        if 'coin' in gif_name.lower():
            return '🪙 Mario Coin'
        elif 'sphere_floor' in gif_name.lower() or 'floor' in gif_name.lower():
            return '🏁 Sphere + Floor'
        elif 'cube' in gif_name.lower():
            return '🎲 Rotating Cube'
        elif 'kirby' in gif_name.lower():
            return '💗 Kirby'
        else:
            return '🔮 Sphere Only'
    
    # Generate HTML for most recent (large)
    recent_html = ""
    for gif in latest_gifs[:3]:
        name = get_type_name(gif)
        recent_html += f'''
        <div class="gif-container-large">
            <h4>{name}</h4>
            <span class="frame-count">Latest</span>
            <img src="gifs/{gif}" alt="{name}" loading="lazy">
        </div>
'''
    if not recent_html:
        recent_html = '<p class="empty-group">No simulations yet. Run a simulation first!</p>'
    
    def generate_small_grid(gifs, max_items=15):
        """Generate small GIF grid HTML"""
        html = ""
        for gif in gifs[:max_items]:
            if 'latest' in gif.lower():
                continue
            frame_info = get_frame_count_from_name(gif)
            html += f'''
            <div class="gif-container-small">
                <span class="gif-name">{frame_info}</span>
                <img src="gifs/{gif}" alt="{gif}" loading="lazy">
            </div>
'''
        if not html:
            html = '<p class="empty-group">No simulations in this category</p>'
        return html
    
    coin_html = generate_small_grid(coin_gifs)
    floor_html = generate_small_grid(floor_gifs)
    sphere_html = generate_small_grid(sphere_gifs)
    cube_html = generate_small_grid(cube_gifs)
    kirby_html = generate_small_grid(kirby_gifs)
    
    # Build the complete HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VGA Ray Marcher - Output Viewer</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }}
        h1 {{ color: #ff6b6b; text-align: center; margin-bottom: 30px; }}
        h2 {{ color: #4ecdc4; border-bottom: 2px solid #4ecdc4; padding-bottom: 10px; margin-top: 40px; }}
        
        /* Most Recent Section - Large GIFs */
        .recent-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        .gif-container-large {{
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid #4ecdc4;
            box-shadow: 0 4px 20px rgba(78, 205, 196, 0.2);
        }}
        .gif-container-large img {{
            max-width: 100%;
            border-radius: 8px;
            image-rendering: pixelated;
            margin-top: 10px;
        }}
        .gif-container-large h4 {{
            margin: 0 0 8px 0;
            color: #4ecdc4;
            font-size: 1.2rem;
        }}
        
        /* History Section - Small GIFs */
        .history-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 30px;
        }}
        .gif-container-small {{
            background: #16213e;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }}
        .gif-container-small img {{
            max-width: 100%;
            border-radius: 4px;
            image-rendering: pixelated;
            margin-top: 5px;
        }}
        .gif-container-small .gif-name {{
            color: #4ecdc4;
            font-size: 0.75rem;
            display: block;
            margin-bottom: 3px;
        }}
        
        .frame-count {{
            display: inline-block;
            background: #ff6b6b;
            color: #fff;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .category-section {{
            margin-bottom: 40px;
        }}
        .category-title {{
            color: #888;
            font-size: 1rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .category-title::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: #333;
        }}
        .empty-group {{
            color: #666;
            font-style: italic;
            padding: 20px;
            text-align: center;
        }}
        
        .info {{
            background: #0f3460;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }}
        .info h3 {{ color: #ff6b6b; margin-top: 0; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        .stat {{
            background: #16213e;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-value {{ font-size: 1.3rem; color: #4ecdc4; }}
        .stat-label {{ font-size: 0.75rem; color: #888; }}
    </style>
</head>
<body>
    <h1>🌐 VGA Sphere Ray Marcher</h1>
    
    <h2>⭐ Most Recent</h2>
    <div class="recent-container">
{recent_html}
    </div>
    
    <h2>📁 Simulation History</h2>
    
    <div class="category-section">
        <div class="category-title">🟡 Mario Coin</div>
        <div class="history-container">
{coin_html}
        </div>
    </div>
    
    <div class="category-section">
        <div class="category-title">🔵 Sphere + Floor</div>
        <div class="history-container">
{floor_html}
        </div>
    </div>
    
    <div class="category-section">
        <div class="category-title">⚪ Sphere Only</div>
        <div class="history-container">
{sphere_html}
        </div>
    </div>
    
    <div class="category-section">
        <div class="category-title">🎲 Rotating Cube</div>
        <div class="history-container">
{cube_html}
        </div>
    </div>
    
    <div class="category-section">
        <div class="category-title">💗 Kirby</div>
        <div class="history-container">
{kirby_html}
        </div>
    </div>
    
    <div class="info">
        <h3>📊 Performance Statistics</h3>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">640×480</div>
                <div class="stat-label">Resolution</div>
            </div>
            <div class="stat">
                <div class="stat-value">60 FPS</div>
                <div class="stat-label">Real-time on FPGA</div>
            </div>
            <div class="stat">
                <div class="stat-value">25.175 MHz</div>
                <div class="stat-label">Pixel Clock</div>
            </div>
            <div class="stat">
                <div class="stat-value">~1000x</div>
                <div class="stat-label">FPGA Speedup</div>
            </div>
        </div>
    </div>
</body>
</html>
'''
    
    viewer_path = os.path.join(OUTPUT_DIR, 'index.html')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(viewer_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return viewer_path


def run_full_simulation(sim_type, num_frames):
    """Run complete simulation pipeline"""
    if sim_type == 'sphere':
        sources = SOURCES_SPHERE
        top_module = 'vga_sphere'
        output_name = 'sphere_verilog'
    elif sim_type == 'floor':
        sources = SOURCES_FLOOR
        top_module = 'vga_scene_sphere'
        output_name = 'sphere_floor'
    elif sim_type == 'coin':
        sources = SOURCES_COIN
        top_module = 'vga_scene_coin'
        output_name = 'mario_coin'
    elif sim_type == 'cube':
        sources = SOURCES_CUBE
        top_module = 'vga_cube'
        output_name = 'cube_verilog'
    elif sim_type == 'kirby':
        sources = SOURCES_KIRBY
        top_module = 'vga_kirby'
        output_name = 'kirby_verilog'
    else:
        sources = SOURCES_FLOOR
        top_module = 'vga_scene_sphere'
        output_name = 'sphere_floor'
    
    # Build
    exe_path = build_simulation(sources, top_module, num_frames)
    if not exe_path:
        return False
    
    # Run simulation
    elapsed_time, frames = run_simulation(exe_path, num_frames)
    if elapsed_time is None:
        return False
    
    # Convert to images
    gif_path, actual_frames = convert_raw_to_frames(frames, output_name)
    if not gif_path:
        return False
    
    # Print report
    sim_names = {
        'sphere': 'Sphere Only',
        'floor': 'Sphere + Floor',
        'coin': 'Mario Coin',
        'cube': 'Rotating Cube',
        'kirby': 'Kirby Character'
    }
    print_completion_report(elapsed_time, actual_frames, sim_names.get(sim_type, sim_type))
    
    # Create viewer
    create_viewer_html()
    
    print(f"\n✅ Output: {gif_path}")
    
    return True


def main():
    """Main interactive loop"""
    # Initialize PATH at startup
    check_tools()
    
    clear_screen()
    print_header()
    
    while True:
        choice = display_menu()
        
        if choice == '1':
            # Sphere only
            num_frames = get_frame_count()
            clear_screen()
            print_header()
            run_full_simulation('sphere', num_frames)
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == '2':
            # Sphere + floor
            num_frames = get_frame_count()
            clear_screen()
            print_header()
            run_full_simulation('floor', num_frames)
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == '3':
            # Mario coin
            num_frames = get_frame_count()
            clear_screen()
            print_header()
            run_full_simulation('coin', num_frames)
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == '4':
            # Rotating cube
            num_frames = get_frame_count()
            clear_screen()
            print_header()
            run_full_simulation('cube', num_frames)
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == '5':
            # Kirby
            num_frames = get_frame_count()
            clear_screen()
            print_header()
            run_full_simulation('kirby', num_frames)
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == 'a':
            # Quick 10 frames - sphere
            clear_screen()
            print_header()
            run_full_simulation('sphere', 10)
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == 'b':
            # Standard 30 frames - sphere
            clear_screen()
            print_header()
            run_full_simulation('sphere', 30)
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == 'c':
            # Full 140 frames - sphere
            clear_screen()
            print_header()
            run_full_simulation('sphere', 140)
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == 'p':
            # Python simulation
            print("\n🐍 Running Python simulation...")
            script = os.path.join(SCRIPTS_DIR, 'sphere_raymarcher.py')
            if os.path.exists(script):
                subprocess.run([sys.executable, script, '--frames', '30', '--gif'])
            else:
                print(f"❌ Script not found: {script}")
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == 's':
            # Start server
            create_viewer_html()
            start_local_server()
            clear_screen()
            print_header()
            
        elif choice == 't':
            # Tool status
            tools = check_tools()
            print("\n🔧 Tool Status:")
            print(f"  verilator: {'✅ Installed' if tools['verilator'] else '❌ Not found'}")
            print(f"  g++:       {'✅ Installed' if tools['g++'] else '❌ Not found'}")
            print(f"  Pillow:    {'✅ Installed' if tools['pillow'] else '❌ Not found'}")
            input("\nPress Enter to continue...")
            clear_screen()
            print_header()
            
        elif choice == 'q':
            print("\n👋 Goodbye!")
            break
            
        else:
            print("\n❌ Invalid choice. Please try again.")
            time.sleep(1)
            clear_screen()
            print_header()


if __name__ == '__main__':
    # Initialize PATH at startup
    check_tools()
    
    # Check if running with command-line args for backward compatibility
    if len(sys.argv) > 1:
        if sys.argv[1] == 'sim':
            run_full_simulation('sphere', 30)
        elif sys.argv[1] == 'floor':
            run_full_simulation('floor', 30)
        elif sys.argv[1] == 'quick':
            run_full_simulation('sphere', 5)
        elif sys.argv[1] == 'quickfloor':
            run_full_simulation('floor', 5)
        elif sys.argv[1] == 'coin':
            run_full_simulation('coin', 30)
        elif sys.argv[1] == 'quickcoin':
            run_full_simulation('coin', 5)
        elif sys.argv[1] == 'cube':
            run_full_simulation('cube', 30)
        elif sys.argv[1] == 'quickcube':
            run_full_simulation('cube', 5)
        elif sys.argv[1] == 'kirby':
            run_full_simulation('kirby', 30)
        elif sys.argv[1] == 'quickkirby':
            run_full_simulation('kirby', 5)
        elif sys.argv[1] == 'server':
            create_viewer_html()
            start_local_server()
        elif sys.argv[1] == 'check':
            tools = check_tools()
            print("Tool Status:")
            for tool, status in tools.items():
                print(f"  {tool}: {'✅' if status else '❌'}")
        else:
            print("Usage: python run_verilator.py [sim|floor|coin|server|check]")
            print("Or run without arguments for interactive menu")
    else:
        main()
