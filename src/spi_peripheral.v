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
    reg transaction_ready;

    // always record sclk_rising
    wire sclk_rising = sclk_sync2 && !sclk_prev;

    always @(posedge clk) begin
        if (transaction_ready) begin
            $display(
                "SPI transaction: rw=%b addr=%h data=%h full=%h",
                shift_reg[15],
                shift_reg[14:8],
                shift_reg[7:0],
                shift_reg
            );
        end

        //$display("en_reg_out_7_0=%h", en_reg_out_7_0);
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

    // shifting bits into the temp register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg <= 16'b0;
            bit_count <= 5'd0;
            transaction_ready <= 1'b0;
        end else if (!ncs_sync2) begin // occur only when transaction is online (nCS = 0)

            // ok this is weird but basically you wanna keep transaction_ready 1 pulse, so the next always block only triggers once
            transaction_ready <= 1'b0;

            if (sclk_rising && bit_count < 5'd16) begin // only transfer when rising edge + one of the 16 bits
                shift_reg <= {shift_reg[14:0], copi_sync2}; // shift the copi bit into the register, take the first 14 bits and append the bit to the end
                bit_count <= bit_count + 1'b1;

                if (bit_count == 0)
                    $display("Starting new SPI transaction");

                if (bit_count == 5'd15) begin
                    $display("Captured 16th SPI bit");
                    transaction_ready <= 1'b1;
                end
            end
        end else begin
            if (bit_count != 0)
            $display(
                "nCS HIGH: resetting bit_count=%0d",
                bit_count
            );
            bit_count <= 5'd0;
            transaction_ready <= 1'b0;
        end
    end

    // once the 16 bits are ready, decode and put them into the pwm registers
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            en_reg_out_7_0   <= 8'b0;
            en_reg_out_15_8  <= 8'b0;
            en_reg_pwm_7_0   <= 8'b0;
            en_reg_pwm_15_8  <= 8'b0;
            pwm_duty_cycle   <= 8'b0;

        end else if (transaction_ready) begin // only when transaction is ready

            // bit 15 = 1 means write
            if (shift_reg[15]) begin
                case (shift_reg[14:8])

                    7'h00:
                        en_reg_out_7_0 <= shift_reg[7:0];

                    7'h01:
                        en_reg_out_15_8 <= shift_reg[7:0];

                    7'h02:
                        en_reg_pwm_7_0 <= shift_reg[7:0];

                    7'h03:
                        en_reg_pwm_15_8 <= shift_reg[7:0];

                    7'h04:
                        pwm_duty_cycle <= shift_reg[7:0];

                    default: begin
                        // invalid address: do nothing
                    end

                endcase
            end
        end
    end



endmodule