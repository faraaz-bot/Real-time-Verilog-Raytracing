#!/usr/bin/env python3
"""
Pure Python Ray Marcher for VGA Sphere
========================================

This script emulates the Verilog ray marching algorithm in Python,
generating the same frames that the hardware would produce.

No Verilog simulator required - just Python + Pillow.

Usage:
    python sphere_raymarcher.py           # Generate 60 frames
    python sphere_raymarcher.py --frames 10  # Generate 10 frames
    python sphere_raymarcher.py --gif     # Also create animated GIF
"""

import os
import sys
import math
import argparse

# Try to import PIL
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    print("Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)

# Screen dimensions
WIDTH = 640
HEIGHT = 480

# Sphere radius
SPHERE_RADIUS = 1.5

# Camera distance from origin
CAMERA_DISTANCE = 4.0


def normalize(v):
    """Normalize a 3D vector"""
    length = math.sqrt(sum(x*x for x in v))
    if length < 0.0001:
        return [0, 0, 1]
    return [x / length for x in v]


def dot(a, b):
    """Dot product of two 3D vectors"""
    return sum(a[i] * b[i] for i in range(3))


def sphere_sdf(p, center, radius):
    """Signed distance to a sphere"""
    dx = p[0] - center[0]
    dy = p[1] - center[1]
    dz = p[2] - center[2]
    return math.sqrt(dx*dx + dy*dy + dz*dz) - radius


def ray_march(ray_origin, ray_dir, max_steps=64, max_dist=20.0):
    """
    Ray march to find intersection with sphere at origin
    Returns (hit, distance, position)
    """
    t = 0.0
    
    for _ in range(max_steps):
        # Current position along ray
        p = [ray_origin[i] + ray_dir[i] * t for i in range(3)]
        
        # Distance to sphere at origin
        dist = sphere_sdf(p, [0, 0, 0], SPHERE_RADIUS)
        
        # Hit check
        if dist < 0.001:
            return True, t, p
        
        # Miss check
        if t > max_dist:
            return False, t, p
        
        # Step forward
        t += dist
    
    return False, t, [ray_origin[i] + ray_dir[i] * t for i in range(3)]


def render_frame(angle):
    """
    Render a single frame with the camera orbiting around the sphere
    Returns list of RGB pixels
    """
    pixels = []
    
    # Camera orbiting around the sphere
    cam_x = math.sin(angle) * CAMERA_DISTANCE
    cam_y = 0.5  # Slightly above center
    cam_z = math.cos(angle) * CAMERA_DISTANCE
    camera = [cam_x, cam_y, cam_z]
    
    # Camera looks at origin
    forward = normalize([-cam_x, -cam_y, -cam_z])
    right = normalize([forward[2], 0, -forward[0]])  # Cross with up
    up = [
        right[1] * forward[2] - right[2] * forward[1],
        right[2] * forward[0] - right[0] * forward[2],
        right[0] * forward[1] - right[1] * forward[0]
    ]
    
    # Light direction (from top-right-front, normalized)
    light = normalize([0.5, 0.8, 0.3])
    
    # Aspect ratio
    aspect = WIDTH / HEIGHT
    fov = 1.0  # Field of view factor
    
    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Normalized screen coordinates (-1 to 1)
            u = (2.0 * x / WIDTH - 1.0) * aspect * fov
            v = (1.0 - 2.0 * y / HEIGHT) * fov
            
            # Ray direction in world space
            ray_dir = normalize([
                forward[0] + right[0] * u + up[0] * v,
                forward[1] + right[1] * u + up[1] * v,
                forward[2] + right[2] * u + up[2] * v
            ])
            
            # Ray march
            hit, dist, pos = ray_march(camera, ray_dir)
            
            if hit:
                # Surface normal (for sphere at origin, it's just normalized position)
                normal = normalize(pos)
                
                # Diffuse lighting
                diffuse = max(0, dot(normal, light))
                
                # Add some ambient
                ambient = 0.15
                luma = ambient + diffuse * 0.85
                luma = min(1.0, luma)
                
                # Slight gamma correction
                luma = luma ** 0.9
                
                # Warm orange-gold sphere color
                r = int(min(255, luma * 255 + 50))
                g = int(min(255, luma * 180 + 30))
                b = int(min(255, luma * 100 + 20))
            else:
                # Sky gradient background
                t = y / HEIGHT
                r = int(20 + t * 15)
                g = int(30 + t * 20)
                b = int(80 + t * 40)
            
            pixels.extend([r, g, b])
    
    return pixels


def main():
    parser = argparse.ArgumentParser(description='Python VGA Sphere Ray Marcher')
    parser.add_argument('--frames', type=int, default=60, help='Number of frames')
    parser.add_argument('--gif', action='store_true', help='Create animated GIF')
    parser.add_argument('--output', default='output', help='Output directory')
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    print(f"Rendering {args.frames} frames...")
    print(f"Output directory: {args.output}")
    print()
    
    images = []
    
    for frame in range(args.frames):
        # Camera rotation angle
        angle = frame * (2 * math.pi / args.frames)  # Full rotation over all frames
        
        print(f"  Frame {frame + 1}/{args.frames}...", end='', flush=True)
        
        pixels = render_frame(angle)
        
        # Create image
        img = Image.frombytes('RGB', (WIDTH, HEIGHT), bytes(pixels))
        
        # Save frame
        filename = os.path.join(args.output, f'frame_{frame:04d}.png')
        img.save(filename)
        print(" done")
        
        if args.gif:
            images.append(img)
    
    print(f"\nSaved {args.frames} frames to {args.output}/")
    
    # Create GIF
    if args.gif and images:
        gif_path = os.path.join(args.output, 'sphere.gif')
        print(f"Creating animated GIF: {gif_path}")
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=50,  # 50ms per frame = 20 fps
            loop=0
        )
        print(f"Created {gif_path}")
    
    # Create HTML viewer
    viewer_path = os.path.join(args.output, 'viewer.html')
    with open(viewer_path, 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>VGA Sphere Ray Marcher</title>
    <style>
        body { background: #1a1a2e; color: #fff; text-align: center; font-family: sans-serif; padding: 20px; }
        h1 { color: #00d9ff; }
        img { border: 2px solid #444; image-rendering: pixelated; }
        .controls { margin: 20px; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; font-size: 16px; }
        #num { display: inline-block; width: 60px; }
    </style>
</head>
<body>
    <h1>VGA Sphere Ray Marcher</h1>
    <p>Hardware ray marching simulation - rotating 3D sphere</p>
    <div class="controls">
        <button onclick="prev()">&lt; Prev</button>
        <span id="num">Frame 0</span>
        <button onclick="next()">Next &gt;</button>
        <button onclick="togglePlay()" id="playBtn">Play</button>
    </div>
    <div>
        <img id="frame" src="frame_0000.png" width="640" height="480">
    </div>
    <p><a href="sphere.gif" style="color:#00d9ff;">View animated GIF</a></p>
    <script>
        let f = 0, playing = false, interval = null;
        const maxF = """ + str(args.frames - 1) + """;
        
        function update() {
            document.getElementById('frame').src = 'frame_' + String(f).padStart(4, '0') + '.png';
            document.getElementById('num').textContent = 'Frame ' + f;
        }
        
        function next() { f = (f + 1) % (maxF + 1); update(); }
        function prev() { f = (f - 1 + maxF + 1) % (maxF + 1); update(); }
        
        function togglePlay() {
            playing = !playing;
            document.getElementById('playBtn').textContent = playing ? 'Pause' : 'Play';
            if (playing) {
                interval = setInterval(next, 50);
            } else {
                clearInterval(interval);
            }
        }
    </script>
</body>
</html>""")
    
    print(f"\nDone! Open {viewer_path} in your browser to view the animation.")


if __name__ == '__main__':
    main()
