import numpy as np
import random
import scipy.signal
from scipy.interpolate import interp1d
import struct
import matplotlib.pyplot as plt

# Глобальные параметры системы OFDM
nFreqSamples = 2048  # Количество поднесущих
pilotDistanceInSamples = 32  # Расстояние между пилотами
pilotAmplitude = 2  # Амплитуда пилотов
nData = 480  # Количество байт данных на символ
nCyclic = int(nFreqSamples * 2 / 4)  # Длина циклического префикса
symbolDuration = 1e-3  # Длительность символа (в секундах)
samplingRate = nFreqSamples / symbolDuration  # Частота дискретизации
subcarrierSpacing = samplingRate / nFreqSamples  # Частотный интервал между поднесущими
k_start = 1  # Начальный индекс поднесущей


# Модуль кодирования
def encode(signal, data, randomSeed=1):
    """
    Кодирует данные в OFDM-сигнал.
    :param signal: Исходный сигнал.
    :param data: Байты данных для передачи.
    :param randomSeed: Зерно генератора случайных чисел.
    :return: Кодированный сигнал и спектр.
    """
    spectrum = np.zeros(nFreqSamples, dtype=complex)
    k = k_start
    random.seed(randomSeed)
    pilot_counter = pilotDistanceInSamples / 2

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

            spectrum[k] = complex(bitstream[int(cnum * 2)], bitstream[int(cnum * 2 + 1)])
            k += 1
            if k >= nFreqSamples:
                k = 0

    complex_symbol = np.fft.ifft(spectrum)
    tx_symbol = np.zeros(len(complex_symbol) * 2)
    s = 1
    txindex = 0

    for smpl in complex_symbol:
        tx_symbol[txindex] = s * np.real(smpl)
        txindex += 1
        tx_symbol[txindex] = s * np.imag(smpl)
        txindex += 1
        s *= -1

    cyclicPrefix = tx_symbol[-nCyclic:]
    signal = np.concatenate((cyclicPrefix, tx_symbol))
    return signal, spectrum


# Модуль декодирования
def decode(signal, offset, randomSeed=1):
    """
    Декодирует OFDM-сигнал в данные.
    :param signal: Принятый сигнал.
    :param offset: Смещение начала символа.
    :param randomSeed: Зерно генератора случайных чисел.
    :return: Декодированные данные и дополнительная информация.
    """
    rxindex = offset + nCyclic
    rx_symbol = np.zeros(nFreqSamples, dtype=complex)
    s = 1

    for a in range(nFreqSamples):
        realpart = s * signal[rxindex]
        rxindex += 1
        imagpart = s * signal[rxindex]
        rxindex += 1
        rx_symbol[a] = complex(realpart, imagpart)
        s *= -1

    isymbol = np.fft.fft(rx_symbol)
    random.seed(randomSeed)
    k = k_start
    pilot_counter = pilotDistanceInSamples / 2
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

def decode_v2(signal, offset, randomSeed=1):
    """
    Декодирует OFDM-сигнал обратно в данные с сохранением информации о пилотах.
    
    :param signal: Принятый сигнал.
    :param offset: Смещение начала символа.
    :param randomSeed: Зерно генератора случайных чисел.
    :return: Декодированные данные, массив пилотов, диаграмма рассеяния и спектр.
    """
    rxindex = offset + nCyclic 
    rx_symbol = np.zeros(nFreqSamples, dtype=complex) 
    s = 1 
    
    for a in range(nFreqSamples):
        realpart = s * signal[rxindex]
        rxindex += 1
        imagpart = s * signal[rxindex] 
        rxindex += 1
        rx_symbol[a] = complex(realpart, imagpart) 
        s *= -1
    
    isymbol = np.fft.fft(rx_symbol)
    random.seed(randomSeed)
    k = k_start
    pilot_counter = pilotDistanceInSamples / 2
    data = np.zeros(nData)
    imPilots_ = [] 
    imPilots = 0
    constellation = []
    
    for x in range(nData):
        bitstream = np.zeros(8)
        for cnum in range(4):
            pilot_counter -= 1
            if pilot_counter <= 0:
                pilot_counter = pilotDistanceInSamples
                imPilots_.append(isymbol[k])  # Сохраняем значение пилотного сигнала
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
    
    return data.astype(np.uint8), imPilots_, constellation, isymbol

