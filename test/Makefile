# Makefile for TinyTapeout VGA Sphere Ray Marcher
# Compatible with TinyTapeout cocotb testing framework

# Defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# TinyTapeout project sources (must match info.yaml source_files)
# Separate files with spaces as required by TinyTapeout guide
PROJECT_SOURCES = tt_um_vga_sphere.v vga_sphere.v sphere_core.v ray_sphere.v vec_rotate2.v vec_rotate3.v dist_scale3d.v

# Add source path prefix
VERILOG_SOURCES += $(addprefix $(PWD)/../src/, $(PROJECT_SOURCES))

# Testbench
VERILOG_SOURCES += $(PWD)/tb.v

# Top-level module (the testbench module name)
TOPLEVEL = tb

# Python cocotb test module
MODULE = test

# Include cocotb makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# ============================================================================
# Additional targets for development/debugging
# ============================================================================

# Test individual modules
test-cordic: VERILOG_SOURCES = $(PWD)/../src/vec_rotate2.v
test-cordic: TOPLEVEL = vec_rotate2
test-cordic: MODULE = test_cordic
test-cordic:
	$(MAKE) sim

test-cordic3: VERILOG_SOURCES = $(PWD)/../src/vec_rotate3.v
test-cordic3: TOPLEVEL = vec_rotate3
test-cordic3: MODULE = test_cordic
test-cordic3:
	$(MAKE) sim

test-step3vec: VERILOG_SOURCES = $(PWD)/../src/dist_scale3d.v
test-step3vec: TOPLEVEL = dist_scale3d
test-step3vec: MODULE = test_step3vec
test-step3vec:
	$(MAKE) sim

test-spherehit: VERILOG_SOURCES = $(PWD)/../src/ray_sphere.v $(PWD)/../src/vec_rotate2.v $(PWD)/../src/vec_rotate3.v $(PWD)/../src/dist_scale3d.v
test-spherehit: TOPLEVEL = ray_sphere
test-spherehit: MODULE = test_spherehit
test-spherehit:
	$(MAKE) sim

# Run with iverilog standalone (no cocotb)
iverilog-sim:
	mkdir -p output
	iverilog -o tb.vvp -I../src $(PWD)/../src/tt_um_vga_sphere.v $(PWD)/../src/vga_sphere.v $(PWD)/../src/sphere_core.v $(PWD)/../src/ray_sphere.v $(PWD)/../src/vec_rotate2.v $(PWD)/../src/vec_rotate3.v $(PWD)/../src/dist_scale3d.v $(PWD)/tb.v
	vvp tb.vvp

# Quick syntax check for all sources
check:
	iverilog -o /dev/null -I../src $(addprefix $(PWD)/../src/, $(PROJECT_SOURCES))
	@echo "Syntax check passed!"

# Check TinyTapeout top module specifically
check-tt:
	iverilog -o /dev/null -I../src $(PWD)/../src/tt_um_vga_sphere.v $(PWD)/../src/vga_sphere.v $(PWD)/../src/sphere_core.v $(PWD)/../src/ray_sphere.v $(PWD)/../src/vec_rotate2.v $(PWD)/../src/vec_rotate3.v $(PWD)/../src/dist_scale3d.v
	@echo "TinyTapeout module check passed!"

# Clean all generated files
clean-all: clean
	rm -rf output
	rm -f *.vcd *.vvp
	rm -f results.xml
	rm -rf sim_build
	rm -rf __pycache__

# Run VGA simulation using existing Python script
vga-sim:
	python3 ../run.py quick

.PHONY: iverilog-sim check check-tt clean-all vga-sim test-cordic test-cordic3 test-step3vec test-spherehit
