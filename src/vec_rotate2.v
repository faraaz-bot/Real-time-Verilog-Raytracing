`default_nettype none

// Two-iteration vectoring mode CORDIC processor
// Computes approximate magnitude of 2D input vector (vec_x, vec_y)
// Simultaneously rotates secondary vector (aux_x, aux_y) by same angle
// Returns rotated aux_x component for lighting calculations
// 
// Two iterations provide acceptable accuracy for real-time rendering
// with minimal gate delay on critical path

module vec_rotate2 (
  input signed [15:0] vec_x,
  input signed [15:0] vec_y,
  input signed [15:0] aux_x,
  input signed [15:0] aux_y,
  output [15:0] magnitude,
  output signed [15:0] aux_rotated
);

// Combinational implementation - no clock needed

// Pre-compute addition/subtraction pairs to minimize critical path
// These feed into multiplexers based on quadrant selection
wire signed [15:0] sum_xy = vec_x + vec_y;
wire signed [15:0] diff_yx = vec_y - vec_x;
wire signed [15:0] sum_aux = aux_x + aux_y;
wire signed [15:0] diff_aux = aux_y - aux_x;

// Quadrant handling for CORDIC convergence
// Initial vector must be rotated into right half-plane (positive x)
// Track sign inversions separately to reduce gate delays
wire negate_result = vec_y[15];
wire quadrant_select = vec_x[15] ^ vec_y[15];

// Iteration 1: 45-degree rotation to align vector toward x-axis
// Selection based on which quadrant the input vector occupies
wire signed [15:0] iter1_x  = quadrant_select ? diff_yx  : sum_xy;
wire signed [15:0] iter1_y  = quadrant_select ? sum_xy   : diff_yx;
wire signed [15:0] iter1_ax = quadrant_select ? diff_aux : sum_aux;
wire signed [15:0] iter1_ay = quadrant_select ? sum_aux  : diff_aux;

// Iteration 2: ~26.57-degree rotation (arctan of 0.5)
// Conditional addition/subtraction based on remaining y-sign
wire signed [15:0] iter2_x  = (negate_result ? ~iter1_x : iter1_x) + (iter1_y[15] ? ~iter1_y>>>1 : iter1_y>>>1);
wire signed [15:0] iter2_ax = (negate_result ? ~iter1_ax : iter1_ax) + (iter1_y[15] ? ~iter1_ay>>>1 : iter1_ay>>>1);

// Apply CORDIC gain compensation: multiply by ~0.6072
// Approximated as (x/2 + x/8) = 0.625 which is close enough
assign magnitude = (iter2_x >>> 1) + (iter2_x >>> 3);
assign aux_rotated = (iter2_ax >>> 1) + (iter2_ax >>> 3);

endmodule  // vec_rotate2

`default_nettype wire