def decode_v3(signal, offset, randomSeed=1):
    rxindex = offset + nCyclic 
    rx_symbol = np.zeros(nFreqSamples, dtype=complex) 
    s = 1 
    for a in range(nFreqSamples):
        realpart = s * signal[rxindex]
        rxindex += 1
        imagpart = s * signal[rxindex] 
        rxindex += 1
        rx_symbol[a] = complex(realpart, imagpart) 
        s *= -1
    isymbol = np.fft.fft(rx_symbol)
    
    imPilots_ = []
    pilot_indices = []
    
    random.seed(randomSeed)
    k = k_start
    pilot_counter = pilotDistanceInSamples // 2 
    
    data = np.zeros(nData)
    constellation = []
    
    # собираем пилоты и их индексы
    for x in range(nData):
        for cnum in range(4):
            pilot_counter -= 1
            if pilot_counter <= 0:
                pilot_counter = pilotDistanceInSamples
                pilot_indices.append(k)  # индекс пилота
                imPilots_.append(isymbol[k])  # значение пилота
                k += 1
                if k >= nFreqSamples:
                    k = 0
            k += 1
            if k >= nFreqSamples:
                k = 0
    
    k = k_start
    pilot_counter = pilotDistanceInSamples // 2
    
    # Оценка канала на пилотах
    H_p = [y_p / pilotAmplitude for y_p in imPilots_]
    
    all_indices = np.arange(nFreqSamples)
    real_p = np.array([h.real for h in H_p])
    imag_p = np.array([h.imag for h in H_p])
    
    # quadratic linear nearest-up zero slinear cubic previous
    f_real = interp1d(pilot_indices, real_p, kind='slinear', fill_value="extrapolate")
    f_imag = interp1d(pilot_indices, imag_p, kind='slinear', fill_value="extrapolate")
    
    real_interpolated = f_real(all_indices)
    imag_interpolated = f_imag(all_indices)
    
    H_interpolated = real_interpolated + 1j * imag_interpolated
    
    epsilon = 1e-8
    corrected_spectrum = isymbol / (H_interpolated + epsilon)

    k = k_start
    pilot_counter = pilotDistanceInSamples // 2
    for x in range(nData):
        bitstream = np.zeros(8)
        for cnum in range(4):
            pilot_counter -= 1
            if pilot_counter <= 0:
                pilot_counter = pilotDistanceInSamples
                k += 1
                if k >= nFreqSamples:
                    k = 0
            sample = corrected_spectrum[k]
            constellation.append((sample.real, sample.imag))
            
            real_bit = 1 if sample.real > 0 else 0
            imag_bit = 1 if sample.imag > 0 else 0
            
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
    
    return data.astype(np.uint8), imPilots_, constellation, corrected_spectrum

def findSymbolStartIndex(signal, searchrangecoarse=None, searchrangefine=25):
    """
    Находит начало OFDM-символа в сигнале.
    
    :param signal: Входной сигнал.
    :param searchrangecoarse: Грубый диапазон поиска.
    :param searchrangefine: Точный диапазон поиска.
    :return: Кросскорреляция, значения мнимых пилотов и смещение начала символа.
    """
    if not searchrangecoarse:
        searchrangecoarse = nFreqSamples * 10  
    
    max_index = len(signal) - (nFreqSamples * 2 + nCyclic)
    if max_index <= 0:
        raise ValueError("Сигнал слишком короткий для обнаружения OFDM-символа.")
    
    crosscorr = [] 
    for i in range(min(searchrangecoarse, max_index)):
        s1 = signal[i:i + nCyclic]  # Циклический префикс
        s2 = signal[i + nFreqSamples * 2:i + nFreqSamples * 2 + nCyclic]  # Повтор циклического префикса
        if len(s1) > 0 and len(s2) > 0:
            cc = np.correlate(s1, s2)  #  кросскорреляция
            crosscorr.append(cc[0] if cc.size > 0 else 0)
        else:
            crosscorr.append(0)
    
    peaks, _ = scipy.signal.find_peaks(crosscorr, distance=nFreqSamples * 2)  #  пики
    o1 = peaks[0] if len(peaks) > 0 else 0  # начальный индекс
    
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
        data, pilots, constellation, received_spectrum = decode_v3(signal, offset)
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