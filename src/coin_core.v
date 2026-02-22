`default_nettype none

// Ray-marched coin renderer with animated camera
// Creates a flat disc shape using compressed ellipsoid SDF
// Camera orbits using incremental rotation updates

module coin_core (
    input wire clk,
    input wire rst_n,
    input wire [10:0] h_count,
    input wire [9:0] v_count,
    input wire [0:0] frame,
    output reg coin_visible,
    output reg [5:0] coin_luma
);

// Display timing constants
parameter H_VISIBLE = 640;
parameter H_TOTAL = 800;
parameter V_TOTAL = 525;

// Camera orientation using incremental rotation
reg signed [15:0] cos_a, sin_a, cos_b, sin_b;
reg signed [15:0] sin_ab, cos_ab, sin_a_cos_b, cos_a_cos_b;

// Rotation angle updates
wire signed [15:0] cos_a_next = cos_a - (sin_a >>> 5);
wire signed [15:0] sin_a_next = sin_a + (cos_a_next >>> 5);
wire signed [15:0] cos_ab_next = cos_ab - (sin_ab >>> 5);
wire signed [15:0] sin_ab_next = sin_ab + (cos_ab_next >>> 5);
wire signed [15:0] cos_a_cos_b_next = cos_a_cos_b - (sin_a_cos_b >>> 5);
wire signed [15:0] sin_a_cos_b_next = sin_a_cos_b + (cos_a_cos_b_next >>> 5);

wire signed [15:0] cos_b_next = cos_b - (sin_b >>> 6);
wire signed [15:0] sin_b_next = sin_b + (cos_b_next >>> 6);
wire signed [15:0] cos_a_cos_b_2 = cos_a_cos_b_next - (cos_ab_next >>> 6);
wire signed [15:0] cos_ab_2 = cos_ab_next + (cos_a_cos_b_2 >>> 6);
wire signed [15:0] sin_a_cos_b_2 = sin_a_cos_b_next - (sin_ab_next >>> 6);
wire signed [15:0] sin_ab_2 = sin_ab_next + (sin_a_cos_b_2 >>> 6);

// Ray direction accumulators
reg signed [21:0] scanline_cos, scanline_sin;
reg signed [21:0] ray_x_acc, ray_y_acc, ray_z_acc;

// Camera position
wire signed [15:0] cam_x = ((sin_b >>> 2) + sin_b) >>> 4;
wire signed [15:0] cam_y = ((sin_a_cos_b >>> 2) + sin_a_cos_b) >>> 4;
wire signed [15:0] cam_z = -((cos_a_cos_b >>> 2) + cos_a_cos_b) >>> 4;

// Per-scanline ray direction increments
wire signed [15:0] y_inc_cos = cos_a >>> 2;
wire signed [15:0] y_inc_sin = sin_a >>> 2;
wire signed [15:0] x_inc_x = cos_b;
wire signed [15:0] x_inc_y = -sin_ab;
wire signed [15:0] x_inc_z = cos_ab;

wire signed [21:0] center_offset_y = (x_inc_y << 5) + (x_inc_y << 3);
wire signed [21:0] center_offset_z = -((x_inc_z << 5) + (x_inc_z << 3));

// Ray origin
wire signed [15:0] ray_origin_x = cam_x + {{6{ray_x_acc[21]}}, ray_x_acc[20:11]};
wire signed [15:0] ray_origin_y = cam_y + {{6{ray_y_acc[21]}}, ray_y_acc[20:11]};
wire signed [15:0] ray_origin_z = cam_z + {{6{ray_z_acc[21]}}, ray_z_acc[20:11]};

// Light direction
wire signed [15:0] light_dir_x = sin_b >>> 2;
wire signed [15:0] light_dir_y = (sin_a_cos_b - cos_a) >>> 2;
wire signed [15:0] light_dir_z = (-cos_a_cos_b - sin_a) >>> 2;

// Coin intersection results
wire signed [15:0] raw_intensity;
wire raw_hit;

wire [3:0] query_phase = {v_count[0] ^ frame[0], v_count[0], v_count[1] ^ frame[0], 1'b0};

ray_coin coin_intersect (
    .clk(clk),
    .start(h_count[3:0] == query_phase && h_count < H_VISIBLE - 8),
    .origin_x(ray_origin_x),
    .origin_y(ray_origin_y),
    .origin_z(ray_origin_z),
    .dir_x(ray_x_acc[21:6]),
    .dir_y(ray_y_acc[21:6]),
    .dir_z(ray_z_acc[21:6]),
    .light_x(light_dir_x),
    .light_y(light_dir_y),
    .light_z(light_dir_z),
    .surface_hit(raw_hit),
    .intensity(raw_intensity)
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        // Initial camera orientation
        cos_a <= 16'h2d3f;
        sin_a <= 16'h2d3f;
        cos_b <= 16'h4000;
        sin_b <= 16'h0000;
        sin_ab <= 16'h0000;
        cos_ab <= 16'h0000;
        sin_a_cos_b <= 16'h2d3f;
        cos_a_cos_b <= 16'h2d3f;
        
        coin_visible <= 0;
        coin_luma <= 0;
    end else begin
        if (h_count == H_TOTAL - 15) begin
            if (v_count == V_TOTAL - 1) begin
                scanline_cos <= -(y_inc_cos << 8) + (y_inc_cos << 4);
                scanline_sin <= -(y_inc_sin << 8) + (y_inc_sin << 4);

                // Update camera rotation
                if (sin_b[15] && !sin_b_next[15]) begin
                    cos_a <= 16'h2d3f;
                    sin_a <= 16'h2d3f;
                    cos_b <= 16'h4000;
                    sin_b <= 16'h0000;
                    sin_ab <= 16'h0000;
                    cos_ab <= 16'h0000;
                    sin_a_cos_b <= 16'h2d3f;
                    cos_a_cos_b <= 16'h2d3f;
                end else begin
                    cos_a <= cos_a_next;
                    sin_a <= sin_a_next;
                    cos_b <= cos_b_next;
                    sin_b <= sin_b_next;
                    cos_ab <= cos_ab_2;
                    sin_ab <= sin_ab_2;
                    cos_a_cos_b <= cos_a_cos_b_2;
                    sin_a_cos_b <= sin_a_cos_b_2;
                end
            end else begin
                scanline_cos <= scanline_cos + y_inc_cos;
                scanline_sin <= scanline_sin + y_inc_sin;
                ray_x_acc <= -((x_inc_x << 5) + (x_inc_x << 3)) - (sin_b << 6);
                ray_y_acc <= scanline_cos - center_offset_y - (sin_a_cos_b << 6);
                ray_z_acc <= scanline_sin + center_offset_z + (cos_a_cos_b << 6);
            end
        end else if (h_count < H_VISIBLE - 8) begin
            if (h_count[3:0] == query_phase) begin
                coin_visible <= raw_hit;
                coin_luma <= {!raw_intensity[13], raw_intensity[12:8]};
            end else if (h_count[2:0] == 7) begin
                ray_x_acc <= ray_x_acc + x_inc_x;
                ray_y_acc <= ray_y_acc + x_inc_y;
                ray_z_acc <= ray_z_acc + x_inc_z;
            end
        end
    end
end

endmodule  // coin_core

`default_nettype wire
