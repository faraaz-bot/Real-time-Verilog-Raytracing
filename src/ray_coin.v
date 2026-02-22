`default_nettype none

// Coin surface intersection using iterative ray marching
// Uses ellipsoid SDF (flattened sphere) to create disc-like coin shape
// Z-axis compression creates the flat coin appearance

module ray_coin (
    input wire clk,
    input wire start,
    input signed [15:0] origin_x,    // Ray starting point
    input signed [15:0] origin_y,
    input signed [15:0] origin_z,
    input signed [15:0] dir_x,       // Ray direction vector
    input signed [15:0] dir_y,
    input signed [15:0] dir_z,
    input signed [15:0] light_x,     // Light direction vector
    input signed [15:0] light_y,
    input signed [15:0] light_z,
    output reg surface_hit,          // True if ray intersects coin
    output reg signed [15:0] intensity  // Surface illumination
);

// Coin geometry parameters
parameter COIN_RADIUS = 16'h0200;  // 2.0 in Q8.8 format
parameter Z_COMPRESS = 1;          // Compression factor: 2^1 = 2x flattening
parameter EDGE_DARKENING = 16'h01C0;  // Darken when radius > 1.75
parameter CENTER_RADIUS = 16'h00C0;   // Darken when radius < 0.75

// Current sample position along ray
reg signed [15:0] pos_x, pos_y, pos_z;
// Ray direction (constant during marching)
reg signed [15:0] ray_x, ray_y, ray_z;
// Accumulated distance traveled
reg signed [15:0] total_dist;
// Store radial distance for edge/center darkening
reg [15:0] radial_dist;

// Light direction passed through
wire signed [15:0] lit_x = light_x;
wire signed [15:0] lit_y = light_y;
wire signed [15:0] lit_z = light_z;

// First CORDIC: XY-plane magnitude and light rotation
wire [15:0] mag_xy;
wire signed [15:0] lit_rotated_xy;

vec_rotate3 magnitude_xy (
    .vec_x(pos_x),
    .vec_y(pos_y),
    .aux_x(lit_x),
    .aux_y(lit_y),
    .magnitude(mag_xy),
    .aux_rotated(lit_rotated_xy)
);

// Apply Z-axis compression for ellipsoid shape
wire signed [15:0] pos_z_compressed = pos_z <<< Z_COMPRESS;

// Second CORDIC: combine compressed Z with XY for ellipsoid distance
wire [15:0] mag_3d;
wire signed [15:0] lit_rotated_3d;

vec_rotate2 magnitude_full (
    .vec_x(pos_z_compressed),
    .vec_y($signed(mag_xy)),
    .aux_x(lit_z),
    .aux_y(lit_rotated_xy),
    .magnitude(mag_3d),
    .aux_rotated(lit_rotated_3d)
);

// Signed distance to ellipsoid surface
wire signed [15:0] sdf = $signed(mag_3d) - $signed(COIN_RADIUS);

// Ray step calculator
wire signed [15:0] step_x, step_y, step_z;

dist_scale3d ray_step (
    .d(sdf[10:0]),
    .xin_(ray_x),
    .yin_(ray_y),
    .zin_(ray_z),
    .xout(step_x),
    .yout(step_y),
    .zout(step_z)
);

// Calculate radial-based darkening factor
// Darken both edges (far from center) and center (close to center)
wire [15:0] edge_factor = (mag_xy > EDGE_DARKENING) ? 
                          ((mag_xy - EDGE_DARKENING) << 4) : 16'h0000;
wire [15:0] center_factor = (mag_xy < CENTER_RADIUS) ? 
                            ((CENTER_RADIUS - mag_xy) << 5) : 16'h0000;
wire [15:0] darkening = edge_factor + center_factor;

// Apply darkening to lighting intensity (more aggressive)
wire signed [15:0] darkened_intensity = lit_rotated_3d - ($signed(darkening) << 1);

// State machine: iteratively march along ray
always @(posedge clk) begin
    if (start) begin
        ray_x <= dir_x;
        ray_y <= dir_y;
        ray_z <= dir_z;
        pos_x <= origin_x;
        pos_y <= origin_y;
        pos_z <= origin_z;
        total_dist <= 512;
        surface_hit <= 1;
        radial_dist <= 0;
    end else begin
        total_dist <= total_dist + sdf;
        surface_hit <= surface_hit & ((total_dist + sdf) < 2048);
        pos_x <= pos_x + step_x + (step_x >>> 2);
        pos_y <= pos_y + step_y + (step_y >>> 2);
        pos_z <= pos_z + step_z + (step_z >>> 2);
        radial_dist <= mag_xy;
    end
    intensity <= darkened_intensity;
end

endmodule  // ray_coin

`default_nettype wire
