`default_nettype none

// Sphere surface intersection using iterative ray marching
// Computes signed distance function (SDF) for a sphere centered at origin
//
// Distance calculation uses cascaded CORDIC operations:
//   First: compute 2D magnitude in XY plane
//   Second: combine with Z to get full 3D magnitude
//   SDF value: magnitude - sphere_radius
//
// The CORDIC auxiliary rotation provides surface normal direction
// which directly yields diffuse lighting intensity

module ray_sphere (
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
    output reg surface_hit,          // True if ray intersects sphere
    output reg signed [15:0] intensity  // Surface illumination
);

// Sphere geometry: radius in Q8.8 fixed-point format
parameter SPHERE_RADIUS = 16'h0200;  // Represents 2.0

// Current sample position along ray
reg signed [15:0] pos_x, pos_y, pos_z;
// Ray direction (constant during marching)
reg signed [15:0] ray_x, ray_y, ray_z;
// Accumulated distance traveled
reg signed [15:0] total_dist;

// Light direction passed through to CORDIC
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

// Second CORDIC: combine Z with XY magnitude for 3D length
wire [15:0] mag_3d;
wire signed [15:0] lit_rotated_3d;

vec_rotate2 magnitude_full (
    .vec_x(pos_z),
    .vec_y($signed(mag_xy)),
    .aux_x(lit_z),
    .aux_y(lit_rotated_xy),
    .magnitude(mag_3d),
    .aux_rotated(lit_rotated_3d)
);

// Signed distance: positive outside sphere, negative inside
wire signed [15:0] sdf = $signed(mag_3d) - $signed(SPHERE_RADIUS);

// Ray step calculator: scales direction by distance
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

// State machine: iteratively march along ray
always @(posedge clk) begin
    if (start) begin
        // Initialize ray march state
        ray_x <= dir_x;
        ray_y <= dir_y;
        ray_z <= dir_z;
        pos_x <= origin_x;
        pos_y <= origin_y;
        pos_z <= origin_z;
        total_dist <= 512;
        surface_hit <= 1;
    end else begin
        // Advance ray position by SDF distance
        total_dist <= total_dist + sdf;
        // Mark as miss if ray traveled too far
        surface_hit <= surface_hit & ((total_dist + sdf) < 2048);
        // Move sample point along ray direction
        // Scale factor: 1.25 = 1 + 0.25 for faster convergence
        pos_x <= pos_x + step_x + (step_x >>> 2);
        pos_y <= pos_y + step_y + (step_y >>> 2);
        pos_z <= pos_z + step_z + (step_z >>> 2);
    end
    // Lighting: rotated auxiliary vector gives dot(normal, light)
    intensity <= lit_rotated_3d;
end

endmodule  // ray_sphere

`default_nettype wire
