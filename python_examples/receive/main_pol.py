import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

def plot_eye_diagram(signal, sps, num_traces=100):
    plt.figure(figsize=(12, 6))
    plt.title('Eye Diagram')
    plt.xlabel('Time (samples)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    for i in range(num_traces):
        start_idx = i * sps
        if start_idx + 2 * sps > len(signal):
            break
        plt.plot(range(2 * sps), signal[start_idx:start_idx + 2 * sps].real, color='blue', alpha=0.5)

def timing_recovery(IQ, alg, Nsps, n1st, DF):
    N = len(IQ)
    I = np.real(IQ)
    Q = np.imag(IQ)

    damp = np.sqrt(2) / 2
    band = (0.5 * np.pi / 500) / (damp + 1/(4*damp))
    mi1 = (4 * damp * band) / ((1 + 2*damp*band + band**2) * DF)
    mi2 = (4 * band**2) / ((1 + 2*damp*band + band**2) * DF)
    
    err = []
    offset = []
    
    if Nsps > 2:
        k = 0
        ns = [n1st]
        offs = 0
        adap1 = 0
        adap2 = 0
        
        for n in range(n1st, len(IQ) - 2*Nsps, Nsps):
            if alg == 3:
                a = (I[n + Nsps + offs] - I[n + offs]) * I[n + Nsps//2 + offs]
                b = (Q[n + Nsps + offs] - Q[n + offs]) * Q[n + Nsps//2 + offs]
                current_err = -(a + b)
            elif alg == 4:
                current_err = -np.real(
                    (np.conj(IQ[n + Nsps + offs]) - np.conj(IQ[n + offs])) * IQ[n + Nsps//2 + offs]
                )
            elif alg == 5:
                a = I[n + offs] * np.sign(I[n + Nsps + offs]) - I[n + Nsps + offs] * np.sign(I[n + offs])
                b = Q[n + offs] * np.sign(Q[n + Nsps + offs]) - Q[n + Nsps + offs] * np.sign(Q[n + offs])
                current_err = -(a + b)
            
            adap2 += mi2 * current_err
            adap1 += adap2 + mi1 * current_err
            
            while adap1 > 1:
                adap1 -= 1
            while adap1 < -1:
                adap1 += 1
            
            offs = int(round(adap1 * Nsps))
            err.append(current_err)
            offset.append(offs)
            k += 1
            ns.append(n + Nsps + offs)
        
        IQs = IQ[ns]
        ns = np.array(ns)
    
    return ns, IQs, np.array(err), np.array(offset)

# filename = '/home/kasperekd/TRX/data/qpsk_signal.bin'
filename = '/home/kasperekd/TRX/data/new/txdata2.pcm'
# filename = '../../data/qpsk_signal_no_phase.bin'
# filename = '../../data/qpsk_signal_noise.bin'
data = np.fromfile(filename, dtype=np.int16).astype(np.float32)

start_sample = 0 * 2
end_sample = 99999 * 2
# start_sample = 25200 * 2
# end_sample = 25700 * 2

selected_data = data[start_sample:end_sample]

I = selected_data[::2]
Q = selected_data[1::2]

I /= np.max(np.abs(I) + 1e-6)
Q /= np.max(np.abs(Q) + 1e-6)

IQ = I + 1j*Q

# Применение фильтра
filter_length = 10
h = np.ones(filter_length)
I_filtered = signal.convolve(I, h, mode='full')[:len(I)]
Q_filtered = signal.convolve(Q, h, mode='full')[:len(Q)]
IQ_filtered = I_filtered + 1j*Q_filtered

alg = 3
Nsps = 10
n1st = 1

ns, IQs, err, offset = timing_recovery(IQ_filtered, alg, Nsps, n1st, 6)

plt.figure(figsize=(15, 20))

plt.subplot(5, 2, 1)
plt.plot(np.real(IQ), 'b', linewidth=1)
plt.plot(np.imag(IQ), 'r', linewidth=1)
plt.title('Исходный сигнал')
plt.xlabel('Выборка')
plt.ylabel('Амплитуда')
plt.grid(True)

plt.subplot(5, 2, 2)
plt.scatter(np.real(IQ), np.imag(IQ), s=10)
plt.title('Созвездие исходного сигнала')
plt.axis('equal')
plt.grid(True)

plt.subplot(5, 2, 3)
plt.plot(np.real(IQ_filtered), 'b', linewidth=1)
plt.plot(np.imag(IQ_filtered), 'r', linewidth=1)
plt.title('Отфильтрованный сигнал')
plt.grid(True)

plt.subplot(5, 2, 4)
plt.scatter(np.real(IQ_filtered), np.imag(IQ_filtered), s=10)
plt.title('Созвездие после фильтрации')
plt.axis('equal')
plt.grid(True)

if len(IQs) > 0 and len(ns) > 0:
    plt.subplot(5, 2, 5)
    plt.plot(np.real(IQs), 'b', linewidth=1)
    plt.plot(np.imag(IQs), 'r', linewidth=1)
    plt.title('Результат после синхронизации')
    plt.grid(True)
    
    plt.subplot(5, 2, 6)
    plt.scatter(np.real(IQs), np.imag(IQs), s=50)
    plt.title('Созвездие после синхронизации')
    plt.axis('equal')
    plt.grid(True)

plt.subplot(5, 2, 7)
if len(err) > 0:
    plt.plot(err, 'g', linewidth=1)
    plt.title('График ошибок')
    plt.grid(True)

plt.subplot(5, 2, 8)
if len(offset) > 0:
    plt.plot(offset, 'm', linewidth=1)
    plt.title('График смещений')
    plt.grid(True)

plt.tight_layout()

# plot_eye_diagram(IQs,1,100)

plt.show()