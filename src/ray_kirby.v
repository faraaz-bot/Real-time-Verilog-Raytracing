`default_nettype none

// Kirby character using composite SDF raymarching
// Combines multiple shapes: body sphere, arms, feet, eyes, cheeks, mouth
// Uses smooth min operations for organic blending

module ray_kirby (
    input wire clk,
    input wire start,
    input signed [15:0] origin_x,
    input signed [15:0] origin_y,
    input signed [15:0] origin_z,
    input signed [15:0] dir_x,
    input signed [15:0] dir_y,
    input signed [15:0] dir_z,
    input signed [15:0] light_x,
    input signed [15:0] light_y,
    input signed [15:0] light_z,
    output reg surface_hit,
    output reg signed [15:0] intensity,
    output reg [2:0] feature_id  // Which part of Kirby was hit
);

// Kirby geometry parameters (Q8.8 fixed-point)
parameter BODY_RADIUS = 16'h0200;      // Main body sphere: 2.0
parameter ARM_RADIUS = 16'h0080;       // Arms: 0.5
parameter FOOT_RADIUS = 16'h00C0;      // Feet: 0.75
parameter EYE_RADIUS = 16'h0060;       // Eyes: 0.375
parameter CHEEK_RADIUS = 16'h0050;     // Cheeks: 0.3125
parameter MOUTH_RADIUS = 16'h0030;     // Mouth: 0.1875

// Feature positions (relative to body center)
parameter ARM_OFFSET_X = 16'h0180;     // Arms at ±1.5 units
parameter ARM_OFFSET_Y = 16'h0040;     // Arms slightly up
parameter FOOT_OFFSET_X = 16'h00C0;    // Feet at ±0.75 units
parameter FOOT_OFFSET_Y = -16'h0180;   // Feet down -1.5
parameter EYE_OFFSET_X = 16'h0080;     // Eyes at ±0.5 units
parameter EYE_OFFSET_Y = 16'h0080;     // Eyes up 0.5
parameter EYE_OFFSET_Z = 16'h0180;     // Eyes forward 1.5
parameter CHEEK_OFFSET_X = 16'h0100;   // Cheeks at ±1.0 units
parameter CHEEK_OFFSET_Z = 16'h0140;   // Cheeks forward 1.25
parameter MOUTH_OFFSET_Y = 16'h0020;   // Mouth slightly up
parameter MOUTH_OFFSET_Z = 16'h0180;   // Mouth forward 1.5

// Current sample position along ray
reg signed [15:0] pos_x, pos_y, pos_z;
reg signed [15:0] ray_x, ray_y, ray_z;
reg signed [15:0] total_dist;
reg [2:0] closest_feature;

// Helper function: sphere SDF
function signed [15:0] sphere_sdf;
    input signed [15:0] px, py, pz;
    input signed [15:0] cx, cy, cz;
    input signed [15:0] radius;
    reg signed [15:0] dx, dy, dz;
    reg signed [15:0] mag_xy, mag_3d;
    begin
        dx = px - cx;
        dy = py - cy;
        dz = pz - cz;
        // Approximate magnitude (simplified)
        mag_xy = (dx[15] ? -dx : dx) + (dy[15] ? -dy : dy);
        mag_3d = mag_xy + (dz[15] ? -dz : dz);
        sphere_sdf = mag_3d - radius;
    end
endfunction

// Smooth minimum for blending (k=0.5)
function signed [15:0] smooth_min;
    input signed [15:0] a, b;
    reg signed [15:0] diff, h;
    begin
        diff = (a > b) ? (a - b) : (b - a);
        h = (diff < 16'h0080) ? (16'h0080 - diff) : 16'h0000;
        smooth_min = ((a < b) ? a : b) - ((h * h) >>> 10);
    end
endfunction

// Compute composite SDF for all Kirby features
wire signed [15:0] body_sdf = sphere_sdf(pos_x, pos_y, pos_z, 16'sd0, 16'sd0, 16'sd0, BODY_RADIUS);
wire signed [15:0] arm_l_sdf = sphere_sdf(pos_x, pos_y, pos_z, -ARM_OFFSET_X, ARM_OFFSET_Y, 16'sd0, ARM_RADIUS);
wire signed [15:0] arm_r_sdf = sphere_sdf(pos_x, pos_y, pos_z, ARM_OFFSET_X, ARM_OFFSET_Y, 16'sd0, ARM_RADIUS);
wire signed [15:0] foot_l_sdf = sphere_sdf(pos_x, pos_y, pos_z, -FOOT_OFFSET_X, FOOT_OFFSET_Y, 16'sd0, FOOT_RADIUS);
wire signed [15:0] foot_r_sdf = sphere_sdf(pos_x, pos_y, pos_z, FOOT_OFFSET_X, FOOT_OFFSET_Y, 16'sd0, FOOT_RADIUS);
wire signed [15:0] eye_l_sdf = sphere_sdf(pos_x, pos_y, pos_z, -EYE_OFFSET_X, EYE_OFFSET_Y, EYE_OFFSET_Z, EYE_RADIUS);
wire signed [15:0] eye_r_sdf = sphere_sdf(pos_x, pos_y, pos_z, EYE_OFFSET_X, EYE_OFFSET_Y, EYE_OFFSET_Z, EYE_RADIUS);
wire signed [15:0] cheek_l_sdf = sphere_sdf(pos_x, pos_y, pos_z, -CHEEK_OFFSET_X, 16'sd0, CHEEK_OFFSET_Z, CHEEK_RADIUS);
wire signed [15:0] cheek_r_sdf = sphere_sdf(pos_x, pos_y, pos_z, CHEEK_OFFSET_X, 16'sd0, CHEEK_OFFSET_Z, CHEEK_RADIUS);
wire signed [15:0] mouth_sdf = sphere_sdf(pos_x, pos_y, pos_z, 16'sd0, MOUTH_OFFSET_Y, MOUTH_OFFSET_Z, MOUTH_RADIUS);

// Blend body with arms and feet
wire signed [15:0] body_arms = smooth_min(body_sdf, smooth_min(arm_l_sdf, arm_r_sdf));
wire signed [15:0] body_feet = smooth_min(body_arms, smooth_min(foot_l_sdf, foot_r_sdf));

// Final SDF (body + limbs, but eyes/cheeks/mouth are separate for coloring)
wire signed [15:0] sdf = body_feet;

// Determine which feature is closest for coloring
wire [2:0] feature = (eye_l_sdf < 16'sd20 || eye_r_sdf < 16'sd20) ? 3'd1 :  // Eyes
                     (cheek_l_sdf < 16'sd20 || cheek_r_sdf < 16'sd20) ? 3'd2 :  // Cheeks
                     (mouth_sdf < 16'sd20) ? 3'd3 :  // Mouth
                     (foot_l_sdf < body_sdf || foot_r_sdf < body_sdf) ? 3'd4 :  // Feet
                     3'd0;  // Body/arms

// Simple normal approximation (gradient of SDF)
wire signed [15:0] normal_x = pos_x;
wire signed [15:0] normal_y = pos_y;
wire signed [15:0] normal_z = pos_z;

// Lighting calculation
wire signed [31:0] dot_raw = (normal_x * light_x + normal_y * light_y + normal_z * light_z);
wire signed [15:0] lit_intensity = dot_raw >>> 8;

// Ray stepping
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

// Raymarching state machine
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
        closest_feature <= 0;
    end else begin
        total_dist <= total_dist + sdf;
        surface_hit <= surface_hit & ((total_dist + sdf) < 2048);
        pos_x <= pos_x + step_x + (step_x >>> 2);
        pos_y <= pos_y + step_y + (step_y >>> 2);
        pos_z <= pos_z + step_z + (step_z >>> 2);
        closest_feature <= feature;
    end
    intensity <= lit_intensity;
    feature_id <= closest_feature;
end

endmodule  // ray_kirby

`default_nettype wire
