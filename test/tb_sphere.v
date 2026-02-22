// Testbench for VGA Sphere
// Simulates the vga_sphere module and provides clock/reset

`default_nettype none
`timescale 1ns / 1ps

module tb_sphere;

    // Clock and reset
    reg clk;
    reg rst_n;
    
    // VGA outputs from DUT
    wire hsync;
    wire vsync;
    wire [1:0] r_out;
    wire [1:0] g_out;
    wire [1:0] b_out;
    
    // Instantiate the VGA sphere module
    vga_sphere dut (
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
    
    // Reset and simulation control
    initial begin
        // Initialize
        rst_n = 0;
        
        // Hold reset for a few cycles
        #100;
        rst_n = 1;
        
        // Run for enough time to generate a few frames
        // One frame = 800 * 525 = 420000 clocks = 16.8ms at 25MHz
        // Run for 3 frames = ~50ms
        #50000000;
        
        $display("Simulation complete");
        $finish;
    end
    
    // Dump waveforms
    initial begin
        $dumpfile("tb_sphere.vcd");
        $dumpvars(0, tb_sphere);
    end

endmodule

`default_nettype wire
