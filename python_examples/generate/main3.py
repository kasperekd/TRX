import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import max_len_seq

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

# def bits_to_qpsk(bits):
#     symbols = []
#     for i in range(0, len(bits), 2):
#         if i + 1 < len(bits):
#             if bits[i] == 0 and bits[i + 1] == 0:
#                 symbols.append(1 + 1j)  # 00
#             elif bits[i] == 0 and bits[i + 1] == 1:
#                 symbols.append(-1 + 1j)  # 01
#             elif bits[i] == 1 and bits[i + 1] == 0:
#                 symbols.append(-1 - 1j)  # 10
#             elif bits[i] == 1 and bits[i + 1] == 1:
#                 symbols.append(1 - 1j)  # 11
#     return np.array(symbols)

def bits_to_qpsk(bits):
    bits = bits.reshape((-1, 2))
    mapping = {
        (0, 0): -1 + -1j,
        (0, 1): -1 + 1j,
        (1, 0): 1 - 1j,
        (1, 1): 1 + 1j,
    }
    return np.array([mapping[tuple(b)] for b in bits], dtype=complex)

def bits_to_bpsk(bits):
    # BPSK: 0 -> -1, 1 -> +1
    return 2 * bits - 1

# def oversampling(symbols, n):
#     zeros = np.array([0 + 0j] * (n-1), dtype=np.complex128)
#     new_symbols = []
#     for symbol in symbols:
#         new_symbols.append(symbol)
#         new_symbols.extend(zeros)
    
#     return np.array(new_symbols, dtype=np.complex128)

def oversampling(symbols, n):
    zeros = np.array([0 + 0j] * (n - 1), dtype=np.complex128)
    new_symbols = []
    
    for i, symbol in enumerate(symbols):
        new_symbols.append(symbol)
        if i < len(symbols) - 1: 
            new_symbols.extend(zeros)
    
    return np.array(new_symbols, dtype=np.complex128)

def convolve_with_one(symbols, n):
    filter_ones = np.ones(n)
    result = np.convolve(symbols, filter_ones, mode='full')
    return result

def barker_sequence():
    # return np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1], dtype=np.int8)
    return np.array([1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1], dtype=np.int8)
    # return np.array([1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0], dtype=np.int8)

def bits_to_bpsk_complex(bits):
    # real_part = 2 * bits - 1 
    return np.array((2 * bits - 1) + 0j)
    # return real_part + 1j * real_part

def generate_gold_sequence(length=31):
    seq1, _ = max_len_seq(5)
    seq2 = np.roll(seq1, 3)
    gold_sequence = np.bitwise_xor(seq1, seq2[:length])
    return gold_sequence.astype(np.int8)

def generate_m_sequence(order=5):
    seq, _ = max_len_seq(order)
    return seq.astype(np.int8)

def create_packet(payload_bits, sync_word=None, header_length=0):
    if sync_word is None:
        sync_word = barker_sequence()
    # payload_length = len(payload_bits)
    # header = np.array([int(b) for b in f"{payload_length:0{header_length}b}"], dtype=np.int8)
    # packet = np.concatenate((sync_word, header, payload_bits))
    packet = np.concatenate((sync_word, payload_bits))
    return packet, sync_word


def сhannel_simulation(signal, noise_level, amplitude_variation, phase_variation):
    noise_length = len(signal) * 2
    white_noise_real = np.random.normal(0.0, noise_level, noise_length)
    white_noise_imag = np.random.normal(0.0, noise_level, noise_length)

    white_noise_real *= (noise_level)
    white_noise_imag *= (noise_level)

    # print((max(white_noise_real)))

    mid_index = len(white_noise_real) // 2
    start_index = mid_index - len(signal) // 2
    white_signal = np.zeros(noise_length, dtype=np.complex128)

    white_signal.real = white_noise_real
    white_signal.imag = white_noise_imag

    white_signal[start_index:start_index + len(signal)].real += signal.real
    white_signal[start_index:start_index + len(signal)].imag += signal.imag

    amplitude_factor = np.random.uniform(1 - amplitude_variation, 1 + amplitude_variation)
    white_signal *= amplitude_factor

    phase_shift = np.random.uniform(-phase_variation, phase_variation)
    white_signal *= np.exp(1j * phase_shift)

    return white_signal

# Передача
N = 10 # Оверсемплинг
# text = "txt"
text = "This is a text ? Yes !"
bit_sequence, num_bits = text_to_bit_sequence(text)
print(bit_sequence)

# Создаем пакет
# payload = bit_sequence
# packet, sync_word = create_packet(payload)


packet = bit_sequence
# выравнивание
if len(bit_sequence) % 2 != 0:
    packet = np.append(bit_sequence, 0)
    num_bits += 1

print(f"data len: {len(packet)/2}" )
# Преобразуем в 
qpsk_symbols = bits_to_qpsk(packet)
np.trim_zeros(qpsk_symbols)
# np.trim_zeros(qpsk_symbols.imag)
# Добавить синхр.
sync = bits_to_bpsk_complex(barker_sequence())
# combined_signal = np.concatenate((sync, qpsk_symbols))
combined_signal = qpsk_symbols
# combined_signal = qpsk_symbols
print(f"with sequence len: {len(combined_signal)}")
print(combined_signal)
combined_signal_app = oversampling(combined_signal, N)
combined_symbols_convolve = convolve_with_one(combined_signal_app, N)

# combined_symbols_convolve = сhannel_simulation(combined_symbols_convolve, 0.0 , 0, 0)
# combined_symbols_convolve = combined_symbols_convolve
combined_symbols_convolve = сhannel_simulation(combined_symbols_convolve, 0.35, 0.5, 0)

# real_part = (noisy_signal.real).astype(np.int16)
# imag_part = (noisy_signal.imag).astype(np.int16)
real_part = (combined_symbols_convolve.real * 1024)
imag_part = (combined_symbols_convolve.imag * 1024)


# real_part = np.trim_zeros(real_part)
# imag_part = np.trim_zeros(imag_part)
# plot_signal(combined_symbols_convolve.real, combined_symbols_convolve.imag)
combined = np.empty(real_part.size + imag_part.size, dtype=np.int16)
combined[0::2] = real_part
combined[1::2] = imag_part

# Сохранение
with open('qpsk_signal.bin', 'wb') as f:
    combined.tofile(f)

with open('qpsk_signal.txt', 'w') as f:
    for i in range(0, combined.size, 2):
        f.write(f"{combined[i]}, {combined[i + 1]}\n")

# with open('sync_word.txt', 'w') as f:
    # f.write("".join(map(str, sync_word)))
plot_signal(real_part, imag_part)
