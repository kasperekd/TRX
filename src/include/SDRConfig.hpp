#ifndef SDRCONFIG_HPP
#define SDRCONFIG_HPP

#include <cstddef>

enum SDRDeviceType { SoapySDR, UHD, Custom, Unknown };  // class ?

struct SDRConfig {
    SDRDeviceType deviceType;
    size_t bufferSize;
    double sampleRate;
    double frequency;
    double gain;

    SDRConfig(SDRDeviceType type, size_t bufSize, double rate, double freq,
              double g);
};

#endif
