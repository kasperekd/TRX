import numpy as np
import matplotlib.pyplot as plt
import commpy.modulation as cm
import scipy.signal

class OFDM:
    def __init__(self, modulation_type='QPSK', num_subcarriers=64, cp_length=16, pilot_spacing=16, pilot_value=1+1j, visualize=True):
        """
        Инициализация OFDM модуляции.
        
        Параметры:
        modulation_type (str): Тип модуляции ('QPSK', 'QAM64', 'QAM16', '8PSK', 'BPSK').
        num_subcarriers (int): Количество поднесущих.
        cp_length (int): Длина циклического префикса.
        pilot_spacing (int): Расстояние между пилотами (например, 16).
        pilot_value (complex): Значение всех пилотов (например, 1+1j).
        visualize (bool): Включить визуализацию.
        """
        self._setup_modulation(modulation_type)
        self.num_subcarriers = num_subcarriers
        self.cp_length = cp_length
        self.pilot_spacing = pilot_spacing
        self.pilot_value = pilot_value
        self.visualize = visualize
        
        # Генерация позиций пилотов через spacing
        self.pilot_positions = self._generate_pilot_positions()

    def _setup_modulation(self, modulation_type):
        """Настройка модуляции с PSKModem(4) для QPSK"""
        m = None
        if modulation_type == 'QPSK':
            m = 4
            self.modulation = cm.PSKModem(m)
        elif modulation_type == 'QAM64':
            m = 64
            self.modulation = cm.QAMModem(m)
        elif modulation_type == 'QAM16':
            m = 16
            self.modulation = cm.QAMModem(m)
        elif modulation_type == '8PSK':
            m = 8
            self.modulation = cm.PSKModem(m)
        elif modulation_type == 'BPSK':
            m = 2
            self.modulation = cm.PSKModem(m)
        else:
            raise ValueError(f"Unsupported modulation type: {modulation_type}")
        self.bits_per_symbol = int(np.log2(m))

    def _generate_pilot_positions(self):
        """Генерация позиций пилотов через spacing"""
        positions = []
        for i in range(0, self.num_subcarriers, self.pilot_spacing):
            positions.append(i)
        return positions

    def generate_ofdm_symbol(self, bits):
        """
        Формирование OFDM-символа от битов до комплексных отсчетов.
        
        Параметры:
        bits (np.array): Входные биты.
        
        Возвращает:
        np.array: Комплексные отсчеты OFDM-символа.
        """
        # Модуляция битов в символы
        data_symbols = self.modulate_bits(bits)
        
        # Создаем массив поднесущих (частотная область)
        subcarriers = np.zeros(self.num_subcarriers, dtype=complex)
        
        # Заполнение пилотов
        for pos in self.pilot_positions:
            subcarriers[pos] = self.pilot_value
        
        # Распределение данных на доступные поднесущие
        data_indices = [i for i in range(self.num_subcarriers) if i not in self.pilot_positions]
        if len(data_symbols) > len(data_indices):
            raise ValueError("Слишком много данных для доступных поднесущих")
        subcarriers[data_indices[:len(data_symbols)]] = data_symbols
        
        # Применение IFFT и добавление CP
        time_domain = np.fft.ifft(subcarriers)
        cp = time_domain[-self.cp_length:]
        ofdm_symbol = np.concatenate([cp, time_domain])
        
        # Визуализация
        self._visualize_all(subcarriers, ofdm_symbol)
        
        return ofdm_symbol

    def modulate_bits(self, bits):
        """Модуляция битов с добавлением padding"""
        remainder = len(bits) % self.bits_per_symbol
        if remainder != 0:
            padding = self.bits_per_symbol - remainder
            bits = np.concatenate([bits, np.zeros(padding, dtype=int)])
        return self.modulation.modulate(bits)

    def _visualize_all(self, subcarriers, ofdm_symbol):
        """Комплексная визуализация на одном сабплоте"""
        if not self.visualize:
            return
        
        fig = plt.figure(figsize=(12, 18))
        
        # Констелляция данных
        ax1 = fig.add_subplot(3, 1, 1)
        data_indices = [i for i in range(self.num_subcarriers) if i not in self.pilot_positions]
        data = subcarriers[data_indices]
        data = data[np.abs(data) > 1e-6]  # Убираем нулевые значения
        
        ax1.scatter(data.real, data.imag, s=10, label='Данные')
        ax1.set_title(f'Констелляция ({self.modulation.__class__.__name__})')
        ax1.set_xlabel('I (In-Phase)')
        ax1.set_ylabel('Q (Quadrature)')
        ax1.grid(True)
        ax1.legend()
        
        # Частотная область
        ax2 = fig.add_subplot(3, 1, 2)
        ax2.stem(np.abs(np.fft.fft(subcarriers)), markerfmt='C0o', basefmt='C0-')
        ax2.set_title('Частотная область OFDM-символа')
        ax2.set_xlabel('Поднесущие')
        ax2.set_ylabel('Амплитуда')
        
        # Выделение пилотов
        for pos in self.pilot_positions:
            ax2.axvline(x=pos, color='r', linestyle='--')
        
        # Временная область
        ax3 = fig.add_subplot(3, 1, 3)
        total_length = len(ofdm_symbol)
        cp_end = self.cp_length
        data_end = total_length
        
        ax3.plot(ofdm_symbol[:cp_end].real, label='Циклический префикс (CP)', color='green')
        ax3.plot(ofdm_symbol[:cp_end].imag, color='green', linestyle='--')
        
        ax3.plot(np.arange(cp_end, data_end), ofdm_symbol[cp_end:].real, label='Основной символ', color='blue')
        ax3.plot(np.arange(cp_end, data_end), ofdm_symbol[cp_end:].imag, color='blue', linestyle='--')
        
        ax3.set_title('Временная область OFDM-символа')
        ax3.set_xlabel('Отсчет')
        ax3.set_ylabel('Амплитуда')
        ax3.legend()
        
        plt.tight_layout()
        plt.show()

    def get_max_bits(self):
        """Возвращает максимальное количество бит, которое можно передать за один OFDM-символ"""
        data_subcarriers = self.num_subcarriers - len(self.pilot_positions)
        return data_subcarriers * self.bits_per_symbol

    def sync_correlation(self, received_signal):
        symbol_length = self.num_subcarriers + self.cp_length
        crosscorr = []
        
        for i in range(len(received_signal) - symbol_length + 1):
            cp_start = i
            cp_end = i + self.cp_length
            main_start = i + self.num_subcarriers
            main_end = main_start + self.cp_length
            
            if (cp_end <= len(received_signal)) and (main_end <= len(received_signal)):
                cp_segment = received_signal[cp_start:cp_end]
                main_segment = received_signal[main_start:main_end]
                cc = np.abs(np.correlate(cp_segment, main_segment, mode='valid')[0])
                crosscorr.append(cc)
            else:
                crosscorr.append(0)
        
        crosscorr = np.array(crosscorr)  # Преобразуем в numpy массив
        
        peaks, _ = scipy.signal.find_peaks(crosscorr, distance=self.num_subcarriers)
        
        if len(peaks) > 0:
            # Находим пик с максимальным значением
            max_peak_val = np.max(crosscorr[peaks])
            peak_indices = np.where(crosscorr == max_peak_val)[0]
            peak_index = peak_indices[0]  # Берем первый из возможных
        else:
            peak_index = 0  # Если пиков нет, возвращаем начало буфера
        
        if self.visualize:
            self._visualize_sync(received_signal, crosscorr, peak_index)
        print(peak_index)
        return peak_index

    def demodulate(self, received_signal):
        start_index = self.sync_correlation(received_signal)
        symbol_length = self.num_subcarriers + self.cp_length
        symbol_with_cp = received_signal[start_index:start_index + symbol_length]
        symbol = symbol_with_cp[self.cp_length:]
        freq_domain = np.fft.fft(symbol)
        
        data_indices = [i for i in range(self.num_subcarriers) if i not in self.pilot_positions]
        data = freq_domain[data_indices]
        
        # Исправление: добавляем параметр demod_type='hard' и bits=True
        demod_bits = self.modulation.demodulate(data, demod_type='hard')
        
        return demod_bits.astype(int)

    def _visualize_sync(self, received_signal, crosscorr, start_index):
        plt.figure(figsize=(14, 6))
        
        plt.subplot(2, 1, 1)
        plt.plot(crosscorr, label='Кросскорреляция')
        plt.scatter(start_index, crosscorr[start_index], color='red', label='Начало OFDM-символа')
        plt.title('Кросскорреляционный анализ')
        plt.legend()
        
        plt.subplot(2, 1, 2)
        plt.plot(received_signal.real, label='I')
        plt.plot(received_signal.imag, label='Q')
        plt.axvline(x=start_index, color='green', linestyle='--')
        plt.title('Синхронизация')
        plt.legend()
        plt.show()

    def __str__(self):
        return (f"OFDM Modulator ("
                f"Modulation: {self.modulation.__class__.__name__}, M={self.modulation.M}, "
                f"Subcarriers: {self.num_subcarriers}, "
                f"CP Length: {self.cp_length}, "
                f"Pilot Spacing: {self.pilot_spacing})")
    
if __name__ == "__main__":
    modulation_type = 'QPSK'
    num_subcarriers = 64
    cp_length = num_subcarriers // 2
    pilot_spacing = num_subcarriers // 8
    pilot_value = 1 + 1j

    ofdm = OFDM(
        modulation_type=modulation_type,
        num_subcarriers=num_subcarriers,
        cp_length=cp_length,
        pilot_spacing=pilot_spacing,
        pilot_value=pilot_value,
        visualize=True
    )


    max_bits = ofdm.get_max_bits()
    bits = np.random.randint(0, 2, max_bits)
    iq_samples = ofdm.generate_ofdm_symbol(bits)

    buffer_length = 1024
    noise = (np.random.randn(buffer_length) + 1j*np.random.randn(buffer_length)) * 0.02
    start_in_buffer = 200
    received_signal = np.copy(noise)
    received_signal[start_in_buffer:start_in_buffer+len(iq_samples)] += iq_samples

    demod_bits = ofdm.demodulate(received_signal)
    print("Исходные биты: ", bits[:10], "...")
    print("Демодулированные биты: ", demod_bits[:10], "...")
    
    correct = np.sum(bits == demod_bits[:len(bits)]) / len(bits)
    print(f"Точность: {correct * 100:.2f}%")