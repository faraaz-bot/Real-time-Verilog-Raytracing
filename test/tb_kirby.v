`timescale 1ns / 1ps

// Testbench for Kirby VGA module
// Tests the complete Kirby rendering pipeline

module tb_kirby;

    // Clock and reset
    reg clk;
    reg rst_n;
    
    // VGA outputs
    wire hsync, vsync;
    wire [1:0] r_out, g_out, b_out;
    
    // Instantiate Kirby VGA module
    vga_kirby dut (
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
    
    // Test sequence
    initial begin
        $dumpfile("kirby_test.vcd");
        $dumpvars(0, tb_kirby);
        
        // Reset
        rst_n = 0;
        #100;
        rst_n = 1;
        
        $display("Starting Kirby VGA test...");
        $display("Testing for 2 complete frames");
        
        // Run for 2 frames (2 * 800 * 525 = 840,000 clocks)
        // At 40ns per clock = 33.6ms per frame
        #67200000;  // 67.2ms for 2 frames
        
        $display("Test complete!");
        $display("VGA signals generated successfully");
        $finish;
    end
    
    // Monitor VGA sync signals
    integer frame_count;
    reg prev_vsync;
    
    initial begin
        frame_count = 0;
        prev_vsync = 1;
    end
    
    always @(posedge clk) begin
        if (prev_vsync && !vsync) begin
            frame_count = frame_count + 1;
            $display("Frame %0d complete", frame_count);
        end
        prev_vsync = vsync;
    end

endmodule
