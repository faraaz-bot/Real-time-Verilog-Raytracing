`default_nettype none

// VGA controller with ray-marched cube rendering
// Generates standard 640x480 @ 60Hz VGA timing
// Renders an animated 3D cube with dithered output

module vga_cube (
    input wire clk,
    input wire rst_n,
    output reg vsync,
    output reg hsync,
    output reg [1:0] b_out,
    output reg [1:0] g_out,
    output reg [1:0] r_out
);

// Standard VGA timing parameters (640x480 @ 60Hz)
// Requires 25.175 MHz pixel clock
parameter H_ACTIVE = 640;
parameter H_FRONT = 16;
parameter H_SYNC = 96;
parameter H_BACK = 48;
parameter H_TOTAL = 800;

parameter V_ACTIVE = 480;
parameter V_FRONT = 10;
parameter V_SYNC = 2;
parameter V_BACK = 33;
parameter V_TOTAL = 525;

// Timing counters
reg [7:0] frame_num;
reg [10:0] pixel_x;
reg [9:0] pixel_y;

// Visible region flag
wire visible = (pixel_x < H_ACTIVE) && (pixel_y < V_ACTIVE);

// Frame increment on vertical retrace
task advance_frame;
    begin
        frame_num <= frame_num + 1;
    end
endtask

// Pixel position counters
always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        pixel_x <= 0;
        pixel_y <= 0;
        frame_num <= 0;
    end else begin
        if (pixel_x == H_TOTAL - 1) begin
            pixel_x <= 0;
            if (pixel_y == V_TOTAL - 1) begin
                pixel_y <= 0;
                advance_frame;
            end else
                pixel_y <= pixel_y + 1;
        end else begin
            pixel_x <= pixel_x + 1;
        end
    end
end

// 3D cube renderer
wire is_cube;
wire [5:0] brightness;

cube_core cube_renderer (
    .clk(clk),
    .rst_n(rst_n),
    .h_count(pixel_x),
    .v_count(pixel_y),
    .cube_luma(brightness),
    .cube_visible(is_cube),
    .frame(frame_num[0:0])
);

// Scene colors: orange cube on dark blue background (same as sphere)
wire [5:0] red_val = is_cube ? brightness : 6'd8;
wire [5:0] green_val = is_cube ? (brightness >> 1) : 6'd12;
wire [5:0] blue_val = is_cube ? (brightness >> 2) : 6'd20;

// Ordered dithering pattern (8x4 Bayer matrix with temporal toggle)
wire [2:0] dither_x = pixel_x[2:0] ^ {3{frame_num[0]}};
wire [1:0] dither_y = pixel_y[1:0];
wire [2:0] dither_combined = {dither_x[2], dither_x[1] ^ dither_y[1], dither_x[0] ^ dither_y[0]};
wire [4:0] dither_val = {dither_combined[0], dither_x[0], dither_combined[1], dither_x[1], dither_combined[2]};

// Quantize 6-bit color to 2-bit with dithering
function [1:0] apply_dither;
    input [5:0] color;
    input [4:0] threshold;
    begin
        apply_dither = ({1'b0, color} + {2'b0, threshold} + color[0] + color[5] + color[5:1]) >> 5;
    end
endfunction

wire [1:0] red_out = apply_dither(red_val, dither_val);
wire [1:0] green_out = apply_dither(green_val, dither_val);
wire [1:0] blue_out = apply_dither(blue_val, dither_val);

// VGA signal generation
always @(posedge clk) begin
    // Sync pulses (active low)
    hsync <= ~((pixel_x >= (H_ACTIVE + H_FRONT)) && 
               (pixel_x < (H_ACTIVE + H_FRONT + H_SYNC)));
    vsync <= ~((pixel_y >= (V_ACTIVE + V_FRONT)) && 
               (pixel_y < (V_ACTIVE + V_FRONT + V_SYNC)));
    
    // RGB output with blanking
    r_out <= visible ? red_out : 0;
    g_out <= visible ? green_out : 0;
    b_out <= visible ? blue_out : 0;
end

endmodule  // vga_cube

`default_nettype wire
