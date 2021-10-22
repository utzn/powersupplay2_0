# ASA PowerSupplay Project Q3 2020
This is a reproduction of the [paper by Guri](https://arxiv.org/pdf/2005.00395.pdf) using synchronous threads instead of barriers.

  

The [modulator](02_modulation/linux.cpp) reads a file and encodes it into a BFSK signal consisting of three parts:

- **Preamble**: A fixed bit sequence (in our case, 10101010) to notify the receiver that we're about to transmit data.
- **Payload**: The actual data to be transmitted.
- **CRC**: an 8-bit checksum to verify payload integrity.

The [demodulator](03_demodulation/demodulate_bfsk.py) takes an audio recording and then analyses it automatically to retrieve the transmitted data.

For more details, please see the [report](deliverables/report.pdf).