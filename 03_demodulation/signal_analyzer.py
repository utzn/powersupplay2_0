from matplotlib import pyplot as plt
import numpy as np
from pydub import AudioSegment
from scipy.io import wavfile
from scipy.signal import butter, lfilter

from recorder import Recorder


# recording via Python, if desired
def record(filepath: str, duration: int):
    rec = Recorder(channels=1)
    print("Recording for " + str(duration) + " seconds...")
    with rec.open(filepath, 'wb') as recfile:
        recfile.record(duration)


# bandpass filter #1
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


# bandpass filter #2
def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


# converts a stereo channel wav to a mono channel wav
def stereo_to_mono(filepath: str):
    sound = AudioSegment.from_wav(filepath)
    sound = sound.set_channels(1)
    sound.export(filepath, format="wav")


# processes the signal, plots the resulting spectrogram and saves it as a png
def plot_spectrogram(filepath: str, nfft=2 ** 12):
    # Read the WAV file (mono)
    stereo_to_mono(filepath)
    sampling_frequency, signal_data = wavfile.read(filepath)

    # de-comment if a bandpass filter is needed:
    # signal_data = butter_bandpass_filter(signal_data, 5250, 6750, sampling_frequency)
    filename = filepath.split("/")[-1]

    plt.title(filename + "  NFFT: " + str(nfft))
    plt.specgram(signal_data, Fs=sampling_frequency, NFFT=nfft, mode="magnitude")
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    print("Saving plot to file")
    plt.savefig(filepath.split("/")[-1][:-3] + "png")
    plt.show()


if __name__ == "__main__":
    with open("inputs.txt", "r") as inputs:
        for line in inputs:
            plot_spectrogram(line.rstrip())
