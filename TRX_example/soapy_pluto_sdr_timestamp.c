#include <SoapySDR/Device.h>
#include <SoapySDR/Formats.h>
#include <stdint.h>
#include <stdio.h>   // printf
#include <stdlib.h>  // free
#include <string.h>

bool read_ofdm_signal(const char *filename, float **tx_i, float **tx_q,
                      size_t *num_samples) {
    FILE *file = fopen(filename, "rb");
    if (file == NULL) {
        perror("Ошибка открытия файла");
        return false;
    }

    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);

    if (file_size % (2 * sizeof(float)) != 0) {
        fprintf(stderr,
                "Ошибка: размер файла не кратен размеру комплексного числа\n");
        fclose(file);
        return false;
    }

    *num_samples = file_size / (2 * sizeof(float));
    float *combined = (float *)malloc(file_size);
    if (combined == NULL) {
        fprintf(stderr, "Ошибка выделения памяти\n");
        fclose(file);
        return false;
    }

    size_t read_count = fread(combined, sizeof(float), *num_samples * 2, file);
    if (read_count != *num_samples * 2) {
        fprintf(stderr, "Ошибка чтения данных из файла\n");
        free(combined);
        fclose(file);
        return false;
    }
    fclose(file);

    *tx_i = (float *)malloc(*num_samples * sizeof(float));
    *tx_q = (float *)malloc(*num_samples * sizeof(float));
    if (*tx_i == NULL || *tx_q == NULL) {
        fprintf(stderr, "Ошибка выделения памяти\n");
        free(combined);
        return false;
    }

    for (size_t i = 0; i < *num_samples; i++) {
        (*tx_i)[i] = combined[2 * i];      // Вещественная часть
        (*tx_q)[i] = combined[2 * i + 1];  // Мнимая часть
        // printf("%f, %f\n", (*tx_i)[i], (*tx_q)[i]);
    }

    free(combined);
    return true;
}

