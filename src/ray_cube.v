`default_nettype none

// Cube surface intersection using iterative ray marching
// Computes signed distance function (SDF) for a cube centered at origin
//
// Uses box SDF: distance to nearest face of axis-aligned cube
// The SDF is computed using max of axis distances
//
// Similar structure to ray_sphere but with box SDF instead of sphere SDF

module ray_cube (
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
    output reg surface_hit,          // True if ray intersects cube
    output reg signed [15:0] intensity  // Surface illumination
);

// Cube geometry: half-size in Q8.8 fixed-point format
parameter CUBE_SIZE = 16'h0180;  // Represents 1.5

// Current sample position along ray
reg signed [15:0] pos_x, pos_y, pos_z;
// Ray direction (constant during marching)
reg signed [15:0] ray_x, ray_y, ray_z;
// Accumulated distance traveled
reg signed [15:0] total_dist;

// Compute absolute values for box SDF
wire signed [15:0] abs_x = (pos_x[15]) ? -pos_x : pos_x;
wire signed [15:0] abs_y = (pos_y[15]) ? -pos_y : pos_y;
wire signed [15:0] abs_z = (pos_z[15]) ? -pos_z : pos_z;

// Distance to each face
wire signed [15:0] dist_x = abs_x - CUBE_SIZE;
wire signed [15:0] dist_y = abs_y - CUBE_SIZE;
wire signed [15:0] dist_z = abs_z - CUBE_SIZE;

// Box SDF: max of all axis distances
// If all negative, we're inside; if any positive, distance to nearest face
wire signed [15:0] max_xy = (dist_x > dist_y) ? dist_x : dist_y;
wire signed [15:0] sdf = (max_xy > dist_z) ? max_xy : dist_z;

// Determine which face we're closest to for normal calculation
wire face_x = (dist_x >= dist_y) && (dist_x >= dist_z);
wire face_y = (dist_y >= dist_x) && (dist_y >= dist_z);
wire face_z = (dist_z >= dist_x) && (dist_z >= dist_y);

// Normal vector based on closest face
wire signed [15:0] normal_x = face_x ? (pos_x[15] ? 16'sd256 : -16'sd256) : 16'sd0;
wire signed [15:0] normal_y = face_y ? (pos_y[15] ? 16'sd256 : -16'sd256) : 16'sd0;
wire signed [15:0] normal_z = face_z ? (pos_z[15] ? 16'sd256 : -16'sd256) : 16'sd0;

// Lighting: dot product of normal and light direction
wire signed [31:0] dot_raw = (normal_x * light_x + normal_y * light_y + normal_z * light_z);
wire signed [15:0] lit_intensity = dot_raw >>> 8;

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
    // Lighting from computed normal
    intensity <= lit_intensity;
end

endmodule  // ray_cube

`default_nettype wire
