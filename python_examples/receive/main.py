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

    plt.show()

filename = '../../data/txdata1.pcm'
data = np.fromfile(filename, dtype=np.int16).astype(np.float32) 
data = np.fromfile(filename, dtype=np.int16).astype(np.float32)
I_ = data[::2]
Q_ = data[1::2] 

threshold = 9 

# mask = (np.abs(I_) > threshold) & (np.abs(Q_) > threshold)
# I = I_[mask]
# Q = Q_[mask]
I = I_
Q = Q_

# I /= np.max(np.abs(I) + 1e-6) 
# Q /= np.max(np.abs(Q) + 1e-6)

nsps = 10
h = np.ones(nsps) / nsps  
# h = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
filtered_I = np.convolve(I, h, mode='full')
filtered_Q = np.convolve(Q, h, mode='full')
# filtered_I = I
# filtered_Q = Q

BnTs = 0.01
Nsps = nsps
Kp = 0.002
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
    # err = (
    #     ((filtered_I[i + Nsps + tau] - filtered_I[i + tau]) * filtered_I[i + (Nsps // 2) + tau]) +
    #     ((filtered_Q[i + Nsps + tau] - filtered_Q[i + tau]) * filtered_Q[i + (Nsps // 2) + tau])
    # )

    p1 = err * K1
    p2 = p2 + p1 + err * K2

    p2 = np.clip(p2, -1.0, 1.0)

    tau = int(round(p2 * Nsps))

    if 0 <= idx_mid < len(filtered_I):
        sync_I.append(filtered_I[idx_mid])
        sync_Q.append(filtered_Q[idx_mid])
    
    errors.append(err)
    taus.append(tau)

plt.figure(figsize=(15, 10))

plt.subplot(221)
plt.scatter(sync_I, sync_Q, alpha=0.5, color='blue')
plt.title('Синхронизированное QPSK созвездие')
plt.grid(True)
# plt.xlim(-1.1, 1.1)
# plt.ylim(-1.1, 1.1)

plt.subplot(222)
plt.plot(errors, color='red')
plt.title('Ошибка синхронизации (TED)')
plt.grid(True)

# plt.subplot(222)
# plt.scatter(I, Q, alpha=0.5, color='red')
# plt.title('Созвездие до обработки')
# plt.grid(True)

plt.subplot(223)
plt.plot(taus, color='green')
plt.title('Смещение tau')
plt.grid(True)

plt.subplot(224)
plt.scatter(filtered_I, filtered_Q, alpha=0.5, color='purple')
plt.title('Созвездие до обработки (фильтр)')
plt.grid(True)
# plt.xlim(-1.1, 1.1)
# plt.ylim(-1.1, 1.1)

plt.tight_layout()
plt.show()


combined_sync = np.concatenate((sync_I, sync_Q))

# plot_eye_diagram(combined_sync, 1, 10000)

print(f"Обработано символов: {len(sync_I)}")
print(f"Среднее значение ошибки: {np.mean(errors):.4f}")
print(f"Максимальное смещение tau: {max(taus):.2f}")
print(f"Среднее значение tau: {np.mean(taus):.4f}")