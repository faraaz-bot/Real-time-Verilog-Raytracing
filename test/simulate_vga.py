#!/usr/bin/env python3
"""
VGA Sphere Simulation with Frame Capture
Uses cocotb to simulate the Verilog design and capture VGA frames as images.

This script can be run standalone to generate PNG frames from the simulation.
"""

import os
import sys
import struct

# Check if PIL is available
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL/Pillow not installed. Will output raw PPM files.")
    print("Install with: pip install Pillow")


# VGA timing parameters
H_DISPLAY = 640
H_FRONT_PORCH = 16
H_SYNC_PULSE = 96
H_BACK_PORCH = 48
H_TOTAL = 800

V_DISPLAY = 480
V_FRONT_PORCH = 10
V_SYNC_PULSE = 2
V_BACK_PORCH = 33
V_TOTAL = 525


def extend_2bit_to_8bit(val):
    """Extend 2-bit color to 8-bit (0-255)"""
    # 00 -> 0, 01 -> 85, 10 -> 170, 11 -> 255
    return (val << 6) | (val << 4) | (val << 2) | val


def save_ppm(filename, pixels, width, height):
    """Save raw RGB pixels as PPM image"""
    with open(filename, 'wb') as f:
        f.write(f"P6\n{width} {height}\n255\n".encode())
        f.write(bytes(pixels))


def save_png(filename, pixels, width, height):
    """Save raw RGB pixels as PNG image using PIL"""
    img = Image.frombytes('RGB', (width, height), bytes(pixels))
    img.save(filename)


def save_frame(filename, pixels, width, height):
    """Save frame as PNG if PIL available, otherwise PPM"""
    if HAS_PIL and filename.endswith('.png'):
        save_png(filename, pixels, width, height)
    else:
        # Convert .png to .ppm if no PIL
        if filename.endswith('.png'):
            filename = filename[:-4] + '.ppm'
        save_ppm(filename, pixels, width, height)
    return filename


class VGAFrameCapture:
    """Captures VGA frames from simulation signals"""
    
    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.frame_count = 0
        self.pixels = []
        self.current_line = []
        self.h_count = 0
        self.v_count = 0
        
    def clock_pixel(self, r, g, b, hsync, vsync):
        """Process one pixel clock"""
        # Capture pixel if in visible area
        if self.h_count < H_DISPLAY and self.v_count < V_DISPLAY:
            self.current_line.extend([
                extend_2bit_to_8bit(r),
                extend_2bit_to_8bit(g),
                extend_2bit_to_8bit(b)
            ])
        
        # Update horizontal counter
        self.h_count += 1
        if self.h_count >= H_TOTAL:
            self.h_count = 0
            # Store completed line
            if self.v_count < V_DISPLAY:
                self.pixels.extend(self.current_line)
            self.current_line = []
            
            # Update vertical counter
            self.v_count += 1
            if self.v_count >= V_TOTAL:
                self.v_count = 0
                self._save_frame()
                self.pixels = []
                
    def _save_frame(self):
        """Save the current frame"""
        if len(self.pixels) == H_DISPLAY * V_DISPLAY * 3:
            filename = os.path.join(self.output_dir, f'frame_{self.frame_count:04d}.png')
            saved_as = save_frame(filename, self.pixels, H_DISPLAY, V_DISPLAY)
            print(f"Saved frame {self.frame_count}: {saved_as}")
            self.frame_count += 1
        else:
            print(f"Warning: Incomplete frame {self.frame_count} ({len(self.pixels)} bytes)")


def create_test_frame():
    """Create a test frame with a gradient pattern to verify the pipeline"""
    pixels = []
    for y in range(V_DISPLAY):
        for x in range(H_DISPLAY):
            # Simple gradient
            r = int(x / H_DISPLAY * 255)
            g = int(y / V_DISPLAY * 255)
            b = 128
            pixels.extend([r, g, b])
    
    os.makedirs('output', exist_ok=True)
    filename = 'output/test_gradient.png'
    saved_as = save_frame(filename, pixels, H_DISPLAY, V_DISPLAY)
    print(f"Created test frame: {saved_as}")


def main():
    """Test the frame capture pipeline"""
    print("VGA Sphere Frame Capture Utility")
    print("=" * 40)
    
    # Create a test frame to verify PIL/output works
    create_test_frame()
    
    print("\nTo run the actual simulation, use:")
    print("  cd test && make")
    print("\nOr run the cocotb test:")
    print("  python -m pytest test_vga_sphere.py")


if __name__ == '__main__':
    main()
