`default_nettype none

// Scene renderer: golden coin with checkerboard floor and sky
// Combines coin ray marching with procedural floor pattern
// Uses gold color palette for metallic coin appearance

module scene_coin (
    input wire clk,
    input wire rst_n,
    input wire [10:0] h_count,
    input wire [9:0] v_count,
    input wire [0:0] frame,
    output reg [1:0] r_out,
    output reg [1:0] g_out,
    output reg [1:0] b_out
);

// Display timing
parameter H_ACTIVE = 640;
parameter V_ACTIVE = 480;

// Coin geometry computation
wire is_coin;
wire [5:0] coin_brightness;

coin_core coin_renderer (
    .clk(clk),
    .rst_n(rst_n),
    .h_count(h_count),
    .v_count(v_count),
    .frame(frame),
    .coin_visible(is_coin),
    .coin_luma(coin_brightness)
);

// Ground plane: lower half of screen (horizon at scanline 240)
wire is_ground = (v_count > 10'd240);

// Checkerboard pattern using position bits
wire tile_parity = h_count[5] ^ v_count[4];

// Ground colors
wire [5:0] tile_bright = 6'd40;
wire [5:0] tile_dim = 6'd20;
wire [5:0] ground_shade = tile_parity ? tile_bright : tile_dim;

// Sky gradient: blue fades from top to horizon
wire [9:0] gradient_factor = (v_count >> 2) + (v_count >> 4) + (v_count >> 5);
wire [5:0] sky_intensity = (gradient_factor > 6'd44) ? 6'd16 : (6'd60 - gradient_factor[5:0]);

// Calculate radial position from screen center for edge darkening
wire signed [10:0] dx = $signed(h_count) - 11'd320;
wire signed [9:0] dy = $signed(v_count) - 10'd240;
wire [10:0] dx_abs = dx[10] ? -dx : dx;
wire [9:0] dy_abs = dy[9] ? -dy : dy;
wire [11:0] radial_approx = {1'b0, dx_abs} + {2'b0, dy_abs};

// Edge darkening: darken outer edge of coin
wire is_edge = is_coin && (radial_approx > 12'd140);
wire [5:0] darkened_brightness = is_edge ? (coin_brightness >> 2) : coin_brightness;

// Gold color palette for metallic coin appearance
// Red channel is brightest, green slightly less, blue minimal for warm gold
wire [5:0] gold_red = darkened_brightness;
wire [5:0] gold_green = (darkened_brightness > 6'd8) ? (darkened_brightness - 6'd8) : 6'd0;
wire [5:0] gold_blue = (darkened_brightness > 6'd40) ? ((darkened_brightness - 6'd40) >> 1) : 6'd0;

// Composite scene colors (6-bit per channel)
wire [5:0] red_channel, green_channel, blue_channel;

// Layer priority: coin (foreground) > ground > sky (background)
assign red_channel = is_coin ? gold_red : 
                     is_ground ? ground_shade : 6'd0;
assign green_channel = is_coin ? gold_green : 
                       is_ground ? ground_shade : 6'd0;
assign blue_channel = is_coin ? gold_blue : 
                      is_ground ? ground_shade : sky_intensity;

// Ordered dithering matrix indices
wire [2:0] dither_col = h_count[2:0] ^ {3{frame[0]}};
wire [1:0] dither_row = v_count[1:0];
wire [2:0] dither_mixed = {dither_col[2], dither_col[1] ^ dither_row[1], dither_col[0] ^ dither_row[0]};
wire [4:0] dither_threshold = {dither_mixed[0], dither_col[0], dither_mixed[1], dither_col[1], dither_mixed[2]};

// Quantization with ordered dithering
function [1:0] quantize_with_dither;
    input [5:0] intensity;
    input [4:0] threshold;
    begin
        quantize_with_dither = ({1'b0, intensity} + {2'b0, threshold} + intensity[0] + intensity[5] + intensity[5:1]) >> 5;
    end
endfunction

wire [1:0] red_final = quantize_with_dither(red_channel, dither_threshold);
wire [1:0] green_final = quantize_with_dither(green_channel, dither_threshold);
wire [1:0] blue_final = quantize_with_dither(blue_channel, dither_threshold);

// Blanking region handling
wire in_visible_area = (h_count < H_ACTIVE) && (v_count < V_ACTIVE);

always @(posedge clk) begin
    r_out <= in_visible_area ? red_final : 2'b00;
    g_out <= in_visible_area ? green_final : 2'b00;
    b_out <= in_visible_area ? blue_final : 2'b00;
end

endmodule  // scene_coin

`default_nettype wire
