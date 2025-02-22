import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import fft, ifft
from scipy.signal import welch

N = 64 
cp_len = 16 
fs = 1e3 
delta_f = fs / N  
text = "OFDM !!!"
binary_data = ''.join(format(ord(c), '08b') for c in text)
symbols = np.array([int(binary_data[i:i+2], 2) for i in range(0, len(binary_data), 2)])

num_symbols = int(np.ceil(len(symbols) / N))

symbols = np.pad(symbols, (0, num_symbols * N - len(symbols)), 'constant')

# QPSK
mapping = {0: 1+1j, 1: -1+1j, 2: -1-1j, 3: 1-1j}
data = np.array([mapping[s] for s in symbols]).reshape((num_symbols, N))

ofdm_symbols = ifft(data, axis=1)  # в частотную область
ofdm_symbols_cp = np.hstack([ofdm_symbols[:, -cp_len:], ofdm_symbols]) 

time_signal = ofdm_symbols_cp.flatten()  # во времени


plt.figure(figsize=(12, 8))
plt.subplot(2, 2, 1)
time_axis = np.linspace(0, len(time_signal) / fs, len(time_signal))
plt.plot(time_axis, np.real(time_signal), label="Действительная часть", alpha=0.7)
plt.plot(time_axis, np.imag(time_signal), label="Мнимая часть", linestyle='dashed', alpha=0.7)
plt.title("OFDM-сигнал во временной области")
plt.xlabel("Время (мс)")
plt.legend()
plt.grid()

plt.subplot(2, 2, 2)
freqs = np.fft.fftfreq(len(time_signal), d=1/fs)
psd = np.abs(np.fft.fft(time_signal))**2
plt.plot(freqs[:len(freqs)//2], psd[:len(psd)//2])
plt.title("Спектр OFDM-сигнала")
plt.xlabel("Частота (Гц)")
plt.ylabel("Амплитуда")
plt.grid()

plt.subplot(2, 2, 3)
freq_axis = np.arange(-N//2, N//2) * delta_f
ofdm_spectrum = np.abs(fft(data[0]))
plt.stem(freq_axis, np.fft.fftshift(ofdm_spectrum))
plt.title("Спектр OFDM с распределенными поднесущими")
plt.xlabel("Частота (Гц)")
plt.ylabel("Амплитуда")
plt.grid()

plt.subplot(2, 2, 4)
plt.scatter(np.real(data.flatten()), np.imag(data.flatten()), alpha=0.5)
plt.title("Созвездие QPSK")
plt.xlabel("Действительная часть")
plt.ylabel("Мнимая часть")
plt.axhline(0, color='gray', linestyle='dashed')
plt.axvline(0, color='gray', linestyle='dashed')
plt.grid()

plt.tight_layout()
plt.show()

received_time_signal = time_signal.reshape(num_symbols, N + cp_len)
received_symbols_no_cp = received_time_signal[:, cp_len:]
received_symbols_dft = fft(received_symbols_no_cp, axis=1)

# Демодуляция 
reverse_mapping = {v: k for k, v in mapping.items()}
received_symbols = np.array([reverse_mapping[min(mapping.values(), key=lambda x: abs(x - r))] for r in received_symbols_dft.flatten()])
received_binary = ''.join(format(s, '02b') for s in received_symbols)
received_text = ''.join(chr(int(received_binary[i:i+8], 2)) for i in range(0, len(received_binary), 8)).strip('\x00')

print(f"Принятый текст: {received_text}")

plt.figure(figsize=(6, 4))
plt.text(0.1, 0.5, f"Принятый текст: {received_text}", fontsize=12)
plt.axis("off")
plt.show()
