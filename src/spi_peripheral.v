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

    always @(posedge clk) begin
        $display(
            "t=%0t sclk=%b copi=%b ncs=%b",
            $time,
            sclk,
            copi,
            ncs
        );
    end


endmodule