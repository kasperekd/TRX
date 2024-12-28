#include "SDRConfig.hpp"

SDRConfig::SDRConfig(SDRDeviceType type, size_t bufSize, double rate,
                     double freq, double g)
    : deviceType(type),
      bufferSize(bufSize),
      sampleRate(rate),
      frequency(freq),
      gain(g) {}
