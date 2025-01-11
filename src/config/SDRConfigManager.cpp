#include "SDRConfigManager.hpp"

#include <stdexcept>

#include "SDRDriver.hpp"

void SDRConfigManager::loadFromNode(const fkyaml::node& sdrNode) {
    for (const auto& node : sdrNode) {
        SDRcfg::SDRConfig sdr;

        if (!node["name"].is_null()) {
            sdr.name = node["name"].get_value<std::string>();
        } else {
            sdr.name = "Unknown_SDR";  // Значение по умолчанию
        }

        if (!node["device_address"].is_null()) {
            sdr.deviceAddress = node["device_address"].get_value<std::string>();
        } else {
            sdr.deviceAddress = "";  // Значение по умолчанию
        }

        if (!node["buffer_size"].is_null()) {
            sdr.bufferSize = node["buffer_size"].get_value<size_t>();
        } else {
            sdr.bufferSize = 0;  // Значение по умолчанию
        }

        if (!node["multiplier"].is_null()) {
            sdr.multiplier = node["multiplier"].get_value<size_t>();
        } else {
            sdr.multiplier = 1;  // Значение по умолчанию
        }

        // Обработка типа устройства
        if (!node["device_type"].is_null()) {
            auto type = node["device_type"].get_value<std::string>();
            if (type == "SoapySDR") {
                sdr.deviceType = SDRcfg::SDRDeviceType::SoapySDR;
            } else if (type == "UHD") {
                sdr.deviceType = SDRcfg::SDRDeviceType::UHD;
            } else {
                sdr.deviceType = SDRcfg::SDRDeviceType::Unknown;
            }
        } else {
            sdr.deviceType = SDRcfg::SDRDeviceType::Unknown;
        }

        // Настройки приемника
        if (!node["settings"].is_null()) {
            auto settingsNode = node["settings"];

            if (!settingsNode["gain"].is_null()) {
                sdr.gain = settingsNode["gain"].get_value<double>();
            }

            if (!settingsNode["rx"].is_null()) {
                auto rxNode = settingsNode["rx"];
                if (!rxNode["frequency"].is_null()) {
                    sdr.rxFrequency = rxNode["frequency"].get_value<double>();
                }
                if (!rxNode["sample_rate"].is_null()) {
                    sdr.rxSampleRate =
                        rxNode["sample_rate"].get_value<double>();
                }
                if (!rxNode["bandwidth"].is_null()) {
                    sdr.rxBandwidth = rxNode["bandwidth"].get_value<double>();
                }
            }

            if (!settingsNode["tx"].is_null()) {
                auto txNode = settingsNode["tx"];
                if (!txNode["frequency"].is_null()) {
                    sdr.txFrequency = txNode["frequency"].get_value<double>();
                }
                if (!txNode["sample_rate"].is_null()) {
                    sdr.txSampleRate =
                        txNode["sample_rate"].get_value<double>();
                }
                if (!txNode["bandwidth"].is_null()) {
                    sdr.txBandwidth = txNode["bandwidth"].get_value<double>();
                }
            }
        }

        sdrConfigs.push_back(sdr);
    }
}

const std::vector<SDRcfg::SDRConfig>& SDRConfigManager::getConfigs() const {
    return sdrConfigs;
}
