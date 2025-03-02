import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

def generate_ofdm_signal(T, Nc, noise_amp=0.0, freq_shift=0.0):
    df = 1 / T
    num_samples = Nc * 100  
    ts = T / num_samples  
    t = ts * np.arange(0, num_samples)
    

    sc_matr = np.zeros((Nc, len(t)), dtype=complex)
    for k in range(Nc):
        sc_matr[k, :] = 1 / np.sqrt(T) * np.exp(1j * 2 * np.pi * k * df * t)
    

    np.random.seed(1) 
    sd = np.sign(np.random.rand(Nc) - 0.5) + 1j * np.sign(np.random.rand(Nc) - 0.5)
    
    xt = np.zeros(len(t), dtype=complex)
    for k in range(Nc):
        xt += sd[k] * sc_matr[k, :]
    
    xt *= np.exp(1j * 2 * np.pi * freq_shift * t)
    
    noise = noise_amp * (np.random.randn(len(t)) + 1j * np.random.randn(len(t)))
    xt_noisy = xt + noise
    
    spectrum = np.abs(np.fft.fftshift(np.fft.fft(xt_noisy))) / len(t)
    freq = np.fft.fftshift(np.fft.fftfreq(len(t), d=ts))
    
    return t, sc_matr, xt_noisy, spectrum, freq

fig, ax = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})
plt.subplots_adjust(left=0.25, bottom=0.4)

T_init = 1e-4
Nc_init = 16  
noise_amp_init = 0.1 
freq_shift_init = 0.0 

t, sc_matr, xt_noisy, spectrum, freq = generate_ofdm_signal(T_init, Nc_init, noise_amp=noise_amp_init, freq_shift=freq_shift_init)

lines = []
for k in range(Nc_init):
    line, = ax[0].plot(t, sc_matr[k, :].real, lw=1, alpha=0.7, label=f'Поднесущая {k}')
    lines.append(line)

ofdm_line, = ax[0].plot(t, xt_noisy.real, color='black', lw=2, label='OFDM-сигнал')

spectrum_line, = ax[1].plot(freq, spectrum, color='red', lw=2, label='Спектр')

ax[0].set_title("OFDM: Поднесущие и сигнал")
ax[0].set_xlabel("Время (с)")
ax[0].set_ylabel("Амплитуда")
ax[0].legend(loc='upper right', fontsize=8)
ax[0].grid()

ax[1].set_title("Спектр OFDM-сигнала")
ax[1].set_xlabel("Частота (Гц)")
ax[1].set_ylabel("Амплитуда")
ax[1].legend(loc='upper right', fontsize=8)
ax[1].grid()

ax_T = plt.axes([0.25, 0.3, 0.65, 0.03])
ax_Nc = plt.axes([0.25, 0.25, 0.65, 0.03])
ax_noise = plt.axes([0.25, 0.2, 0.65, 0.03])
ax_freq_shift = plt.axes([0.25, 0.15, 0.65, 0.03])

slider_T = Slider(ax_T, 'Длительность символа T (с)', valmin=1e-5, valmax=1e-3, valinit=T_init, valfmt="%1.2e")
slider_Nc = Slider(ax_Nc, 'Количество поднесущих Nc', valmin=1, valmax=1024, valinit=Nc_init, valstep=1)
slider_noise = Slider(ax_noise, 'Амплитуда шума', valmin=0.0, valmax=1000.0, valinit=noise_amp_init)
slider_freq_shift = Slider(ax_freq_shift, 'Частотный сдвиг (Гц)', valmin=-1000, valmax=1000, valinit=freq_shift_init)

def update(val):
    T = slider_T.val
    Nc = int(slider_Nc.val)
    noise_amp = slider_noise.val
    freq_shift = slider_freq_shift.val
    
    ax[0].clear()
    ax[1].clear()
    
    t, sc_matr, xt_noisy, spectrum, freq = generate_ofdm_signal(T, Nc, noise_amp=noise_amp, freq_shift=freq_shift)

    lines = []
    for k in range(Nc):
        line, = ax[0].plot(t, sc_matr[k, :].real, lw=1, alpha=0.7, label=f'Поднесущая {k}')
        lines.append(line)

    ofdm_line, = ax[0].plot(t, xt_noisy.real, color='black', lw=2, label='OFDM-сигнал')

    ax[0].set_title("OFDM: Поднесущие и сигнал")
    ax[0].set_xlabel("Время (с)")
    ax[0].set_ylabel("Амплитуда")
    ax[0].legend(loc='upper right', fontsize=8)
    ax[0].grid()

    spectrum_line, = ax[1].plot(freq, spectrum, color='red', lw=2, label='Спектр')

    ax[1].set_title("Спектр OFDM-сигнала")
    ax[1].set_xlabel("Частота (Гц)")
    ax[1].set_ylabel("Амплитуда")
    ax[1].legend(loc='upper right', fontsize=8)
    ax[1].grid()
    
    fig.canvas.draw_idle()

slider_T.on_changed(update)
slider_Nc.on_changed(update)
slider_noise.on_changed(update)
slider_freq_shift.on_changed(update)

plt.show()