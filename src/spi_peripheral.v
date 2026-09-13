`default_nettype none

module spi_peripheral (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       sclk,
    input  wire       copi,
    input  wire       ncs,

    output reg [7:0] en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0,
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0] pwm_duty_cycle
);

    // n=2 synchronizers
    reg sclk_sync1, sclk_sync2;
    reg copi_sync1, copi_sync2;
    reg ncs_sync1,  ncs_sync2;

    // for detecting edges
    reg sclk_prev;
    reg ncs_prev;

    // for 16 bit info to pass
    reg [15:0] shift_reg;
    reg [4:0]  bit_count; // count num of bits

    // always record sclk_rising
    wire sclk_rising = sclk_sync2 && !sclk_prev;

    // printing
    always @(posedge clk) begin
        $display(
            "t=%0t raw_sclk=%b sync1=%b sync2=%b prev=%b rising=%b copi=%b ncs=%b",
            $time,
            sclk,
            sclk_sync1,
            sclk_sync2,
            sclk_prev,
            sclk_rising,
            copi,
            ncs
        );
    end

    // moving signals within synchronizers + edge detection 
    // spi mode 0; posedge -> sample
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin // initial state
            sclk_sync1 <= 1'b0;
            sclk_sync2 <= 1'b0;

            copi_sync1 <= 1'b0;
            copi_sync2 <= 1'b0;

            ncs_sync1 <= 1'b1;
            ncs_sync2 <= 1'b1;

            sclk_prev <= 1'b0;
        end else begin

            // sync1's could be metastable
            // sync2's are for stable
            sclk_sync1 <= sclk;
            sclk_sync2 <= sclk_sync1;

            copi_sync1 <= copi;
            copi_sync2 <= copi_sync1;

            ncs_sync1 <= ncs;
            ncs_sync2 <= ncs_sync1;
            
            // record prev to detect edges
            sclk_prev <= sclk_sync2;

        end
    end




endmodule