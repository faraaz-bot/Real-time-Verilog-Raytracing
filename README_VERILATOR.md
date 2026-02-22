# Verilator Build System for VGA Ray Tracer

This document explains how to use the new Verilator-based build system for significantly faster simulation performance.

## Overview

Verilator is a high-performance Verilog simulator that compiles Verilog to C++, resulting in **10-100x faster** simulation speeds compared to Icarus Verilog.

### Performance Comparison

| Simulator       | 40 Frames | Speed      |
|----------------|-----------|------------|
| Icarus Verilog | 30-60 sec | Baseline   |
| Verilator      | 1-5 sec   | **10-60x** |

## Installation

### Windows

**Important:** Verilator is not available via Chocolatey on Windows. Use one of these methods:

**Option A - WSL2 (Recommended for best experience):**
1. Install WSL2: `wsl --install`
2. In WSL Ubuntu: `sudo apt-get install verilator`
3. Run the script from WSL

**Option B - Manual Build (Advanced):**
1. Install MSYS2 from https://www.msys2.org/
2. In MSYS2 terminal:
   ```bash
   pacman -S mingw-w64-x86_64-verilator
   ```
3. Add to PATH: `C:\msys64\mingw64\bin`

**Option C - Use Icarus Verilog Instead:**
- Verilator setup on Windows is complex
- Continue using `run_verilog.py` with Icarus Verilog
- Icarus is already installed and working on your system

**Requirements:**
- Visual Studio (for C++ compiler) or MinGW
- Python 3.8+
- Pillow: `pip install Pillow`

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install verilator
pip install Pillow
```

### macOS

```bash
brew install verilator
pip install Pillow
```

## Usage

### Quick Start

Run everything (check tools, build, simulate, convert to frames):
```bash
python run_verilator.py
```

### Step-by-Step

1. **Check if tools are installed:**
```bash
python run_verilator.py --check
```

2. **Show installation instructions:**
```bash
python run_verilator.py --install
```

3. **Build the simulation:**
```bash
python run_verilator.py --build
```

4. **Run the simulation:**
```bash
python run_verilator.py --run
```

5. **Convert output to PNG frames:**
```bash
python run_verilator.py --convert
```

### Advanced Options

**Capture more frames:**
```bash
python run_verilator.py --frames 100
```

**Enable aggressive optimizations (even faster):**
```bash
python run_verilator.py --optimize
```

**Enable VCD waveform tracing (for debugging, slower):**
```bash
python run_verilator.py --trace
```

**Combine options:**
```bash
python run_verilator.py --optimize --frames 60
```

## How It Works

### Build Process

1. **Verilator Compilation:**
   - Verilator reads the Verilog source files
   - Generates optimized C++ code
   - Compiles C++ to native executable

2. **Testbench:**
   - C++ testbench drives the simulation
   - Captures VGA pixel data frame-by-frame
   - Writes raw RGB data to file

3. **Post-Processing:**
   - Python script converts raw data to PNG frames
   - Creates animated GIF
   - Saves to timestamped directories

### File Structure

```
build/verilator/
├── vga_sphere_wrapper.v      # Verilog wrapper module
├── tb_verilator.cpp           # C++ testbench
├── Vvga_sphere_wrapper.exe    # Compiled executable (Windows)
├── Vvga_sphere_wrapper        # Compiled executable (Linux/Mac)
└── vga_output.raw             # Raw simulation output

output/
├── frames/
│   └── sphere_verilator_TIMESTAMP/
│       ├── frame_0000.png
│       ├── frame_0001.png
│       └── ...
└── gifs/
    ├── sphere_verilator_TIMESTAMP.gif
    └── sphere_verilator_latest.gif
```

## Optimization Levels

### Standard (Default)
- `-O2` optimization
- Good balance of speed and build time
- Recommended for most use cases

### Aggressive (`--optimize`)
- `-O3` optimization
- `--x-assign fast` and `--x-initial fast`
- `--noassert` (disables assertions)
- Maximum simulation speed
- Longer build time

## Debugging

### Enable Waveform Tracing

```bash
python run_verilator.py --trace
```

This generates a `vga_sphere.vcd` file that can be viewed with GTKWave:
```bash
gtkwave build/verilator/vga_sphere.vcd
```

**Note:** Tracing significantly slows down simulation (10-20x slower).

## Comparison with Icarus Verilog

| Feature              | Icarus Verilog | Verilator        |
|---------------------|----------------|------------------|
| Speed               | Baseline       | 10-100x faster   |
| Compilation         | Interpreted    | Compiled to C++  |
| Setup               | Simple         | Requires C++     |
| Waveforms           | Native VCD     | Optional VCD     |
| Best for            | Quick tests    | Long simulations |

## Troubleshooting

### "verilator: command not found"
- Verilator is not installed or not in PATH
- Run: `python run_verilator.py --install`

### "C++ compiler not found"
- **Windows:** Install Visual Studio or MinGW
- **Linux:** `sudo apt-get install build-essential`
- **macOS:** Install Xcode Command Line Tools

### Build fails with warnings
- Verilator is stricter than Icarus
- Check the warnings - they often indicate real issues
- Some warnings can be suppressed with `--Wno-<warning>`

### Simulation runs but produces black frames
- Check that all Verilog source files are included
- Verify the module hierarchy is correct
- Try running with `--trace` to debug

## Performance Tips

1. **Use `--optimize` for production runs**
2. **Disable tracing unless debugging**
3. **Increase `--frames` to amortize build time**
4. **Use SSD for build directory**
5. **Close other applications during simulation**

## Integration with Existing Workflow

The Verilator build system is **completely separate** from the existing Icarus Verilog workflow:

- `run_verilog.py` - Uses Icarus Verilog (slower, simpler)
- `run_verilator.py` - Uses Verilator (faster, requires C++)

Both can coexist and be used interchangeably.

## Future Enhancements

Potential improvements:
- [ ] Multi-threading support (`--threads`)
- [ ] Coverage analysis (`--coverage`)
- [ ] Incremental builds
- [ ] Support for other top-level modules (coin, floor)
- [ ] Makefile integration

## References

- [Verilator Documentation](https://verilator.org/guide/latest/)
- [Verilator GitHub](https://github.com/verilator/verilator)
- [GTKWave](http://gtkwave.sourceforge.net/)

## License

Same as the main project (Apache-2.0)
