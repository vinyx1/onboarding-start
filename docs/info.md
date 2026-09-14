<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

 * SPI controller -> input pins (ui_in[])

In spi_peripheral, 
 * (ui_in[]) -> 2 flip flop synchronizers (synced to the main clock)
 * During transaction, shift the COPI input into a 16 bit register 
 * Once the transaction is ready, decode: bit 0 -> r/w, bit [1,7] -> address, bit [8, 15] -> data
 * write to the corresponding registers read by pwm_peripheral

## How to test

To create a test, go to `test.py` and create a function with `@cocotb.test()` and parameter `dut`, which is the protocol. Run with make through  `make TESTCASE={function}`

## External hardware


