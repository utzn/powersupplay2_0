import argparse
import binascii
import statistics
from itertools import groupby

import crc8
import numpy as np
from colorama import Fore
from scipy import fftpack
from scipy.io import wavfile

from signal_analyzer import butter_bandpass_filter

parser = argparse.ArgumentParser(description="PowerSupplay demodulator")
parser.add_argument("--one-freq",
                    help="Target frquency for binary 1s",
                    default=5500,
                    dest="one_freq",
                    type=int),
parser.add_argument("--zero-freq",
                    help="Target frquency for binary 0s",
                    default=6500,
                    dest="zero_freq",
                    type=int),
parser.add_argument("--filepath",
                    help="Filepath to the modulated recording",
                    default="../02_modulation/audio_files/dell_test_100_300.wav",
                    dest="filepath",
                    type=str)
parser.add_argument("--time-interval",
                    help="Time intervals into which to slice sound file",
                    default=0.1,
                    dest="time_interval",
                    type=float)

args = parser.parse_args()

# PARSE ARGS TO MATCH YOUR TARGETS
ONE_FREQ = args.one_freq
ZERO_FREQ = args.zero_freq
FILEPATH = args.filepath
TIME_INTERVAL = args.time_interval


def get_dominant_freq(signal):
    """
    Find the dominant frequency within a signal represented by numpy array x.
    x should not be too short, otherwise we can't determine the frequency with FFT!
    """
    x_fft = fftpack.fft(signal)
    freqs = fftpack.fftfreq(len(signal)) * f_s
    freqs = freqs[int(len(signal) / 10):int(len(signal) / 2)]
    abs_x = np.abs(x_fft)
    abs_x = abs_x[int(len(signal) / 10):int(len(signal) / 2)]
    res = freqs[np.argmax(abs_x)]

    # returns the dominant (loudest) frequency within x.
    return int(res)


def adjust_and_add_freqs(sub_xs):
    """Adjust the parsed frequencies to be more accurate and returns the dominant frequencies as an array"""
    global ZERO_FREQ, ONE_FREQ
    res = []
    # transform raw chunks into chunks of dominant frequencies
    for idx, x in enumerate(sub_xs):
        res.append(get_dominant_freq(x))

    # fine-tune given frequencies with detected mean for 1s and 0s
    zero_freqs = []
    one_freqs = []
    for freq in res:
        if abs(freq - ZERO_FREQ) <= abs(freq - ONE_FREQ):
            zero_freqs.append(freq)
        else:
            one_freqs.append(freq)

    print("Updating 1 and 0 frequency targets according to gathered data...")
    ZERO_FREQ = int(statistics.mean(zero_freqs))
    ONE_FREQ = int(statistics.mean(one_freqs))

    print("ZERO_FREQ --> " + str(ZERO_FREQ) + " Hz")
    print("ONE_FREQ --> " + str(ONE_FREQ) + " Hz")

    return res


def cut_preamble_and_return_bin_count(raw_data):
    """Trims off the preamble and returns the respective symbol lengths following it"""
    print(Fore.CYAN + "\n---PREAMBLE DETECTION---")
    print(Fore.RESET, end="")

    # transform frequencies into bitstream
    bin_data_from_raw = []
    print("Attempting to parse detected frequencies to 1s and 0s...")
    for bin_val in raw_data:
        if ONE_FREQ - 250 <= bin_val <= ONE_FREQ + 250:
            bin_data_from_raw.append(1)
        elif ZERO_FREQ - 250 <= bin_val <= ZERO_FREQ + 250:
            bin_data_from_raw.append(0)
        else:
            bin_data_from_raw.append(None)
    print("Done!")

    # correct transmission errors
    print("Detecting and correcting errors...")
    loop_range = len(bin_data_from_raw)
    for idx in range(0, loop_range):
        if idx == loop_range:
            break
        if not (idx == 0 or idx == len(bin_data_from_raw) - 2):
            if bin_data_from_raw[idx] == 0 and bin_data_from_raw[idx - 1] == 1 and bin_data_from_raw[idx + 1] == 1:
                print("Position " + str(idx) + " - replaced a 0 with a 1")
                bin_data_from_raw[idx] = 1
            elif bin_data_from_raw[idx] == 1 and bin_data_from_raw[idx - 1] == 0 and bin_data_from_raw[idx + 1] == 0:
                print("Position " + str(idx) + " - replaced a 1 with a 0")
                bin_data_from_raw[idx] = 0
            elif bin_data_from_raw[idx] is None:
                try:
                    bin_data_from_raw[idx] = int(
                        round((bin_data_from_raw[idx - 1] + bin_data_from_raw[idx - 1]) / 2, 0))
                    print("Position " + str(idx) + " - replaced a None value with " + str(bin_data_from_raw[idx]))
                except TypeError:
                    print("Position " + str(idx) + " - deleted irreparable None value")
                    del bin_data_from_raw[idx]
                    loop_range = len(bin_data_from_raw)
    print("Done!")

    print("Calculating symbol lengths...")
    symbol_lengths = [sum(1 for _ in group) for _, group in groupby(bin_data_from_raw)]
    print("Done!")
    print("Accounting for rounding errors...")
    for idx in range(0, len(symbol_lengths)):
        symbol_lengths[idx] = round(symbol_lengths[idx], -1)
        symbol_lengths[idx] = int(symbol_lengths[idx] / 10)
    print("Done!")

    # remove preamble and return payload+crc payload lengths
    symbol_lengths = symbol_lengths[7:]
    if symbol_lengths[0] == 0:
        del symbol_lengths[0]
    else:
        symbol_lengths[0] -= 1

    return symbol_lengths


