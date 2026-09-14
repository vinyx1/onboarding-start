# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    
    Parameters:
    - r_w: boolean, True for write, False for read
    - address: int, 7-bit address (0-127)
    - data: LogicArray or int, 8-bit data
    """
    # Convert data to int if it's a LogicArray
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Validate inputs
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # Combine RW and address into first byte
    first_byte = (int(r_w) << 7) | address
    # Start transaction - pull CS low
    sclk = 0
    ncs = 0
    bit = 0
    # Set initial state with CS low
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send first byte (RW + Address)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send second byte (Data)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End transaction - return CS high
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)

    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")

async def setup_dut(dut):
    clock = Clock(dut.clk, 100, units="ns")  # 10 MHz
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.uio_in.value = 0

    # SPI idle: nCS=1, COPI=0, SCLK=0
    dut.ui_in.value = ui_in_logicarray(1, 0, 0)

    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

@cocotb.test()
async def test_pwm_freq(dut):
    await setup_dut(dut)

    # Enable uo_out[0]
    await send_spi_transaction(dut, 1, 0x00, 0x01)
    await ClockCycles(dut.clk, 5)

    # Enable PWM on uo_out[0]
    await send_spi_transaction(dut, 1, 0x02, 0x01)
    await ClockCycles(dut.clk, 5)

    # set 50% cycle
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    await ClockCycles(dut.clk, 5)

    # Find first rising edge of uo_out[0]
    prev = int(dut.uo_out.value) & 1

    while True:
        await RisingEdge(dut.clk)
        cur = int(dut.uo_out.value) & 1

        if prev == 0 and cur == 1:
            t1 = cocotb.utils.get_sim_time(units="ns")
            break

        prev = cur

    # Find next rising edge
    prev = int(dut.uo_out.value) & 1

    while True:
        await RisingEdge(dut.clk)
        cur = int(dut.uo_out.value) & 1

        if prev == 0 and cur == 1:
            t2 = cocotb.utils.get_sim_time(units="ns")
            break

        prev = cur

    period_ns = t2 - t1
    frequency = 1e9 / period_ns

    dut._log.info(f"PWM frequency = {frequency} Hz")

    assert abs(frequency - 3000) / 3000 <= 0.01, \
        f"Expected about 3000 Hz, got {frequency} Hz"

    dut._log.info("PWM Frequency test completed successfully")
# make TESTCASE=test_pwm_freq

@cocotb.test()
async def test_pwm_duty(dut):
    await setup_dut(dut)

    # Enable uo_out[0]
    await send_spi_transaction(dut, 1, 0x00, 0x01) # write 0x01 to 0x00 (enable)
    await ClockCycles(dut.clk, 5)

    # Enable PWM on uo_out[0]
    await send_spi_transaction(dut, 1, 0x02, 0x01) # write 0x01 to 0x02 (enable pwm)
    await ClockCycles(dut.clk, 5)

    test_values = [
        0x00,   # 0%
        0x40,   # 25%
        0x80,   # 50%
        0xC0,   # 75%
        0xFF,   # 100%
    ]

    for duty in test_values:
        await send_spi_transaction(dut, 1, 0x04, duty)
        await ClockCycles(dut.clk, 5)

        # ~3000 cycles per pwm cycle
        await ClockCycles(dut.clk, 3500)

        # record % of high signals in 10k, so ~3 pwm cycles
        high_count = 0
        samples = 10000

        for _ in range(samples):
            await RisingEdge(dut.clk)

            if int(dut.uo_out.value) & 1:
                high_count += 1

        measured = high_count / samples

        if duty == 0xFF:
            expected = 1.0
        else:
            expected = duty / 256.0

        dut._log.info(
            f"duty register=0x{duty:02X}, "
            f"expected={expected*100:.2f}%, "
            f"measured={measured*100:.2f}%"
        )

        assert abs(measured - expected) <= 0.01, \
            f"Bad duty cycle for 0x{duty:02X}"
        

    dut._log.info("PWM Duty Cycle test completed successfully")
    # make TESTCASE=test_pwm_duty
