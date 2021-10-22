# Demodulation

## Structure
Use ```signal_analyzer.py``` to create spectrograms of wave files. For recording, ```recorder.py``` is used as a helper library (requires PyAudio, see below). If you just want to analyze without recording, PyAudio is not required.

## Getting started
- You might have issues installing PyAudio. For UNIX like systems, check out [this](https://stackoverflow.com/questions/20023131/cannot-install-pyaudio-gcc-error). For Windows systems, check out [this](https://stackoverflow.com/questions/52283840/i-cant-install-pyaudio-on-windows-how-to-solve-error-microsoft-visual-c-14).
- ```ref_file.wav``` is used as a reference audio file. PLEASE DO NOT MODIFY / OVERWRITE! It should generate a valid spectogram. If it doesn't, you messed up the code somehow.
- It might be necessary to convert a wave file from stereo to mono first (spectograms are defined for single-channel recordings only). To do this, use the ```stereo_to_mono()``` function within ```signal_analyzer.py```.
- If you're having trouble recording via Python, you can use [ALSA](https://learn.linksprite.com/pcduino/linux-applications/how-to-capture-microphone-input-to-wav-format-file-on-pcduino/) on Linux.