`default_nettype none

// Distance-scaled vector multiplier for ray marching
// Efficiently multiplies a 3D direction vector by a scalar distance
// Uses leading-bit detection instead of full multiplication
//
// Approximates: output = (distance * direction) >> 14
// 
// The imprecision is acceptable since ray marching iterates multiple times
// Trading accuracy for reduced gate count and critical path delay

module dist_scale3d (
  input signed [10:0] d,
  input signed [15:0] xin_,
  input signed [15:0] yin_,
  input signed [15:0] zin_,
  output reg signed [15:0] xout,
  output reg signed [15:0] yout,
  output reg signed [15:0] zout
);

// Extract sign and magnitude of distance
wire dist_neg = d[10];
wire [9:0] dist_abs = dist_neg ? ~d[9:0] : d[9:0];

// Conditionally negate inputs based on distance sign
wire [15:0] xvec = dist_neg ? ~xin_ : xin_;
wire [15:0] yvec = dist_neg ? ~yin_ : yin_;
wire [15:0] zvec = dist_neg ? ~zin_ : zin_;

// Suppress unused bit warnings
wire _unused = &{xin_[4:0], yin_[4:0], zin_[4:0], xvec[4:0], yvec[4:0], zvec[4:0]};

// Sign bits for sign extension
wire xsign = xvec[15];
wire ysign = yvec[15];
wire zsign = zvec[15];

// Leading-bit decoder determines shift amount
// Higher distance magnitude = less right shift = larger step
always @* begin
  casez (dist_abs)
    10'b1?????????:  // Magnitude >= 512: shift by 5
      begin
        xout = {{6{xsign}}, xvec[14:5]};
        yout = {{6{ysign}}, yvec[14:5]};
        zout = {{6{zsign}}, zvec[14:5]};
      end
    10'b01????????:  // Magnitude >= 256: shift by 6
      begin
        xout = {{7{xsign}}, xvec[14:6]};
        yout = {{7{ysign}}, yvec[14:6]};
        zout = {{7{zsign}}, zvec[14:6]};
      end
    10'b001???????:  // Magnitude >= 128: shift by 7
      begin
        xout = {{8{xsign}}, xvec[14:7]};
        yout = {{8{ysign}}, yvec[14:7]};
        zout = {{8{zsign}}, zvec[14:7]};
      end
    10'b0001??????:  // Magnitude >= 64: shift by 8
      begin
        xout = {{9{xsign}}, xvec[14:8]};
        yout = {{9{ysign}}, yvec[14:8]};
        zout = {{9{zsign}}, zvec[14:8]};
      end
    10'b00001?????:  // Magnitude >= 32: shift by 9
      begin
        xout = {{10{xsign}}, xvec[14:9]};
        yout = {{10{ysign}}, yvec[14:9]};
        zout = {{10{zsign}}, zvec[14:9]};
      end
    10'b000001????:  // Magnitude >= 16: shift by 10
      begin
        xout = {{11{xsign}}, xvec[14:10]};
        yout = {{11{ysign}}, yvec[14:10]};
        zout = {{11{zsign}}, zvec[14:10]};
      end
    10'b0000001???:  // Magnitude >= 8: shift by 11
      begin
        xout = {{12{xsign}}, xvec[14:11]};
        yout = {{12{ysign}}, yvec[14:11]};
        zout = {{12{zsign}}, zvec[14:11]};
      end
    10'b00000001??:  // Magnitude >= 4: shift by 12
      begin
        xout = {{13{xsign}}, xvec[14:12]};
        yout = {{13{ysign}}, yvec[14:12]};
        zout = {{13{zsign}}, zvec[14:12]};
      end
    10'b000000001?:  // Magnitude >= 2: shift by 13
      begin
        xout = {{14{xsign}}, xvec[14:13]};
        yout = {{14{ysign}}, yvec[14:13]};
        zout = {{14{zsign}}, zvec[14:13]};
      end
    10'b0000000001:  // Magnitude == 1: shift by 14
      begin
        xout = {{15{xsign}}, xvec[14]};
        yout = {{15{ysign}}, yvec[14]};
        zout = {{15{zsign}}, zvec[14]};
      end
    default:  // Magnitude == 0: zero output
      begin
        xout = 16'b0;
        yout = 16'b0;
        zout = 16'b0;
      end
  endcase
end

endmodule  // dist_scale3d

`default_nettype wire
