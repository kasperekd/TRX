import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import commpy as cpy

# Параметры системы
K = 1024  # Количество поднесущих OFDM
CP = K // 4  # Длина циклического префикса (25%)
P =  K // 64  # Количество пилотных сигналов
pilotValue = 3 + 3j  # Значение пилотного сигнала
Modulation_type = 'QAM16'  # Метод модуляции (BPSK, QPSK, 8PSK, QAM16, QAM64)
channel_type = 'random'  # Тип канала (awgn или random)
SNRdb = 10  # Отношение сигнал/шум на приемнике (дБ)

# Индексы поднесущих
allCarriers = np.arange(K)  # Номера поднесущих ([0, 1, ..., K-1])
pilotCarrier = allCarriers[::K // P]  # Каждая P-я поднесущая является пилотной
pilotCarriers = np.hstack([pilotCarrier, np.array([allCarriers[-1]])])  # Добавляем последнюю поднесущую как пилотную
P = P + 1  # Увеличиваем количество пилотных сигналов

dataCarriers = np.delete(allCarriers, pilotCarriers)  # Индексы данных поднесущих

# График расположения пилотов и данных
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

axes[0, 0].plot(pilotCarriers, np.zeros_like(pilotCarriers), 'bo', label='Пилоты')
axes[0, 0].plot(dataCarriers, np.zeros_like(dataCarriers), 'ro', label='Данные')
axes[0, 0].legend(fontsize=10, ncol=2)
axes[0, 0].set_xlim((-1, K))
axes[0, 0].set_ylim((-0.1, 0.3))
axes[0, 0].set_xlabel('Индекс поднесущей')
axes[0, 0].set_yticks([])
axes[0, 0].grid(True)
axes[0, 0].set_title('Расположение пилотов и данных')

# Карта модуляций
m_map = {"BPSK": 1, "QPSK": 2, "8PSK": 3, "QAM16": 4, "QAM64": 6}
mu = m_map[Modulation_type]
payloadBits_per_OFDM = len(dataCarriers) * mu  # Количество бит в каждом OFDM-символе

# Функция модуляции
def Modulation(bits):
    if Modulation_type == "QPSK":
        PSK4 = cpy.PSKModem(4)
        symbol = PSK4.modulate(bits)
        return symbol
    elif Modulation_type == "QAM64":
        QAM64 = cpy.QAMModem(64)
        symbol = QAM64.modulate(bits)
        return symbol
    elif Modulation_type == "QAM16":
        QAM16 = cpy.QAMModem(16)
        symbol = QAM16.modulate(bits)
        return symbol
    elif Modulation_type == "8PSK":
        PSK8 = cpy.PSKModem(8)
        symbol = PSK8.modulate(bits)
        return symbol
    elif Modulation_type == "BPSK":
        BPSK = cpy.PSKModem(2)
        symbol = BPSK.modulate(bits)
        return symbol

# Функция демодуляции
def DeModulation(symbol):
    if Modulation_type == "QPSK":
        PSK4 = cpy.PSKModem(4)
        bits = PSK4.demodulate(symbol, demod_type='hard')
        return bits
    elif Modulation_type == "QAM64":
        QAM64 = cpy.QAMModem(64)
        bits = QAM64.demodulate(symbol, demod_type='hard')
        return bits
    elif Modulation_type == "QAM16":
        QAM16 = cpy.QAMModem(16)
        bits = QAM16.demodulate(symbol, demod_type='hard')
        return bits
    elif Modulation_type == "8PSK":
        PSK8 = cpy.PSKModem(8)
        bits = PSK8.demodulate(symbol, demod_type='hard')
        return bits
    elif Modulation_type == "BPSK":
        BPSK = cpy.PSKModem(2)
        bits = BPSK.demodulate(symbol, demod_type='hard')
        return bits

# Импульсная характеристика канала
channelResponse = np.array([1, 0, 0.3 + 0.3j])
H_exact = np.fft.fft(channelResponse, K)

# Добавление AWGN шума
def add_awgn(x_s, snrDB):
    data_pwr = np.mean(abs(x_s ** 2))
    noise_pwr = data_pwr / (10 ** (snrDB / 10))
    noise = 1 / np.sqrt(2) * (np.random.randn(len(x_s)) + 1j * np.random.randn(len(x_s))) * np.sqrt(noise_pwr)
    return x_s + noise, noise_pwr

# Канал
def channel(in_signal, SNRdb, channel_type="awgn"):
    channelResponse = np.array([1, 0, 0.3 + 0.3j])  # Случайная импульсная характеристика канала
    if channel_type == "random":
        convolved = np.convolve(in_signal, channelResponse)
        out_signal, noise_pwr = add_awgn(convolved, SNRdb)
    elif channel_type == "awgn":
        out_signal, noise_pwr = add_awgn(in_signal, SNRdb)
    return out_signal, noise_pwr

# 1. Генерация потока битов
bits = np.random.binomial(n=1, p=0.5, size=(payloadBits_per_OFDM,))
# 2. Модуляция битового потока
QAM_s = Modulation(bits)
# 3. Вставка пилотов и данных для создания OFDM-символа
def OFDM_symbol(QAM_payload):
    symbol = np.zeros(K, dtype=complex)
    symbol[pilotCarriers] = pilotValue
    symbol[dataCarriers] = QAM_payload
    return symbol

OFDM_data = OFDM_symbol(QAM_s)
# 4. Быстрое преобразование Фурье (обратное)
def IDFT(OFDM_data):
    return np.fft.ifft(OFDM_data)

OFDM_time = IDFT(OFDM_data)
# 5. Добавление циклического префикса
def addCP(OFDM_time):
    cp = OFDM_time[-CP:]
    return np.hstack([cp, OFDM_time])

OFDM_withCP = addCP(OFDM_time)
# 6. Передача через канал
OFDM_TX = OFDM_withCP
OFDM_RX = channel(OFDM_TX, SNRdb, "random")[0]

axes[1, 0].plot(abs(OFDM_TX), label='TX сигнал')
axes[1, 0].plot(abs(OFDM_RX), label='RX сигнал')
axes[1, 0].legend(fontsize=10)
axes[1, 0].set_xlabel('Время')
axes[1, 0].set_ylabel('|x(t)|')
axes[1, 0].grid(True)
axes[1, 0].set_title('Сигнал передатчика и приемника')

# 7. Удаление циклического префикса
def removeCP(signal):
    return signal[CP:(CP + K)]

OFDM_RX_noCP = removeCP(OFDM_RX)
# 8. Преобразование Фурье
def DFT(OFDM_RX):
    return np.fft.fft(OFDM_RX)

OFDM_demod = DFT(OFDM_RX_noCP)
# 9. Оценка канала
def channelEstimate(OFDM_demod):
    pilots = OFDM_demod[pilotCarriers]
    Hest_at_pilots = pilots / pilotValue

    Hest_abs = interpolate.interp1d(pilotCarriers, abs(Hest_at_pilots), kind='linear')(allCarriers)
    Hest_phase = interpolate.interp1d(pilotCarriers, np.angle(Hest_at_pilots), kind='linear')(allCarriers)
    Hest = Hest_abs * np.exp(1j * Hest_phase)

    axes[1, 1].plot(allCarriers, abs(H_exact), label='Точный канал')
    axes[1, 1].scatter(pilotCarriers, abs(Hest_at_pilots), label='Оценки пилотов')
    axes[1, 1].plot(allCarriers, abs(Hest), label='Оцененный канал')
    axes[1, 1].grid(True)
    axes[1, 1].set_xlabel('Индекс поднесущей')
    axes[1, 1].set_ylabel('|H(f)|')
    axes[1, 1].legend(fontsize=10)
    axes[1, 1].set_ylim(0, 2)
    axes[1, 1].set_title('Оценка канала')

    return Hest

Hest = channelEstimate(OFDM_demod)
# 10. Равномеризация
def equalize(OFDM_demod, Hest):
    return OFDM_demod / Hest

equalized_Hest = equalize(OFDM_demod, Hest)

def get_payload(equalized):
    return equalized[dataCarriers]

QAM_est = get_payload(equalized_Hest)
# 11. Визуализация constellation диаграммы
axes[0, 1].scatter(QAM_est.real, QAM_est.imag, color='blue', label='Полученные данные')  # Только scatter
axes[0, 1].scatter(QAM_s.real, QAM_s.imag, color='red', label='Исходные данные')  # Только scatter
axes[0, 1].legend()
axes[0, 1].grid(True)
axes[0, 1].set_xlabel('Действительная часть')
axes[0, 1].set_ylabel('Мнимая часть')
axes[0, 1].set_title('Constellation диаграмма')

# 12. Демодуляция
bits_est = DeModulation(QAM_est)
# 13. Расчет BER
print("Ошибка битов BER:", np.sum(abs(bits - bits_est)) / len(bits))

plt.tight_layout()
plt.show()