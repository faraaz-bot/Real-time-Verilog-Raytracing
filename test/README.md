# Testing the Ray Marching VGA Renderer

This directory contains all testing infrastructure for the Hardware Ray Marching VGA Renderer.

## Quick Start

```bash
# From project root, activate virtual environment
source venv/bin/activate

# Capture images (5-10 minutes)
cd test
COCOTB_TEST_MODULES=capture_images make

# Convert to PNG
./convert_images.sh

# View results
cd output
ls -lh *.png
```

## Files in This Directory

### Test Scripts
- **test.py** - Basic functionality tests (VGA timing, modes, clock)
- **capture_images.py** - Captures static images of all scenes
- **capture_video.py** - Captures animation frames for video

### Helper Scripts
- **convert_images.sh** - Converts PPM to PNG
- **generate_video.sh** - Creates MP4 and GIF from frames
- **run_all_captures.sh** - Master script (runs everything)

### Documentation
- **CAPTURE_GUIDE.md** - Complete capture guide
- **README.md** - This file

### Build Files
- **Makefile** - Cocotb build configuration
- **tb.v** - Verilog testbench wrapper
- **requirements.txt** - Python dependencies

## Available Tests

### 1. Basic Tests (test.py)
```bash
make
```
Runs 3 tests:
- VGA signal generation
- Display mode switching
- Clock divider functionality

### 2. Image Capture (capture_images.py)
```bash
COCOTB_TEST_MODULES=capture_images make
```
Captures 5 static images:
- Test pattern
- Sphere
- Torus
- Kirby
- Pokemon

### 3. Video Capture (capture_video.py)
```bash
COCOTB_TEST_MODULES=capture_video make
```
Captures animation frames:
- 30 frames (default)
- 60 frames (smoother)

## Output Directory

All captured images and videos are saved to `test/output/`:

```
output/
├── test_pattern.ppm/png
├── sphere.ppm/png
├── torus.ppm/png
├── kirby.ppm/png
├── pokemon.ppm/png
├── frame_*.ppm/png (animation frames)
├── raymarcher_30fps.mp4 (video)
└── raymarcher_30fps.gif (animated GIF)
```

## Workflow

### For Static Images Only
```bash
source venv/bin/activate
cd test
COCOTB_TEST_MODULES=capture_images make
./convert_images.sh
```

### For Animation Video
```bash
source venv/bin/activate
cd test
COCOTB_TEST_MODULES=capture_video make
./generate_video.sh
```

### Complete Workflow (Everything)
```bash
source venv/bin/activate
cd test
./run_all_captures.sh
```

## Viewing Results

### On Headless Server
Download to your local machine:
```bash
scp user@server:~/ttsky-verilog-raytracing/test/output/*.png .
scp user@server:~/ttsky-verilog-raytracing/test/output/*.mp4 .
```

### With GUI
```bash
cd output
eog *.png          # View images
mpv *.mp4          # View video
```

## Performance

- **Single frame**: 2-5 minutes
- **5 static images**: 10-25 minutes
- **30 animation frames**: 30-60 minutes
- **60 animation frames**: 1-2 hours

## Troubleshooting

See **CAPTURE_GUIDE.md** for detailed troubleshooting.

Common issues:
- Missing dependencies: Run `../setup_test_env.sh`
- Virtual env not activated: Run `source ../venv/bin/activate`
- No output: Check `output/` directory was created

## Next Steps

1. Run basic tests to verify design
2. Capture static images
3. Generate animation video
4. Share your results!

For complete instructions, see **CAPTURE_GUIDE.md**.
