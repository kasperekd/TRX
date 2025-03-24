import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import commpy.modulation as cm

class OFDM:
    def __init__(self, K=64, CP=None, P=8, pilotValue=3+3j, Modulation_type='QPSK'):
        self.K = K
        self.CP = CP if CP is not None else K // 4
        self.P = P
        self.pilotValue = pilotValue
        self.Modulation_type = Modulation_type
        
        self.allCarriers = np.arange(K)
        self.pilotCarrier = self.allCarriers[::K // P]
        self.pilotCarriers = np.hstack([self.pilotCarrier, np.array([self.allCarriers[-1]])])
        self.P += 1
        
        self.dataCarriers = np.delete(self.allCarriers, self.pilotCarriers)
        
        self.m_map = {"BPSK": 1, "QPSK": 2, "8PSK": 3, "QAM16": 4, "QAM64": 6}
        self.mu = self.m_map[self.Modulation_type]
        self.payloadBits_per_OFDM = len(self.dataCarriers) * self.mu
    
    def modulate(self, bits):
        modulated_bits = self._modulation(bits)
        ofdm_symbol = self._create_ofdm_symbol(modulated_bits)
        ofdm_time = self._idft(ofdm_symbol)
        ofdm_with_cp = self._add_cp(ofdm_time)
        return ofdm_with_cp, ofdm_symbol
    
    def demodulate(self, received_signal):
        sync_offset = self._time_sync(received_signal)
        print(sync_offset)
        received_signal_no_cp = self._remove_cp(received_signal[sync_offset:])
        ofdm_demod = self._dft(received_signal_no_cp)
        h_est = self._channel_estimate(ofdm_demod)
        freq_offset = self._freq_sync(ofdm_demod, h_est)
        ofdm_demod = ofdm_demod * np.exp(-1j * 2 * np.pi * freq_offset * np.arange(self.K))
        equalized = self._equalize(ofdm_demod, h_est)
        qam_est = self._get_payload(equalized)
        bits_est = self._demodulation(qam_est)
        return bits_est, h_est, qam_est
    
    def _time_sync(self, received_signal):
        corr = np.correlate(received_signal, received_signal, mode='full')
        corr = corr[len(corr) // 2:]
        max_corr_idx = np.argmax(corr)
        return max_corr_idx
    
    def _freq_sync(self, ofdm_demod, h_est):
        pilot_values = ofdm_demod[self.pilotCarriers] / h_est[self.pilotCarriers]
        freq_offset = np.angle(pilot_values[1:] / pilot_values[:-1]).mean() / (2 * np.pi * self.K)
        return freq_offset

    def _modulation(self, bits):
        if self.Modulation_type == "QPSK":
            modem = cm.PSKModem(4)
        elif self.Modulation_type == "QAM64":
            modem = cm.QAMModem(64)
        elif self.Modulation_type == "QAM16":
            modem = cm.QAMModem(16)
        elif self.Modulation_type == "8PSK":
            modem = cm.PSKModem(8)
        elif self.Modulation_type == "BPSK":
            modem = cm.PSKModem(2)
        else:
            raise ValueError(f"Unsupported modulation type: {self.Modulation_type}")
        
        symbol = modem.modulate(bits)
        return symbol
    
    def _demodulation(self, symbol):
        if self.Modulation_type == "QPSK":
            modem = cm.PSKModem(4)
        elif self.Modulation_type == "QAM64":
            modem = cm.QAMModem(64)
        elif self.Modulation_type == "QAM16":
            modem = cm.QAMModem(16)
        elif self.Modulation_type == "8PSK":
            modem = cm.PSKModem(8)
        elif self.Modulation_type == "BPSK":
            modem = cm.PSKModem(2)
        else:
            raise ValueError(f"Unsupported modulation type: {self.Modulation_type}")
        
        bits = modem.demodulate(symbol, demod_type='hard')
        return bits
    
    def _create_ofdm_symbol(self, QAM_payload):
        symbol = np.zeros(self.K, dtype=complex)
        symbol[self.pilotCarriers] = self.pilotValue
        symbol[self.dataCarriers] = QAM_payload
        return symbol
    
    def _idft(self, OFDM_data):
        return np.fft.ifft(OFDM_data)
    
    def _add_cp(self, OFDM_time):
        cp = OFDM_time[-self.CP:]
        return np.hstack([cp, OFDM_time])
    
    def _remove_cp(self, signal):
        return signal[self.CP:(self.CP + self.K)]
    
    def _dft(self, OFDM_RX):
        return np.fft.fft(OFDM_RX)
    
    def _channel_estimate(self, OFDM_demod):
        pilots = OFDM_demod[self.pilotCarriers]
        Hest_at_pilots = pilots / self.pilotValue

        Hest_abs = interpolate.interp1d(self.pilotCarriers, abs(Hest_at_pilots), kind='linear')(self.allCarriers)
        Hest_phase = interpolate.interp1d(self.pilotCarriers, np.angle(Hest_at_pilots), kind='linear')(self.allCarriers)
        Hest = Hest_abs * np.exp(1j * Hest_phase)
        return Hest
    
    def _equalize(self, OFDM_demod, Hest):
        return OFDM_demod / Hest
    
    def _get_payload(self, equalized):
        return equalized[self.dataCarriers]
    
    def plot(self, original_symbols, tx_signal, rx_signal, h_est, qam_est, noise_samples):
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        axes[0, 0].stem(self.allCarriers, np.abs(original_symbols), basefmt=" ", )
        axes[0, 0].plot(self.pilotCarriers, np.abs(original_symbols[self.pilotCarriers]), 'bo', label='Пилоты')
        axes[0, 0].plot(self.dataCarriers, np.abs(original_symbols[self.dataCarriers]), 'ro', label='Данные')
        axes[0, 0].legend(fontsize=10, ncol=2)
        axes[0, 0].set_xlabel('Индекс поднесущей')
        axes[0, 0].set_ylabel('|Символ|')
        axes[0, 0].grid(True)
        axes[0, 0].set_title('Исходный OFDM-символ')

        time_indices_rx = np.arange(len(rx_signal))
        time_indices_tx = np.arange(len(tx_signal)) + noise_samples
        
        axes[0, 1].plot(time_indices_rx, abs(rx_signal), label='RX сигнал')
        axes[0, 1].plot(time_indices_tx, abs(tx_signal), label='TX сигнал', linestyle='--')
        axes[0, 1].legend(fontsize=10)
        axes[0, 1].set_xlabel('Время')
        axes[0, 1].set_ylabel('|x(t)|')
        axes[0, 1].grid(True)
        axes[0, 1].set_title('Сигнал передатчика и приемника')

        axes[1, 0].scatter(original_symbols.real, original_symbols.imag, color='red', label='Исходные данные', s=50, alpha=0.7)
        axes[1, 0].scatter(qam_est.real, qam_est.imag, color='blue', label='Полученные данные', s=50, alpha=0.7)
        axes[1, 0].legend(fontsize=10)
        axes[1, 0].grid(True)
        axes[1, 0].set_xlabel('Действительная часть')
        axes[1, 0].set_ylabel('Мнимая часть')
        axes[1, 0].set_title('Созвездие (Исходные vs Полученные)')
        axes[1, 0].set_aspect('equal', 'box')

        # 4. Оценка канала по пилотам
        H_exact = np.fft.fft(np.array([1, 0, 0.3 + 0.3j]), self.K)
        axes[1, 1].plot(self.allCarriers, abs(H_exact), label='Точный канал')
        axes[1, 1].scatter(self.pilotCarriers, abs(h_est[self.pilotCarriers]), label='Оценки пилотов', color='green')
        axes[1, 1].plot(self.allCarriers, abs(h_est), label='Оцененный канал', color='orange')
        axes[1, 1].grid(True)
        axes[1, 1].set_xlabel('Индекс поднесущей')
        axes[1, 1].set_ylabel('|H(f)|')
        axes[1, 1].legend(fontsize=10)
        axes[1, 1].set_title('Оценка канала')

        plt.tight_layout()
        plt.show()

class Channel:
    def __init__(self, channel_type='random', SNRdb=25, noise_samples=10):
        self.channel_type = channel_type
        self.SNRdb = SNRdb
        self.channelResponse = np.array([1, 0, 0.3 + 0.3j])
        self.noise_samples = noise_samples
    
    def pass_through(self, in_signal):
        if self.channel_type == "random":
            convolved = np.convolve(in_signal, self.channelResponse)
            out_signal, noise_pwr = self._add_awgn(convolved, self.SNRdb)
        elif self.channel_type == "awgn":
            out_signal, noise_pwr = self._add_awgn(in_signal, self.SNRdb)
        else:
            raise ValueError(f"Unsupported channel type: {self.channel_type}")
        
        noise_before = self._generate_noise(self.noise_samples, noise_pwr)
        noise_after = self._generate_noise(self.noise_samples, noise_pwr)
        out_signal = np.concatenate((noise_before, out_signal, noise_after))
        return out_signal, noise_pwr
    
    def _add_awgn(self, x_s, snrDB):
        data_pwr = np.mean(abs(x_s ** 2))
        noise_pwr = data_pwr / (10 ** (snrDB / 10))
        noise = 1 / np.sqrt(2) * (np.random.randn(len(x_s)) + 1j * np.random.randn(len(x_s))) * np.sqrt(noise_pwr)
        return x_s + noise, noise_pwr
    
    def _generate_noise(self, num_samples, noise_pwr):
        return 1 / np.sqrt(2) * (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * np.sqrt(noise_pwr)

def main_sim():
    K = 64  # Количество поднесущих OFDM
    CP = K // 4  # Длина циклического префикса (25%)
    P = 8  # Количество пилотных сигналов
    pilotValue = 3 + 3j  # Значение пилотного сигнала
    Modulation_type = 'QPSK'  # (BPSK, QPSK, 8PSK, QAM16, QAM64)
    channel_type = 'random'  # (awgn или random)
    SNRdb = 50
    noise_samples = 100

    ofdm = OFDM(K=K, CP=CP, P=P, pilotValue=pilotValue, Modulation_type=Modulation_type)
    channel = Channel(channel_type=channel_type, SNRdb=SNRdb, noise_samples=noise_samples)

    bits = np.random.binomial(n=1, p=0.5, size=(ofdm.payloadBits_per_OFDM,))

    tx_signal, original_symbols = ofdm.modulate(bits)

    rx_signal, noise_pwr = channel.pass_through(tx_signal)

    bits_est, h_est, qam_est = ofdm.demodulate(rx_signal) #[noise_samples:-noise_samples]

    ber = np.sum(abs(bits - bits_est)) / len(bits)
    print("Ошибка битов BER:", ber)

    ofdm.plot(original_symbols, tx_signal, rx_signal, h_est, qam_est, noise_samples)

def text_to_bits(text):
    bits = []
    for char in text:
        bits.extend(format(ord(char), '08b'))
    return np.array(bits, dtype=int)

def bits_to_text(bits):
    chars = []
    for b in range(0, len(bits), 8):
        byte = bits[b:b+8]
        chars.append(chr(int(''.join(str(bit) for bit in byte), 2)))
    return ''.join(chars)

def main():
    # python3 main.py modulate input.txt output_iq.txt --K 64 --CP 16 --P 8 --pilotValue 3+3j --Modulation_type QAM64 --file_format text
    # python3 main.py demodulate output_iq.txt decoded_output.txt --K 64 --CP 16 --P 8 --pilotValue 3+3j --Modulation_type QAM64 --file_format text

    # python3 main.py modulate input.txt output_iq.bin --K 64 --CP 16 --P 8 --pilotValue 3+3j --Modulation_type QAM64 --file_format binary
    # python3 main.py demodulate output_iq.bin decoded_output.txt --K 64 --CP 16 --P 8 --pilotValue 3+3j --Modulation_type QAM64 --file_format binary


    parser = argparse.ArgumentParser(description="OFDM Modulation and Demodulation")
    parser.add_argument("mode", choices=["modulate", "demodulate"], help="Mode of operation: modulate or demodulate")
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("output_file", help="Path to the output file")
    parser.add_argument("--K", type=int, default=64, help="Number of OFDM subcarriers")
    parser.add_argument("--CP", type=int, default=None, help="Length of cyclic prefix")
    parser.add_argument("--P", type=int, default=8, help="Number of pilot signals")
    parser.add_argument("--pilotValue", type=complex, default=3+3j, help="Value of pilot signal")
    parser.add_argument("--Modulation_type", default='QPSK', choices=["BPSK", "QPSK", "8PSK", "QAM16", "QAM64"], help="Modulation method")
    
    args = parser.parse_args()

    ofdm = OFDM(K=args.K, CP=args.CP, P=args.P, pilotValue=args.pilotValue, Modulation_type=args.Modulation_type)

    if args.mode == "modulate":
        with open(args.input_file, 'r') as file:
            text = file.read()
        
        bits = text_to_bits(text)
        
        num_symbols = (len(bits) + ofdm.payloadBits_per_OFDM - 1) // ofdm.payloadBits_per_OFDM
        bit_chunks = [bits[i*ofdm.payloadBits_per_OFDM:(i+1)*ofdm.payloadBits_per_OFDM] for i in range(num_symbols)]
        
        ofdm_symbols = []
        for chunk in bit_chunks:
            if len(chunk) < ofdm.payloadBits_per_OFDM:
                chunk = np.pad(chunk, (0, ofdm.payloadBits_per_OFDM - len(chunk)), mode='constant')
            tx_signal, original_symbol = ofdm.modulate(chunk)
            ofdm_symbols.append(tx_signal)
        
        tx_signal_flat = np.concatenate(ofdm_symbols)
        
        with open(args.output_file, 'wb') as file:
            iq_samples = np.vstack((tx_signal_flat.real, tx_signal_flat.imag)).T.astype(np.float32)
            iq_samples.tofile(file)
    
    elif args.mode == "demodulate":
        iq_samples = np.fromfile(args.input_file, dtype=np.float32)
        iq_samples = iq_samples.reshape(-1, 2)
        
        received_signal = iq_samples[:, 0] + 1j * iq_samples[:, 1]
        
        ofdm_symbol_length = ofdm.K + ofdm.CP
        num_symbols = len(received_signal) // ofdm_symbol_length
        ofdm_symbols = [received_signal[i*ofdm_symbol_length:(i+1)*ofdm_symbol_length] for i in range(num_symbols)]
        
        all_bits_est = []
        for symbol in ofdm_symbols:
            bits_est, h_est, qam_est = ofdm.demodulate(symbol)
            all_bits_est.extend(bits_est)
        
        decoded_text = bits_to_text(all_bits_est)
        
        with open(args.output_file, 'w') as file:
            file.write(decoded_text)

if __name__ == "__main__":
    main_sim()
    # main()