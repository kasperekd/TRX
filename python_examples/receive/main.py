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
    # plt.show()

filename = '../../data/qpsk_signal.bin'
# filename = '../../data/txdata1.pcm'
data = np.fromfile(filename, dtype=np.int16).astype(np.float32)

start_sample = 440 * 2
end_sample = 1330 * 2
# start_sample = 23276 * 2
# end_sample = 23730 * 2
selected_data = data[start_sample:end_sample]

# I_ = data[::2]
# Q_ = data[1::2]
I_ = selected_data[::2]
Q_ = selected_data[1::2]

plt.figure(figsize=(15, 10))

plt.subplot(321)
plt.plot(I_, label='I', alpha=0.7)
plt.plot(Q_, label='Q', alpha=0.7)
plt.title('Исходные данные I и Q')
plt.legend()
plt.grid(True)

plt.subplot(322)
plt.scatter(I_, Q_, alpha=0.5, color='blue')
plt.title('Созвездие до обработки')
plt.grid(True)


I = I_ / np.max(np.abs(I_) + 1e-6) 
Q = Q_ / np.max(np.abs(Q_) + 1e-6) 
# I = I_ 
# Q = Q_ 

nsps = 10
h = np.ones(nsps) / nsps  
filtered_I = np.convolve(I, h, mode='full')
filtered_Q = np.convolve(Q, h, mode='full')

plt.subplot(323)
plt.plot(filtered_I, label='Filtered I', alpha=0.7)
plt.plot(filtered_Q, label='Filtered Q', alpha=0.7)
plt.title('Отфильтрованные данные I и Q')
plt.legend()
plt.grid(True)

plt.subplot(324)
plt.scatter(filtered_I, filtered_Q, alpha=0.5, color='purple')
plt.title('Созвездие после фильтрации')
plt.grid(True)

BnTs = 0.01
Nsps = nsps
Kp = 2.7
zeta = np.sqrt(2) / 2
theta = (BnTs / Nsps) / (zeta + 0.25/zeta)
denominator = (1 + 2*zeta*theta + theta**2) * Kp
K1 = -4 * zeta * theta / denominator
K2 = -4 * theta**2 / denominator

p1 = 0.0
p2 = 0.0
tau = 0 
errors = []
taus = []
sync_I = []
sync_Q = []

for i in range(0, len(filtered_I) - Nsps, Nsps):
    current_tau = tau
    idx_start = i + current_tau
    idx_end = idx_start + Nsps
    idx_mid = idx_start + Nsps//2
    
    if idx_end >= len(filtered_I) or idx_start < 0:
        break

    I_end = filtered_I[idx_end]
    I_start = filtered_I[idx_start]
    I_mid = filtered_I[idx_mid]
    
    Q_end = filtered_Q[idx_end]
    Q_start = filtered_Q[idx_start]
    Q_mid = filtered_Q[idx_mid]
    
    err = (I_end - I_start) * I_mid + (Q_end - Q_start) * Q_mid
    p1 = err * K1
    p2 = p2 + p1 + err * K2
    p2 = np.clip(p2, -1.0, 1.0)
    tau = int(round(p2 * Nsps))
    
    # if 0 <= idx_mid < len(filtered_I):
    sync_I.append(filtered_I[tau + i])
    sync_Q.append(filtered_Q[tau + i])
    
    errors.append(err)
    taus.append(tau)

plt.subplot(325)
plt.plot(errors, color='red', label='Errors')
plt.title('Ошибки синхронизации (TED)')
plt.legend()
plt.grid(True)

plt.subplot(326)
plt.scatter(sync_I, sync_Q, alpha=0.5, color='green')
plt.title('Синхронизированное QPSK созвездие')
plt.grid(True)

plt.figure(figsize=(10, 5))
plt.plot(taus, color='blue', label='Tau')
plt.title('Смещение tau')
plt.legend()
plt.grid(True)

combined_sync = np.concatenate((sync_I, sync_Q))
# plt.figure(figsize=(12, 6))
plot_eye_diagram(combined_sync, 1, len(sync_I))

print(f"Обработано символов: {len(sync_I)}")
print(f"Среднее значение ошибки: {np.mean(errors):.4f}")
print(f"Максимальное смещение tau: {max(taus):.2f}")
print(f"Среднее значение tau: {np.mean(taus):.4f}")

plt.tight_layout()
plt.show()