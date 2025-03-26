import numpy as np
import random
import scipy.signal
from scipy.interpolate import interp1d
import struct
import matplotlib.pyplot as plt

# Глобальные параметры системы OFDM
nFreqSamples = 2048  # Количество поднесущих
pilotDistanceInSamples = 32  # Расстояние между пилотами
pilotAmplitude = 2  # Амплитуда пилотов (комплексная)
nData = 480  # Количество байт данных на символ
nCyclic = int(nFreqSamples / 4)  # Длина циклического префикса (комплексные отсчеты)
symbolDuration = 1e-3  # Длительность символа (в секундах)
samplingRate = nFreqSamples / symbolDuration  # Частота дискретизации
subcarrierSpacing = samplingRate / nFreqSamples  # Частотный интервал между поднесущими
k_start = 1  # Начальный индекс поднесущей

def encode(signal, data, randomSeed=1):
    spectrum = np.zeros(nFreqSamples, dtype=complex)
    k = k_start
    random.seed(randomSeed)
    pilot_counter = pilotDistanceInSamples // 2

    for x in range(nData):
        databyte = int(data[x])
        r = random.randint(0, 255)
        databyte ^= r
        bitstream = np.zeros(8)

        for bit in range(8):
            m = 1 << bit
            bitstream[bit] = 1 if (databyte & m) else -1

        for cnum in range(4):
            pilot_counter -= 1
            if pilot_counter <= 0:
                spectrum[k] = pilotAmplitude
                k += 1
                pilot_counter = pilotDistanceInSamples
                if k >= nFreqSamples:
                    k = 0

            # Кодирование данных в комплексные символы
            real_part = bitstream[int(cnum * 2)]
            imag_part = bitstream[int(cnum * 2 + 1)]
            spectrum[k] = complex(real_part, imag_part)
            k += 1
            if k >= nFreqSamples:
                k = 0

    complex_symbol = np.fft.ifft(spectrum)
    cyclicPrefix = complex_symbol[-nCyclic:]
    tx_symbol = np.concatenate((cyclicPrefix, complex_symbol))
    return tx_symbol, spectrum

def decode(signal, offset, randomSeed=1):
    rxindex = offset + nCyclic
    rx_symbol = signal[rxindex:rxindex + nFreqSamples]
    isymbol = np.fft.fft(rx_symbol)
    
    random.seed(randomSeed)
    k = k_start
    pilot_counter = pilotDistanceInSamples // 2
    data = np.zeros(nData)
    imPilots = 0
    constellation = []

    for x in range(nData):
        bitstream = np.zeros(8)

        for cnum in range(4):
            pilot_counter -= 1
            if pilot_counter <= 0:
                pilot_counter = pilotDistanceInSamples
                imPilots += np.abs(np.imag(isymbol[k]))
                k += 1
                if k >= nFreqSamples:
                    k = 0

            constellation.append((np.real(isymbol[k]), np.imag(isymbol[k])))
            real_bit = 1 if np.real(isymbol[k]) > 0 else 0
            imag_bit = 1 if np.imag(isymbol[k]) > 0 else 0
            bitstream[int(cnum * 2)] = real_bit
            bitstream[int(cnum * 2 + 1)] = imag_bit
            k += 1
            if k >= nFreqSamples:
                k = 0

        databyte = 0
        for bit in range(8):
            if bitstream[bit] > 0:
                databyte |= (1 << bit)

        r = random.randint(0, 255)
        databyte ^= r
        data[x] = databyte

    return data.astype(np.uint8), imPilots, constellation, isymbol

def findSymbolStartIndex(signal, searchrangecoarse=None, searchrangefine=25):
    if not searchrangecoarse:
        searchrangecoarse = nFreqSamples * 10

    max_index = len(signal) - (nFreqSamples + nCyclic)
    if max_index <= 0:
        raise ValueError("Сигнал слишком короткий для обнаружения OFDM-символа.")

    crosscorr = []
    for i in range(min(searchrangecoarse, max_index)):
        s1 = signal[i:i + nCyclic]
        s2 = signal[i + nFreqSamples:i + nFreqSamples + nCyclic]
        if len(s1) == len(s2):
            cc = np.correlate(s1, s2.conj()).real
            crosscorr.append(cc[0] if cc.size > 0 else 0)
        else:
            crosscorr.append(0)

    peaks, _ = scipy.signal.find_peaks(crosscorr, distance=nFreqSamples)
    o1 = peaks[0] if len(peaks) > 0 else 0

    imagpilots = []
    for i in range(max(0, o1 - searchrangefine), min(o1 + searchrangefine, max_index)):
        _, im, _, _ = decode(signal, i)
        imagpilots.append(im)

    best_idx = np.argmin(imagpilots)
    o2 = o1 - searchrangefine + best_idx

    return crosscorr, imagpilots, o2

def prepare_data_for_transmission(text, message_type=0x01):
    """
    Подготавливает данные для передачи с учетом новой структуры.
    :param text: Исходный текст для передачи.
    :param message_type: Тип сообщения.
    :return: Список блоков данных для передачи.
    """
    text_bytes = text.encode('utf-8')
    total_length = len(text_bytes)
    length_header = struct.pack('>I', total_length)
    type_header = struct.pack('B', message_type)
    header = length_header + type_header
    data_with_header = header + text_bytes

    chunks = []
    for i in range(0, len(data_with_header), nData):
        chunk = data_with_header[i:i + nData]
        if len(chunk) < nData:
            chunk += b'\x00' * (nData - len(chunk))
        chunks.append(chunk)

    return chunks

