`default_nettype none

// VGA controller for sphere with floor scene
// Manages 640x480 @ 60Hz timing and coordinates scene rendering
// Integrates sphere ray marching with checkerboard floor

module vga_scene_sphere (
    input wire clk,              // 25.175 MHz pixel clock
    input wire rst_n,            // Active-low reset
    output wire hsync,           // Horizontal sync (active low)
    output wire vsync,           // Vertical sync (active low)
    output wire [1:0] r_out,     // Red channel (2-bit)
    output wire [1:0] g_out,     // Green channel (2-bit)
    output wire [1:0] b_out      // Blue channel (2-bit)
);

// VGA timing constants (640x480 @ 60Hz)
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

// Position and frame counters
reg [10:0] pixel_x;
reg [9:0] pixel_y;
reg [0:0] frame_toggle;

// Sync generation (active low pulses)
assign hsync = ~(pixel_x >= (H_ACTIVE + H_FRONT) && 
                 pixel_x < (H_ACTIVE + H_FRONT + H_SYNC));
assign vsync = ~(pixel_y >= (V_ACTIVE + V_FRONT) && 
                 pixel_y < (V_ACTIVE + V_FRONT + V_SYNC));

// Scene renderer instantiation
scene_sphere scene_renderer (
    .clk(clk),
    .rst_n(rst_n),
    .h_count(pixel_x),
    .v_count(pixel_y),
    .frame(frame_toggle),
    .r_out(r_out),
    .g_out(g_out),
    .b_out(b_out)
);

// Raster scan counter logic
always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        pixel_x <= 0;
        pixel_y <= 0;
        frame_toggle <= 0;
    end else begin
        if (pixel_x == H_TOTAL - 1) begin
            pixel_x <= 0;
            if (pixel_y == V_TOTAL - 1) begin
                pixel_y <= 0;
                frame_toggle <= frame_toggle + 1;
            end else begin
                pixel_y <= pixel_y + 1;
            end
        end else begin
            pixel_x <= pixel_x + 1;
        end
    end
end

endmodule  // vga_scene_sphere

`default_nettype wire
