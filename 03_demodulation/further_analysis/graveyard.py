def process_preamble(sub_xs):
    """
    Listen for a full preamble within x.
    """

    print("Looking for preamble start...")

    # setting some helper variable which we need for detection
    preamble = []
    state_one = False  # are we currently in state 1 of the preamble?
    state_zero = False  # are we currently in state 0 of the preamble?
    freq_calc_counter = 0  # counter to see for how long the 1s in the preamble lasted...
    freq_calc_counter_max = 0  # ...to calculate the (estimated) BFSK_FREQ.

    # loop through x's subarrays, extract dominant freq and see whether we receive a full preamble

    for idx, x_short in enumerate(sub_xs):
        print(idx)
        dominant_freq = get_dominant_freq(x_short)
        print(dominant_freq)

        # we recognized a freq which we associate with a 1
        if ONE_FREQ - 400 <= dominant_freq <= ONE_FREQ + 400:

            freq_calc_counter += 1
            if freq_calc_counter > freq_calc_counter_max:
                freq_calc_counter_max = freq_calc_counter

            state_zero = False  # we are in state 1
            if not state_one:
                state_one = True
                preamble.append(1)

        # we recognized a freq which we associate with a 0 (following a 1 freq)
        elif ZERO_FREQ - 400 <= dominant_freq <= ZERO_FREQ + 400 and not state_zero and state_one:
            freq_calc_counter = 0
            state_zero = True
            state_one = False
            preamble.append(0)

        else:
            freq_calc_counter = 0
            # preamble = []

        # is preamble complete?
        if preamble == [1, 0, 1, 0, 1, 0, 1, 0]:
            print("PREAMBLE DETECTED - switching to data collection phase...")
            global BFSK_FREQ
            BFSK_FREQ = int((1 / freq_calc_counter_max) / TIME_INTERVAL)  # estimate BFSK_FREQ
            print("BFSK Frequency is " + str(BFSK_FREQ) + " Hz")

            global DATA_START_FRAME
            DATA_START_FRAME = idx * len(x_short)
            print(idx)
            print(len(x_short))
            print("Data start frame: " + str(DATA_START_FRAME))

            return True
        print(preamble)
    print("NO PREAMBLE FOUND - aborting...")
    sys.exit(1)


def process_data(sub_xs):
    """
    Read the whole signal TODO: WORK IN PROGRESS
    """
    data = []
    frames_per_freq_period = BFSK_FREQ / TIME_INTERVAL  # how many frames per symbol (1/0) time?
    for idx, x_signal in enumerate(sub_xs):
        timestamp = idx * TIME_INTERVAL
        if not idx % (frames_per_freq_period / 2):  # only check twice per symbol time
            dominant_freq = get_dominant_freq(x_signal)
            print("Time: " + str(timestamp))
            print("Frame: " + str(int(timestamp * f_s)))
            print(str(dominant_freq) + " Hz \n")

            if ONE_FREQ - 400 <= dominant_freq <= ONE_FREQ + 400:
                data.append(1)

            elif ZERO_FREQ - 400 <= dominant_freq <= ZERO_FREQ + 400:
                data.append(0)
    return data

def detect_preamble(raw_data):
    global BFSK_FREQ
    preamble = []
    # TESTING
    raw_data = raw_data[39:]

    # loop through all elements
    sliding_preamble_window = []
    potential_preamble_seen = False
    for idx, elem in enumerate(raw_data):
        if idx > len(raw_data) - int(round(BFSK_FREQ / TIME_INTERVAL, 0)):
            return

        if ONE_FREQ - 250 <= elem <= ONE_FREQ + 250:
            if not potential_preamble_seen:
                print("Potential preamble detected...")
                potential_preamble_seen = True
            sliding_preamble_window.append(elem)
            if len(preamble) <= idx:
                preamble.append(1)
        elif ZERO_FREQ - 250 <= elem <= ZERO_FREQ + 250 and potential_preamble_seen:
            if ONE_FREQ - 250 <= raw_data[-idx] <= ONE_FREQ + 250:
                if len(preamble) <= idx + 1:
                    preamble.append(0)
                potential_symbol_length = len(sliding_preamble_window)
                zero_candidates = raw_data[idx:idx + potential_symbol_length]
                for presumed_zero in zero_candidates:
                    if not ZERO_FREQ - 250 <= presumed_zero <= ZERO_FREQ + 250:
                        break
                if potential_symbol_length == len(zero_candidates):
                    BFSK_FREQ = len(zero_candidates) * TIME_INTERVAL
                    print("Setting BFSK_FREQ to " + str(BFSK_FREQ))

        elif potential_preamble_seen:
            print("Didn't receive full preamble. Aborting...")
            potential_preamble_seen = False
            sliding_preamble_window = []

        if preamble == [1, 0, 1, 0, 1, 0, 1, 0]:
            print("Preamble verified!")
            return idx * f_s * TIME_INTERVAL