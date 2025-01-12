#ifndef SDRCONFIG_HPP
#define SDRCONFIG_HPP

#include <cstddef>
#include <string>

namespace SDRcfg {

enum SDRDeviceType { SoapySDR, UHD, Custom, UnknownType };
enum GainMode { Manual, SlowAttack, FastAttack, UnknownGain };
enum DataSourceType { File, Network, UnknowSource };

struct SDRConfig {
    SDRDeviceType deviceType;   // Тип устройства
    std::string name;           // Название устройства
    std::string deviceAddress;  // Адрес устройства

    double rxFrequency;   // Частота RX
    double rxSampleRate;  // Частота выборки RX
    double rxBandwidth;   // Полоса пропускания RX

    double txFrequency;   // Частота TX
    double txSampleRate;  // Частота выборки TX
    double txBandwidth;   // Полоса пропускания TX

    double gain;        // Усиление
    GainMode gainMode;  // Режим AGC

    size_t bufferSize;  // Размер буфера
    size_t multiplier;  // Множитель для сэмплов

    DataSourceType dataSourceType;  // Тип источника данных
    std::string dataSourcePath;  // Путь к источнику данных
    size_t repeatCount;  // Количество повторений (0 = бесконечно)

    SDRConfig(SDRDeviceType type, const std::string& name,
              const std::string& address, double rxFreq, double rxRate,
              double rxBW, double txFreq, double txRate, double txBW, double g,
              GainMode mode, size_t bufSize, size_t mult,
              DataSourceType srcType, const std::string& srcPath,
              size_t repeat);

    SDRConfig(const SDRConfig& other);
    SDRConfig();
};

}  // namespace SDRcfg

#endif
