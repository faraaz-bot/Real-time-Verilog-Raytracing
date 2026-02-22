#!/usr/bin/env python3
"""
Streamlit Web App for VGA Raytracing Visualizations
Displays all generated GIFs in an interactive gallery
"""

import streamlit as st
import os
from pathlib import Path
import re
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="VGA Raytracing Gallery",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
OUTPUT_DIR = Path(__file__).parent / 'output'
GIFS_DIR = OUTPUT_DIR / 'gifs'
FRAMES_DIR = OUTPUT_DIR / 'frames'

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #1a1a2e;
    }
    h1 {
        color: #ff6b6b;
        text-align: center;
    }
    h2 {
        color: #4ecdc4;
        border-bottom: 2px solid #4ecdc4;
        padding-bottom: 10px;
    }
    .stImage {
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(78, 205, 196, 0.2);
    }
</style>
""", unsafe_allow_html=True)

def get_frame_count(gif_path):
    """Get frame count from corresponding frames directory"""
    gif_name = gif_path.stem
    frames_dir = FRAMES_DIR / gif_name
    if frames_dir.exists():
        frame_files = list(frames_dir.glob('frame_*.png'))
        return len(frame_files)
    return 0

def categorize_gifs():
    """Categorize GIFs by type"""
    if not GIFS_DIR.exists():
        return {}
    
    categories = {
        'Mario Coin': [],
        'Sphere + Floor': [],
        'Sphere Only': [],
        'Rotating Cube': [],
        'Kirby': []
    }
    
    for gif_file in GIFS_DIR.glob('*.gif'):
        if 'latest' in gif_file.name.lower():
            continue
            
        if 'mario_coin' in gif_file.name.lower() or 'coin' in gif_file.name.lower():
            categories['Mario Coin'].append(gif_file)
        elif 'sphere_floor' in gif_file.name.lower() or 'floor' in gif_file.name.lower():
            categories['Sphere + Floor'].append(gif_file)
        elif 'cube' in gif_file.name.lower():
            categories['Rotating Cube'].append(gif_file)
        elif 'kirby' in gif_file.name.lower():
            categories['Kirby'].append(gif_file)
        elif 'sphere' in gif_file.name.lower():
            categories['Sphere Only'].append(gif_file)
    
    # Sort by modification time (newest first)
    for category in categories:
        categories[category].sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return categories

def get_latest_gifs():
    """Get the latest GIF for each category"""
    if not GIFS_DIR.exists():
        return []
    
    latest = []
    for gif_file in GIFS_DIR.glob('*_latest.gif'):
        latest.append(gif_file)
    return latest

# Main app
st.title("VGA Raytracing Gallery")
st.markdown("### Real-time Verilog Raytracing Simulations")

# Sidebar
with st.sidebar:
    st.header("Statistics")
    st.metric("Resolution", "640×480")
    st.metric("FPGA Frame Rate", "60 FPS")
    st.metric("Pixel Clock", "25.175 MHz")
    st.metric("Verilator Speedup", "20-40x")
    
    st.markdown("---")
    st.header("Simulation Types")
    st.markdown("""
    - Sphere Only
    - Sphere + Floor
    - Mario Coin
    - Rotating Cube
    - Kirby Character
    """)
    
    st.markdown("---")
    
    with st.expander("Technical Details"):
        st.markdown("""
        **Raymarching Technique:**
        - Signed Distance Functions (SDF)
        - Iterative ray stepping
        - 8 clock cycles per pixel
        
        **Sphere SDF:**
        - CORDIC-based magnitude calculation
        - 2-3 iterations for accuracy
        - Smooth lighting via normal rotation
        
        **Cube SDF:**
        - Box SDF using axis distances
        - max(|x|-size, |y|-size, |z|-size)
        - Per-face normal calculation
        
        **Kirby SDF:**
        - Composite of 10 blended spheres
        - Smooth min operations
        - Feature-based coloring
        
        **Camera System:**
        - Minsky circle rotation
        - Incremental updates per frame
        - Prevents drift accumulation
        
        **Hardware:**
        - VGA 640x480 @ 60Hz
        - 25.175 MHz pixel clock
        - 2-bit color per channel
        - Temporal dithering
        """)
    
    st.markdown("---")
    st.markdown("**GitHub:** [Real-time-Verilog-Raytracing](https://github.com/faraaz-bot/Real-time-Verilog-Raytracing)")

# Most Recent Section
st.header("Most Recent")
latest_gifs = get_latest_gifs()

if latest_gifs:
    cols = st.columns(min(len(latest_gifs), 3))
    for idx, gif_path in enumerate(latest_gifs[:3]):
        with cols[idx]:
            # Determine type from filename
            if 'coin' in gif_path.name.lower():
                st.subheader("Mario Coin")
            elif 'floor' in gif_path.name.lower():
                st.subheader("Sphere + Floor")
            elif 'cube' in gif_path.name.lower():
                st.subheader("Rotating Cube")
            elif 'kirby' in gif_path.name.lower():
                st.subheader("Kirby")
            else:
                st.subheader("Sphere Only")
            
            st.image(str(gif_path), use_container_width=True)
            st.caption("Latest")
else:
    st.info("No simulations yet. Run a simulation first!")

# Simulation History
st.header("Simulation History")

categories = categorize_gifs()

# Create tabs for each category
tabs = st.tabs(["Mario Coin", "Sphere + Floor", "Sphere Only", "Rotating Cube", "Kirby"])

for tab, (category_name, category_key) in zip(tabs, [
    ("Mario Coin", "Mario Coin"),
    ("Sphere + Floor", "Sphere + Floor"),
    ("Sphere Only", "Sphere Only"),
    ("Rotating Cube", "Rotating Cube"),
    ("Kirby", "Kirby")
]):
    with tab:
        gifs = categories.get(category_key, [])
        
        if gifs:
            # Display in grid
            cols_per_row = 4
            for i in range(0, len(gifs), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(gifs):
                        gif_path = gifs[i + j]
                        with col:
                            st.image(str(gif_path), use_container_width=True)
                            frame_count = get_frame_count(gif_path)
                            if frame_count > 0:
                                st.caption(f"{frame_count} frames")
                            else:
                                st.caption(gif_path.stem)
        else:
            st.info(f"No {category_name} simulations yet")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p>VGA Raytracing Project - Powered by Verilator & Streamlit</p>
    <p>Real-time hardware raytracing at 60 FPS on FPGA</p>
</div>
""", unsafe_allow_html=True)
