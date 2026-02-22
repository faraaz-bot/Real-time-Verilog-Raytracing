# VGA Ray Marcher

A real-time ray marcher that renders 3D shaded shapes on VGA output, designed for Tiny Tapeout. The rendering uses only fixed-point arithmetic and CORDIC algorithms - no multipliers required!

![Sphere with Floor](output/gifs/sphere_floor_latest.gif)

## Quick Start (From Scratch)

### Step 1: Install Python Dependencies

```bash
pip install Pillow
```

### Step 2: Install Icarus Verilog

<details>
<summary><b>Windows</b></summary>

1. Download the installer from: https://bleyer.org/icarus/
   - Direct link: [iverilog-v12-20220611-x64_setup.exe](https://bleyer.org/icarus/iverilog-v12-20220611-x64_setup.exe)
2. Run the installer
3. **IMPORTANT:** Check "Add to PATH" during installation, OR manually add `C:\iverilog\bin` to your PATH
4. Restart your terminal/VS Code after installation

To verify installation:
```bash
iverilog -v
vvp -v
```

</details>

<details>
<summary><b>macOS</b></summary>

Using Homebrew:
```bash
brew install icarus-verilog
```

</details>

<details>
<summary><b>Linux (Ubuntu/Debian)</b></summary>

```bash
sudo apt update
sudo apt install iverilog
```

</details>

<details>
<summary><b>Linux (Fedora)</b></summary>

```bash
sudo dnf install iverilog
```

</details>

### Step 3: Run the Simulation

```bash
# Interactive menu
python run.py

# Or quick commands:
python run.py quickfloor    # 5 frames, sphere + floor (~1.5 min)
python run.py quickcoin     # 5 frames, Mario coin (~1.5 min)
python run.py floor         # 30 frames, sphere + floor (~10 min)
```

### Step 4: View Results

```bash
# Start local web server to view all generated GIFs
python run.py server
```

This opens http://localhost:8080 showing all your rendered animations.

---

## Available Simulations

| Command | Shape | Frames | Time |
|---------|-------|--------|------|
| `python run.py quick` | Sphere only | 5 | ~1.5 min |
| `python run.py quickfloor` | Sphere + Floor | 5 | ~1.5 min |
| `python run.py quickcoin` | Mario Coin | 5 | ~1.5 min |
| `python run.py sim` | Sphere only | 30 | ~10 min |
| `python run.py floor` | Sphere + Floor | 30 | ~10 min |
| `python run.py coin` | Mario Coin | 30 | ~10 min |

Or run `python run.py` for an interactive menu with more options.

---

## Troubleshooting

### "iverilog not found"

The script automatically checks common installation paths:
- `C:\iverilog\bin`
- `C:\Program Files\Icarus Verilog\bin`

If still not found:
1. Verify iverilog is installed: run `iverilog -v` in a terminal
2. Add the bin directory to your PATH manually
3. Restart VS Code/terminal after PATH changes

### Check Tool Status

```bash
python run.py check
```

Shows status for: iverilog, vvp, Pillow

---

## Project Structure

```
ray-tracing/
├── src/                        # Verilog HDL source
│   ├── vgasphere.v             # Sphere only VGA controller
│   ├── vgasphere_floor.v       # Sphere + floor VGA controller
│   ├── vgacoin_floor.v         # Mario coin VGA controller
│   ├── sphere.v                # Sphere ray marching controller
│   ├── spherehit.v             # Sphere SDF + lighting
│   ├── coin.v                  # Coin ray marching controller
│   ├── coinhit.v               # Coin SDF (flattened sphere)
│   ├── sphere_floor.v          # Sphere scene with floor
│   ├── coin_floor.v            # Coin scene with floor
│   ├── cordic2step.v           # 2-step CORDIC rotation
│   ├── cordic3step.v           # 3-step CORDIC rotation
│   ├── step3vec.v              # 3D vector stepping
│   ├── tt_um_vga_sphere.v      # TinyTapeout: Sphere
│   ├── tt_um_vga_sphere_floor.v # TinyTapeout: Sphere + Floor
│   └── tt_um_vga_coin.v        # TinyTapeout: Mario Coin
│
├── output/                     # Generated output
│   ├── gifs/                   # Animated GIFs
│   ├── frames/                 # Individual PNG frames
│   └── index.html              # Web viewer
│
├── build/                      # Build artifacts (gitignored)
├── test/                       # Test files
├── scripts/                    # Python tools
│
├── run.py                      # Main entry point
├── info.yaml                   # Tiny Tapeout configuration
└── README.md
```

---

## How It Works

### Ray Marching
Each pixel casts a ray from the camera through the screen. The ray is "marched" forward in steps, evaluating the Signed Distance Function (SDF) at each point:

```
Sphere SDF:  SDF(p) = length(p) - radius
Coin SDF:    SDF(p) = length(p.x, p.y, p.z * 2) - radius  (flattened)
```

When SDF is approximately 0, we've hit the surface.

### Lighting
The surface normal at hit point P is `normalize(P)`. Diffuse lighting is computed as `dot(normal, light_direction)`.

### CORDIC
All rotations and normalizations use CORDIC (COordinate Rotation DIgital Computer) algorithms, which only require shifts and adds - no expensive multipliers!

### Camera Animation
The camera orbits using the HAKMEM 149 "Minsky circle" algorithm, producing smooth rotation without drift.

---

## VGA Output

| Parameter | Value |
|-----------|-------|
| Resolution | 640x480 |
| Refresh Rate | 60 Hz |
| Color Depth | 2-bit per channel (64 colors) |
| Pixel Clock | 25.175 MHz |

---

## Tiny Tapeout

This design is configured for [Tiny Tapeout](https://tinytapeout.com/). Three separate top-level wrappers are available:

| Module | Description |
|--------|-------------|
| `tt_um_vga_sphere.v` | Sphere only (blue background) |
| `tt_um_vga_sphere_floor.v` | Sphere with checkerboard floor |
| `tt_um_vga_coin.v` | Mario coin with floor |

### TinyVGA PMOD Pinout
| Pin | Signal |
|-----|--------|
| `uo_out[0]` | HSync |
| `uo_out[1]` | B[0] |
| `uo_out[2]` | G[0] |
| `uo_out[3]` | R[0] |
| `uo_out[4]` | VSync |
| `uo_out[5]` | B[1] |
| `uo_out[6]` | G[1] |
| `uo_out[7]` | R[1] |

---

## Performance

| Metric | FPGA (Hardware) | CPU Simulation |
|--------|-----------------|----------------|
| Clock Speed | 25.175 MHz | ~0.02 MHz |
| Time per Frame | 16.68 ms | ~19,000 ms |
| Frame Rate | 59.9 FPS | ~0.05 FPS |
| **Speedup** | **~1000x faster** | - |

---

## Testing

The project includes comprehensive testbenches for verification and TinyTapeout submission.

### Quick Verification

```bash
# Syntax check all sources
iverilog -o nul -Isrc src/tt_um_vga_sphere.v src/vgasphere.v src/sphere.v src/spherehit.v src/cordic2step.v src/cordic3step.v src/step3vec.v

# Run VGA simulation
python run.py quick
```

### Cocotb Testbenches

Requires [cocotb](https://docs.cocotb.org/):

```bash
pip install cocotb

# Run all tests
cd test && make

# Run individual module tests
cd test && make test-cordic
cd test && make test-step3vec
cd test && make test-spherehit
```

### Test Coverage

| Test File | Module | Tests | Description |
|-----------|--------|-------|-------------|
| `test.py` | tt_um_vga_sphere | 8 | Top-level TinyTapeout wrapper |
| `test_cordic.py` | cordic2step | 5 | Vector magnitude (CORDIC) |
| `test_step3vec.py` | step3vec | 5 | Distance-scaled stepping |
| `test_spherehit.py` | spherehit | 5 | Ray-sphere intersection |

### TinyTapeout Test Requirements

The testbench follows TinyTapeout guidelines:
- `tb.v` instantiates `tt_um_vga_sphere` with correct interface
- `test.py` contains required cocotb assertions
- All bidirectional pins configured as inputs (`uio_oe = 0x00`)
- Unused outputs assigned to 0

---

## Roadmap

- [x] Sphere rendering
- [x] Checkerboard floor
- [x] Sky gradient
- [x] Mario coin (flattened sphere)
- [ ] Kirby character (multiple SDFs)
- [ ] Reflective floor
- [ ] Torus (donut)

---
