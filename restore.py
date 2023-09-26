import sys
import os
import time
import io
import scipy as sp
from scipy.io import wavfile
from scipy import signal
import numpy as np
import wave
import subprocess

def main():
    print("Starting...")
    t1 = time.time()

    file = sys.argv[1]
    # file = "music.mp3"

    with open(file, "rb") as f:
        audio = f.read()

    audio = btb(data=audio, action="-f wav -acodec pcm_s32le -ac 2 -ar 48000")

    intervals = calculate_intervals(16000, 20000, 30)
    print(intervals)
    time.sleep(3)

    audios = [audio]
    for interval in intervals:
        initial, final, cents = interval  # high pass initial, pitch cents

        rate = 48000 * pow(2, (cents/1200))
        tempo = 1 / pow(2, (cents/1200))
        print(rate)
        print(tempo)
        pitched_audio = btb(data=audio,
                            action=f"-f wav -acodec pcm_s32le -af asetrate={rate},aresample=48000,atempo={tempo}")
        highpassed_audio = btb(data=pitched_audio,
                               action=f'-filter_complex "acrossover=split={initial}:'
                                      f'order=20th[LOW][HIGH]" -f wav -map "[LOW]" temp '
                                      f'-f wav -acodec pcm_s32le -map "[HIGH]"')

        audios.append(highpassed_audio)

    print("Combining & writing audios.")
    write_audio(audios, "file.wav")

    t2 = round(time.time() - t1, 2)
    print(f"Done: {t2} sec")
    time.sleep(1000)


def btb(data: bytes, action: str) -> bytes:
    command = f"ffmpeg -y -i pipe:0 {action} pipe:1"
    print(command)
    ffmpeg_process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    output_stream = ffmpeg_process.communicate(bytearray(data))
    output_bytes = output_stream[0]
    return output_bytes


def write_audio(audios, outfile):
    audios2 = []
    for audio in audios:
        x = io.BytesIO()
        x.write(audio)
        x.seek(0)
        audios2.append(x)
    audios = audios2

    wavs = [wave.open(f) for f in audios]
    frames = [w.readframes(w.getnframes()) for w in wavs]
    samples = [np.frombuffer(f, dtype='<i2') for f in frames]
    samples = [samp.astype(np.float64) for samp in samples]

    n = min(map(len, samples))
    mix = samples[0][:n]
    for i in range(1, len(samples)):
        mix += samples[i][:n]

    with wave.open(outfile, 'wb') as wav_out:
        wav_out.setparams(wavs[0].getparams())
        wav_out.writeframes(mix.astype('<i2').tobytes())


def calculate_intervals(initial, final, pitch_interval):
    interval_hz = (pitch_interval / 1200) * initial
    intervals = []

    x = 1
    while 1:
        segment_initial = initial + ((x - 1) * interval_hz) - 100
        segment_final = initial + (x * interval_hz)
        pitch_change = (x * pitch_interval)
        if segment_initial > final:
            break
        intervals.append([round(segment_initial), round(segment_final), pitch_change])
        x += 1

    return intervals


main()