def visualize_resource_grid(resource_grid, title="Resource Grid"):
    """
    Визуализирует ресурсную сетку.
    
    :param resource_grid: Матрица амплитуд частотных компонент.
    :param title: Заголовок графика.
    """
    plt.figure(figsize=(12, 6))
    plt.imshow(np.abs(resource_grid), aspect='auto', cmap='viridis', interpolation='none')
    plt.colorbar(label="Амплитуда")
    plt.title(title)
    plt.xlabel("Поднесущие")
    plt.ylabel("Символы времени")
    plt.show()

def visualize_old_plots(crosscorr, imagpilots, offset, constellation, signal):
    """
    Строит графики для анализа: диаграмма рассеяния, корреляция циклического префикса, мнимая часть пилотов и сигнал.
    
    :param crosscorr: Массив значений кросскорреляции.
    :param imagpilots: Массив значений мнимой части пилотов.
    :param offset: Смещение начала символа.
    :param constellation: Диаграмма рассеяния.
    :param signal: Исходный сигнал.
    """
    plt.figure(figsize=(18, 12))
    plt.subplot(241)
    constellation = np.array(constellation)
    plt.scatter(constellation[:, 0], constellation[:, 1], alpha=0.5)
    plt.title("Constellation Diagram")
    plt.xlabel("Real")
    plt.ylabel("Imaginary")
    plt.grid()
    
    plt.subplot(242)
    plt.plot(crosscorr)
    plt.axvline(x=offset, color='r', linestyle='--', label="Detected Symbol Start")
    plt.title("Cross-Correlation for Cyclic Prefix")
    plt.xlabel("Sample Index")
    plt.ylabel("Correlation")
    plt.legend()
    
    plt.subplot(243)
    plt.plot(range(len(imagpilots)), imagpilots)
    plt.title("Pilot Imaginary Parts for Fine Synchronization")
    plt.xlabel("Relative Sample Index")
    plt.ylabel("Sum of Imaginary Parts")
    
    plt.subplot(244)
    plt.plot(signal)
    plt.title("Signal")
    plt.tight_layout()
    plt.show()

def decode_message(data_chunks):
    """
    Декодирует полученные данные.
    :param data_chunks: Список блоков данных.
    :return: Восстановленное сообщение и тип сообщения.
    """
    all_data = b''.join(data_chunks)
    length_header = all_data[:4]
    type_header = all_data[4:5]
    total_length = struct.unpack('>I', length_header)[0]
    message_type = struct.unpack('B', type_header)[0]
    payload = all_data[5:5 + total_length]
    return payload.decode('utf-8', errors='ignore'), message_type

def validate_parameters():
    """
    Проверяет параметры системы OFDM на корректность.
    """
    nPilots = nFreqSamples // pilotDistanceInSamples
    max_nData = (nFreqSamples - nPilots) // 4 
    if nData > max_nData:
        raise ValueError(f"Значение nData ({nData}) слишком велико. Максимальное допустимое значение: {max_nData}.")

def main():
    validate_parameters()
    input_file = "input.txt"
    output_file = "output.txt"

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"Файл {input_file} не найден.")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    chunks = prepare_data_for_transmission(text, message_type=0x01)
    signal = np.zeros(nFreqSamples)
    transmitted_resource_grid = []
    received_resource_grid = []
    all_constellation = []

    for chunk in chunks:
        signal_, spectrum = encode(signal, np.frombuffer(chunk, dtype=np.uint8))
        signal = np.append(signal, signal_)
        transmitted_resource_grid.append(spectrum)

    signal = np.append(signal, np.zeros(nFreqSamples * 1))
    noise_kernel = np.random.normal(loc=0, scale=1, size=10)
    signal = scipy.signal.convolve(signal, noise_kernel, mode='full')

    crosscorr, imagpilots, offset = findSymbolStartIndex(signal)
    all_pilots = []
    received_chunks = []

    for _ in range(len(chunks)):
        data, pilots, constellation, received_spectrum = decode(signal, offset)
        received_chunks.append(bytes(data))
        all_constellation.extend(constellation)
        received_resource_grid.append(received_spectrum)
        all_pilots.extend(pilots)

    received_text, message_type = decode_message(received_chunks)

    plt.figure(figsize=(12, 6))
    plt.plot(np.abs(all_pilots), 'ro-', markersize=5)
    plt.title("Пилотные сигналы")
    plt.xlabel("Индекс пилота")
    plt.ylabel("Амплитуда")
    plt.grid(True)
    plt.show()

    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(received_text)
        print(f"Декодированный текст успешно записан в файл: {output_file}")
    except Exception as e:
        print(f"Ошибка при записи в файл: {e}")

    transmitted_resource_grid = np.array(transmitted_resource_grid).T
    received_resource_grid = np.array(received_resource_grid).T

    visualize_resource_grid(transmitted_resource_grid, title="Transmitted Resource Grid")
    visualize_resource_grid(received_resource_grid, title="Received Resource Grid")
    visualize_old_plots(crosscorr, imagpilots, offset, all_constellation, signal)


if __name__ == "__main__":
    main()