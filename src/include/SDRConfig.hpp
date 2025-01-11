#ifndef SDRCONFIG_HPP
#define SDRCONFIG_HPP

#include <cstddef>
#include <string>

namespace SDRcfg {
enum SDRDeviceType { SoapySDR, UHD, Custom, Unknown };  // class ?

struct SDRConfig {
    SDRDeviceType deviceType;   // Тип устройства
    std::string name;           // Название устройства
    std::string deviceAddress;  // Адрес устройства
    double rxFrequency;         // Частота RX
    double rxSampleRate;        // Частота выборки RX
    double rxBandwidth;         // Полоса пропускания RX
    double txFrequency;         // Частота TX
    double txSampleRate;        // Частота выборки TX
    double txBandwidth;         // Полоса пропускания TX
    double gain;                // Усиление
    size_t bufferSize;          // Размер буфера
    size_t multiplier;          // Множитель для сэмплов

    SDRConfig(SDRDeviceType type, const std::string& name,
              const std::string& address, double rxFreq, double rxRate,
              double rxBW, double txFreq, double txRate, double txBW, double g,
              size_t bufSize, size_t mult);
    SDRConfig(const SDRConfig& other);
    SDRConfig();
};
}  // namespace SDRcfg
#endif
