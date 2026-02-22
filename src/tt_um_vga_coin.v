`default_nettype none

// TinyTapeout wrapper for VGA coin with floor scene
// Outputs via TinyVGA PMOD connector
// Renders golden coin with checkerboard floor
//
// Hardware requirements:
// - 25.175 MHz clock for VGA 640x480 @ 60Hz
// - TinyVGA PMOD on output pins

module tt_um_vga_coin (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // Always 1 when the design is powered
    input  wire       clk,      // Clock (used directly as pixel clock)
    input  wire       rst_n     // Reset (active low)
);

    // VGA output signals
    wire h_sync;
    wire v_sync;
    wire [1:0] red;
    wire [1:0] green;
    wire [1:0] blue;

    // Coin scene renderer with VGA timing
    vga_scene_coin renderer (
        .clk(clk),
        .rst_n(rst_n),
        .vsync(v_sync),
        .hsync(h_sync),
        .r_out(red),
        .g_out(green),
        .b_out(blue)
    );

    // TinyVGA PMOD signal mapping:
    // Bit 0: HSYNC
    // Bit 1: B[0]
    // Bit 2: G[0]
    // Bit 3: R[0]
    // Bit 4: VSYNC
    // Bit 5: B[1]
    // Bit 6: G[1]
    // Bit 7: R[1]
    assign uo_out = {red[1], green[1], blue[1], v_sync, red[0], green[0], blue[0], h_sync};

    // Bidirectional pins unused (configured as inputs)
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Unused input warning suppression
    wire _unused = &{ena, ui_in, uio_in};

endmodule

`default_nettype wire