def detect_payload_plus_crc(one_and_zero_lengths):
    """Takes in the symbol lengths and returns a bitstream as a binary array"""
    print(Fore.CYAN + "\n---PAYLOAD PROCESSING---")
    print(Fore.RESET, end="")
    payload_plus_crc = []
    for idx, bits in enumerate(one_and_zero_lengths):
        for i in range(0, bits):
            if idx % 2:
                payload_plus_crc.append(0)
            else:
                payload_plus_crc.append(1)

    # payload pruning (to multiples of 8)
    while len(payload_plus_crc) % 8:
        del payload_plus_crc[-1]

    print("Done!")
    return payload_plus_crc


def crc_check(payload_plus_crc):
    """Verify CRC"""
    print(Fore.CYAN + "\n---CRC CHECK---")
    print(Fore.RESET, end="")

    # determine data, cut last 8 bits
    payload_int = 0
    for bit in payload_plus_crc[:len(payload_plus_crc) - 8]:
        payload_int = (payload_int << 1) | bit

    # calculate crc on last 8 bits in payload_plus_crc
    crc_int = 0
    for bit in payload_plus_crc[-8:]:
        crc_int = (crc_int << 1) | bit

    crc = crc8.crc8()
    crc.update(bin(payload_int).encode("UTF-8"))

    print("Received CRC: " + "{0:b}".format(crc_int))
    print("Calculated CRC: " + "{0:b}".format(int(crc.hexdigest())))

    if crc_int == crc.hexdigest():
        return True
    else:
        return False


# taken from https://stackoverflow.com/questions/7396849/convert-binary-to-ascii-and-vice-versa
def int2bytes(i):
    hex_string = '%x' % i
    n = len(hex_string)
    return binascii.unhexlify(hex_string.zfill(n + (n & 1)))


# taken from https://stackoverflow.com/questions/7396849/convert-binary-to-ascii-and-vice-versa
def text_from_bits(bits, encoding='utf-8', errors='surrogatepass'):
    n = int(bits, 2)
    return int2bytes(n).decode(encoding, errors)


def process_signal(sampling_frequency, x_signal):
    """Main function for processing the signal, sub functions called within"""
    print(Fore.CYAN + "\n---PREPARATION---")
    print(Fore.RESET, end="")
    # splitting raw signal into chunks of length TIME_INTERVAL
    split = []
    i = 0
    while i < len(x_signal):
        i += int(sampling_frequency * TIME_INTERVAL)
        split.append(i)

    x_signal_split = np.array_split(x_signal, split)

    # cut remainder if too small for useful analysis
    if len(x_signal_split[-1]) < sampling_frequency * 100:
        del x_signal_split[-1]

    print("Splitting x into " + str(len(x_signal_split)) + " subarrays, lasting for " +
          str(TIME_INTERVAL) + " s each")

    # data processing
    frequency_list = adjust_and_add_freqs(x_signal_split)
    ones_and_zeroes_count = cut_preamble_and_return_bin_count(frequency_list)
    payload_plus_crc = detect_payload_plus_crc(ones_and_zeroes_count)

    # return a printable payload string
    payload_string = ""
    payload = payload_plus_crc[1:len(payload_plus_crc) - 8]
    for bit in payload:
        payload_string += str(bit)

    # what happens if we pass crc
    if crc_check(payload_plus_crc):
        print(Fore.GREEN + "CRC's matched!")
        print(Fore.RESET, end="")
        try:
            ascii = text_from_bits(payload_string)
            print("\nReceived ASCII text: ")
            print(Fore.CYAN, end="")
            print(ascii)
        except UnicodeDecodeError as err:
            print(Fore.YELLOW + "Error: " + str(err))
            print(Fore.RESET, end="")
            print("\nReceived signal was:")
            print(Fore.YELLOW, end="")
            for idx, bit in enumerate(payload_string):
                if not idx % 8 and idx != 0:
                    print(" ", end="")
                print(bit, end="")
            print("")

    #what happens if we don't pass crc
    else:
        print(Fore.YELLOW + "CRC mismatch found. Data might be corrupted...")
        print(Fore.RESET, end="")
        print("\nPlease verify received signal manually:")
        print(Fore.YELLOW, end="")
        for idx, bit in enumerate(payload_string):
            if not idx % 8 and idx != 0:
                print(" ", end="")
            print(bit, end="")
        print(Fore.RESET, end="")
    print("\n\n")


if __name__ == "__main__":
    print("Reading " + FILEPATH)
    f_s, x = wavfile.read(FILEPATH)

    # "guard bands"
    if ZERO_FREQ < ONE_FREQ:
        x = butter_bandpass_filter(x, ZERO_FREQ - abs(ONE_FREQ - ZERO_FREQ), ONE_FREQ + abs(ONE_FREQ - ZERO_FREQ), f_s)
    else:
        x = butter_bandpass_filter(x, ONE_FREQ - abs(ONE_FREQ - ZERO_FREQ), ZERO_FREQ + abs(ONE_FREQ - ZERO_FREQ), f_s)

    # printing initial information
    print("# samples: " + str(len(x)))
    print("Sampling frequency: " + str(f_s) + " Hz")
    print("Signal duration: " + str(round((len(x) / f_s), 2)) + " s")
    process_signal(f_s, x)
