#include "SDRConfig.hpp"

SDRcfg::SDRConfig::SDRConfig()
    : deviceType(SDRDeviceType::UnknownType),
      name(""),
      deviceAddress(""),
      rxFrequency(0.0),
      rxSampleRate(0.0),
      rxBandwidth(0.0),
      txFrequency(0.0),
      txSampleRate(0.0),
      txBandwidth(0.0),
      gain(0.0),
      bufferSize(0),
      multiplier(1) {}

SDRcfg::SDRConfig::SDRConfig(SDRDeviceType type, const std::string& name,
                             const std::string& address, double rxFreq,
                             double rxRate, double rxBW, double txFreq,
                             double txRate, double txBW, double g,
                             GainMode mode, size_t bufSize, size_t mult,
                             DataSourceType srcType, const std::string& srcPath,
                             size_t repeat)
    : deviceType(type),
      name(name),
      deviceAddress(address),
      rxFrequency(rxFreq),
      rxSampleRate(rxRate),
      rxBandwidth(rxBW),
      txFrequency(txFreq),
      txSampleRate(txRate),
      txBandwidth(txBW),
      gain(g),
      gainMode(mode),
      bufferSize(bufSize),
      multiplier(mult),
      dataSourceType(srcType),
      dataSourcePath(srcPath),
      repeatCount(repeat) {}

SDRcfg::SDRConfig::SDRConfig(const SDRConfig& other)
    : deviceType(other.deviceType),
      name(other.name),
      deviceAddress(other.deviceAddress),
      rxFrequency(other.rxFrequency),
      rxSampleRate(other.rxSampleRate),
      rxBandwidth(other.rxBandwidth),
      txFrequency(other.txFrequency),
      txSampleRate(other.txSampleRate),
      txBandwidth(other.txBandwidth),
      gain(other.gain),
      bufferSize(other.bufferSize),
      multiplier(other.multiplier) {}