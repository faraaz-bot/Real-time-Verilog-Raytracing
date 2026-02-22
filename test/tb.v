`default_nettype none
`timescale 1ns / 1ps

// TinyTapeout testbench wrapper
// This testbench is required for TinyTapeout submission
// It instantiates the top module with the TinyTapeout interface

module tb;

    // TinyTapeout interface signals
    reg  clk;
    reg  rst_n;
    reg  ena;
    reg  [7:0] ui_in;
    wire [7:0] uo_out;
    reg  [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    // Dump signals for debugging
    initial begin
        $dumpfile("tb.vcd");
        $dumpvars(0, tb);
        #1;
    end

    // Instantiate the TinyTapeout top module
    // The module name must match your top_module in info.yaml
    tt_um_vga_sphere tt_um_vga_sphere_inst (
        `ifdef GL_TEST
            .VPWR(1'b1),
            .VGND(1'b0),
        `endif
        .ui_in   (ui_in),
        .uo_out  (uo_out),
        .uio_in  (uio_in),
        .uio_out (uio_out),
        .uio_oe  (uio_oe),
        .ena     (ena),
        .clk     (clk),
        .rst_n   (rst_n)
    );

    // Extract VGA signals from output for easier debugging
    wire hsync = uo_out[0];
    wire vsync = uo_out[4];
    wire [1:0] blue  = {uo_out[5], uo_out[1]};
    wire [1:0] green = {uo_out[6], uo_out[2]};
    wire [1:0] red   = {uo_out[7], uo_out[3]};

endmodule

`default_nettype wire
