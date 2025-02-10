import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter

def plot_cross_correlation(x_fixed, x_data):
    # Длина фиксированной последовательности
    n_fixed = len(x_fixed)
    n_data = len(x_data)
    
    # Массив для хранения корреляций
    correlations = []
    
    # Вычисляем корреляцию для сдвигов от 0 до n_data - n_fixed
    for shift in range(n_data - n_fixed + 1):
        # Берем срез данных с учетом сдвига
        x_shifted = x_data[shift:shift + n_fixed]
        
        # Вычисляем корреляцию (скалярное произведение)
        correlation = np.dot(x_fixed, x_shifted)
        correlations.append(correlation)
    
    # Построение графика
    plt.figure(figsize=(10, 5))
    plt.plot(range(n_data - n_fixed + 1), correlations, marker='o')
    plt.title('Корреляция фиксированной последовательности с данными')
    plt.xlabel('Сдвиг')
    plt.ylabel('Корреляция')
    plt.grid()
    plt.show()

def plot_autocorrelation(data):
    n = len(data)
    mean = np.mean(data)
    var = np.var(data)
    
    autocorr = np.correlate(data - mean, data - mean, mode='full')[-n:]
    autocorr /= (var * np.arange(n, 0, -1))  # Нормируем

    plt.figure(figsize=(10, 5))
    plt.plot(autocorr)
    plt.title('Автокорреляция')
    plt.xlabel('Сдвиг')
    plt.ylabel('Автокорреляция')
    plt.grid()
    plt.show()

def autocorrelation_and_plot(seq):
    n = len(seq)
    result = np.zeros(n)

    for lag in range(n):
        sum = 0
        for i in range(n - lag):
            sum += 1 if seq[i] == seq[i + lag] else -1
        result[lag] = sum / (n - lag)

    lags = np.arange(len(result))
    plt.stem(lags, result)
    plt.title('Автокорреляция')
    plt.xlabel('Лаг')
    plt.ylabel('Значение автокорреляции')
    plt.grid()
    plt.show()

def plot_signal(real_part, imag_part):
    time_indices = range(len(real_part))

    plt.figure(figsize=(12, 6))

    # real
    plt.subplot(2, 1, 1)
    plt.plot(time_indices, real_part, color='blue', label='Real Part')
    # plt.scatter(time_indices, real_part, s=9)
    # plt.plot(time_indices, imag_part, color='red', label='Imaginary Part')
    plt.title('Real Part')
    plt.xlabel('Index')
    plt.ylabel('Amplitude')
    plt.grid(True)
    plt.axhline(0, color='black', linewidth=0.5, ls='--')
    plt.legend()

    # img
    plt.subplot(2, 1, 2)
    plt.plot(time_indices, imag_part, color='red', label='Imaginary Part')
    plt.title('Imaginary Part')
    plt.xlabel('Index')
    plt.ylabel('Amplitude')
    plt.grid(True)
    plt.axhline(0, color='black', linewidth=0.5, ls='--')
    plt.legend()

    # QPSK
    plt.figure()
    plt.scatter(real_part, imag_part, s=9)
    plt.xlabel('I')
    plt.ylabel('Q')
    plt.grid()
    plt.axis('equal')

    plt.tight_layout()
    plt.show()

def text_to_bit_sequence(text):
    bit_sequence = []
    
    for char in text:
        ascii_value = ord(char)
        bits = format(ascii_value, '08b')
        bit_sequence.extend(int(bit) for bit in bits)
    
    bit_sequence_array = np.array(bit_sequence)
    return bit_sequence_array, len(bit_sequence_array)

def bits_to_qpsk(bits):
    symbols = []
    for i in range(0, len(bits), 2):
        if i + 1 < len(bits):
            if bits[i] == 0 and bits[i + 1] == 0:
                symbols.append(1 + 1j)  # 00
            elif bits[i] == 0 and bits[i + 1] == 1:
                symbols.append(-1 + 1j)  # 01
            elif bits[i] == 1 and bits[i + 1] == 0:
                symbols.append(-1 - 1j)  # 10
            elif bits[i] == 1 and bits[i + 1] == 1:
                symbols.append(1 - 1j)  # 11
    return np.array(symbols)

def oversampling(symbols, n):
    zeros = np.array([0 + 0j] * (n-1), dtype=np.complex128)
    new_symbols = []
    for symbol in symbols:
        new_symbols.append(symbol)
        new_symbols.extend(zeros)
    
    return np.array(new_symbols, dtype=np.complex128)

def convolve_with_one(symbols, n):
    filter_ones = np.ones(n)
    result = np.convolve(symbols, filter_ones, mode='full')
    return result

N = 10
text = "text!!!!"
bit_sequence, num_bits = text_to_bit_sequence(text)
print(num_bits)

if len(bit_sequence) % 2 != 0:
    bit_sequence = np.append(bit_sequence, 0) 
    num_bits += 1

print(num_bits)
print(bit_sequence)

qpsk_symbols = bits_to_qpsk(bit_sequence)
qpsk_symbols_app = oversampling(qpsk_symbols, N)
qpsk_symbols_convolve = convolve_with_one(qpsk_symbols_app, N)

real_part = (qpsk_symbols_convolve.real).astype(np.int16)
imag_part = (qpsk_symbols_convolve.imag).astype(np.int16) 

real_part = np.trim_zeros(real_part)
imag_part = np.trim_zeros(imag_part)

combined = np.empty(real_part.size + imag_part.size, dtype=np.int16)
combined[0::2] = real_part
combined[1::2] = imag_part

print(combined)
print(real_part.size)

with open('qpsk_signal.bin', 'wb') as f:
    combined.tofile(f)
with open('qpsk_signal.txt', 'w') as f:
    for i in range(0, combined.size, 2):
        f.write(f"{combined[i]}, {combined[i + 1]}\n")

plot_signal(real_part, imag_part)