int main(void) {
    SoapySDRKwargs args = {};
    SoapySDRKwargs_set(&args, "driver", "plutosdr");
    SoapySDRKwargs_set(&args, "uri", "usb:");
    SoapySDRKwargs_set(&args, "direct", "1");
    SoapySDRKwargs_set(&args, "timestamp_every", "1920");
    SoapySDRKwargs_set(&args, "loopback", "0");

    SoapySDRDevice *sdr = SoapySDRDevice_make(&args);
    SoapySDRKwargs_clear(&args);
    if (sdr == NULL) {
        printf("SoapySDRDevice_make fail: %s\n", SoapySDRDevice_lastError());
        return EXIT_FAILURE;
    }

    if (SoapySDRDevice_setSampleRate(sdr, SOAPY_SDR_RX, 0, 1e6) != 0) {
        printf("setSampleRate rx fail: %s\n", SoapySDRDevice_lastError());
    }
    if (SoapySDRDevice_setFrequency(sdr, SOAPY_SDR_RX, 0, 800e6, NULL) != 0) {
        printf("setFrequency rx fail: %s\n", SoapySDRDevice_lastError());
    }
    if (SoapySDRDevice_setSampleRate(sdr, SOAPY_SDR_TX, 0, 1e6) != 0) {
        printf("setSampleRate tx fail: %s\n", SoapySDRDevice_lastError());
    }
    if (SoapySDRDevice_setFrequency(sdr, SOAPY_SDR_TX, 0, 800e6, NULL) != 0) {
        printf("setFrequency tx fail: %s\n", SoapySDRDevice_lastError());
    }

    double bandwidth = 10e6;
    if (SoapySDRDevice_setBandwidth(sdr, SOAPY_SDR_RX, 0, bandwidth) != 0) {
        printf("setBandwidth rx fail: %s\n", SoapySDRDevice_lastError());
    } else {
        printf("RX Bandwidth set to %.2f Hz\n", bandwidth);
    }

    if (SoapySDRDevice_setBandwidth(sdr, SOAPY_SDR_TX, 0, bandwidth) != 0) {
        printf("setBandwidth tx fail: %s\n", SoapySDRDevice_lastError());
    } else {
        printf("TX Bandwidth set to %.2f Hz\n", bandwidth);
    }

    double actualBandwidth = SoapySDRDevice_getBandwidth(sdr, SOAPY_SDR_RX, 0);
    printf("Actual RX Bandwidth: %.2f Hz\n", actualBandwidth);

    printf("SoapySDRDevice_getFrequency tx: %lf\n",
           SoapySDRDevice_getFrequency(sdr, SOAPY_SDR_TX, 0));

    size_t channels[] = {0};
    size_t channel_count = sizeof(channels) / sizeof(channels[0]);
    SoapySDRStream *rxStream = SoapySDRDevice_setupStream(
        sdr, SOAPY_SDR_RX, SOAPY_SDR_CF32, channels, channel_count, NULL);
    if (rxStream == NULL) {
        printf("setupStream rx fail: %s\n", SoapySDRDevice_lastError());
        SoapySDRDevice_unmake(sdr);
        return EXIT_FAILURE;
    }

    SoapySDRStream *txStream = SoapySDRDevice_setupStream(
        sdr, SOAPY_SDR_TX, SOAPY_SDR_CF32, channels, channel_count, NULL);
    if (txStream == NULL) {
        printf("setupStream tx fail: %s\n", SoapySDRDevice_lastError());
        SoapySDRDevice_unmake(sdr);
        return EXIT_FAILURE;
    }

    if (SoapySDRDevice_setGain(sdr, SOAPY_SDR_RX, channels, 10.0) != 0) {
        printf("setGain rx fail: %s\n", SoapySDRDevice_lastError());
    }
    if (SoapySDRDevice_setGain(sdr, SOAPY_SDR_TX, channels, -50.0) != 0) {
        printf("setGain rx fail: %s\n", SoapySDRDevice_lastError());
    }

    size_t rx_mtu = SoapySDRDevice_getStreamMTU(sdr, rxStream);
    size_t tx_mtu = SoapySDRDevice_getStreamMTU(sdr, txStream);
    printf("MTU - TX: %lu, RX: %lu\n", tx_mtu, rx_mtu);

    float tx_buff[2 * tx_mtu];
    float rx_buffer[2 * rx_mtu];

    // из файла
    float *tx_i = NULL;
    float *tx_q = NULL;
    size_t num_samples = 0;
    if (!read_ofdm_signal("./ofdm_signal.bin", &tx_i, &tx_q, &num_samples)) {
        printf("Failed to read signal!\n");
        return EXIT_FAILURE;
    }

    // Заполнение буфера TX
    for (size_t i = 0; i < num_samples && i < tx_mtu; i++) {
        tx_buff[2 * i] = tx_i[i];      // Вещественная часть
        tx_buff[2 * i + 1] = tx_q[i];  // Мнимая часть
    }

    SoapySDRDevice_activateStream(sdr, rxStream, 0, 0, 0);
    SoapySDRDevice_activateStream(sdr, txStream, 0, 0, 0);

    // Основной цикл
    const long timeoutUs = 400000;  // Таймаут в микросекундах
    size_t iteration_count = 100;
    long long last_time = 0;

    size_t total_samples = iteration_count * rx_mtu * 2;
    float *big_buffer = (float *)malloc(total_samples * sizeof(float));
    if (!big_buffer) {
        printf("Memory allocation failed!\n");
        return EXIT_FAILURE;
    }

    size_t big_buffer_index = 0;

    for (size_t buffers_read = 0; buffers_read < iteration_count;
         buffers_read++) {
        // Прием данных
        void *rx_buffs[] = {rx_buffer};
        int flags;
        long long timeNs;
        int sr = SoapySDRDevice_readStream(sdr, rxStream, rx_buffs, rx_mtu,
                                           &flags, &timeNs, timeoutUs);
        if (sr < 0) {
            continue;
        }

        memcpy(big_buffer + big_buffer_index, rx_buffer,
               2 * sr * sizeof(float));
        big_buffer_index += 2 * sr;

        // Отправка данных
        long long tx_time =
            timeNs + (4 * 1000 * 1000);  // Время отправки через 4 мс
        void *tx_buffs[] = {tx_buff};
        if ((buffers_read % 2 == 0)) {
            flags = SOAPY_SDR_HAS_TIME;
            int st = SoapySDRDevice_writeStream(
                sdr, txStream, (const void *const *)tx_buffs, tx_mtu, &flags,
                tx_time, timeoutUs);
            if ((size_t)st != tx_mtu) {
                printf("TX Failed: %i\n", st);
            }
        }

        // Вывод информации
        printf(
            "Buffer: %lu - Samples: %i, Flags: %i, Time: %lli, TimeDiff: "
            "%lli\n",
            buffers_read, sr, flags, timeNs, timeNs - last_time);
        last_time = timeNs;
    }

    // for (size_t i = 0; i < big_buffer_index; i++) {
    //     printf("%f, ", big_buffer[i]);
    //     // big_buffer[i] /= (float)1e6;
    //     printf("%f \n", big_buffer[i]);
    // }

    FILE *file = fopen("rxdata.pcm", "wb");
    if (file) {
        fwrite(big_buffer, sizeof(float), big_buffer_index, file);
        fclose(file);
    } else {
        printf("Failed to open file for writing!\n");
    }

    free(big_buffer);

    SoapySDRDevice_deactivateStream(sdr, rxStream, 0, 0);
    SoapySDRDevice_deactivateStream(sdr, txStream, 0, 0);
    SoapySDRDevice_closeStream(sdr, rxStream);
    SoapySDRDevice_closeStream(sdr, txStream);
    SoapySDRDevice_unmake(sdr);

    free(tx_i);
    free(tx_q);
    return EXIT_SUCCESS;
}