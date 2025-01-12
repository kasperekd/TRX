#include "SDRConfigManager.hpp"

#include <regex>
#include <stdexcept>
#include <string>

#include "SDRDriver.hpp"

static double parseValueWithMultiplier(const std::string& value) {
    static const std::regex regex(R"((\d+(\.\d+)?)\s*([kMG]?Hz|[kM]?SPS))");
    std::smatch match;

    if (std::regex_match(value, match, regex)) {
        double number = std::stod(match[1]);
        std::string unit = match[3];

        if (unit == "Hz" || unit.empty()) {
            return number;
        } else if (unit == "kHz" || unit == "k") {
            return number * 1e3;
        } else if (unit == "MHz" || unit == "M") {
            return number * 1e6;
        } else if (unit == "GHz" || unit == "G") {
            return number * 1e9;
        } else if (unit == "SPS") {
            return number;
        } else if (unit == "KSPS" || unit == "kSPS") {
            return number * 1e3;
        } else if (unit == "MSPS" || unit == "MS") {
            return number * 1e6;
        }

        throw std::invalid_argument("Unsupported unit: " + unit);
    }

    throw std::invalid_argument("Invalid value format: " + value);
}

static SDRcfg::GainMode parseGainMode(const std::string& mode) {
    if (mode == "manual") {
        return SDRcfg::GainMode::Manual;
    } else if (mode == "slow_attack") {
        return SDRcfg::GainMode::SlowAttack;
    } else if (mode == "fast_attack") {
        return SDRcfg::GainMode::FastAttack;
    }
    return SDRcfg::GainMode::UnknownGain;
}

static SDRcfg::DataSourceType parseDataSourceType(const std::string& type) {
    if (type == "file") {
        return SDRcfg::DataSourceType::File;
    } else if (type == "network") {
        return SDRcfg::DataSourceType::Network;
    }
    return SDRcfg::DataSourceType::UnknowSource;
}

void SDRConfigManager::loadFromNode(const fkyaml::node& sdrNode) {
    for (const auto& node : sdrNode) {
        SDRcfg::SDRConfig sdr;

        sdr.name = node["name"].is_null()
                       ? "Unknown_SDR"
                       : node["name"].get_value<std::string>();
        sdr.deviceAddress =
            node["device_address"].is_null()
                ? ""
                : node["device_address"].get_value<std::string>();
        sdr.bufferSize = node["buffer_size"].is_null()
                             ? 0
                             : node["buffer_size"].get_value<size_t>();
        sdr.multiplier = node["multiplier"].is_null()
                             ? 1
                             : node["multiplier"].get_value<size_t>();

        // Обработка типа устройства
        auto type = node["device_type"].is_null()
                        ? "UnknowSource"
                        : node["device_type"].get_value<std::string>();
        if (type == "SoapySDR") {
            sdr.deviceType = SDRcfg::SDRDeviceType::SoapySDR;
        } else if (type == "UHD") {
            sdr.deviceType = SDRcfg::SDRDeviceType::UHD;
        } else if (type == "Custom") {
            sdr.deviceType = SDRcfg::SDRDeviceType::Custom;
        } else {
            sdr.deviceType = SDRcfg::SDRDeviceType::UnknownType;
        }

        // Настройки усиления
        if (!node["settings"].is_null()) {
            auto settingsNode = node["settings"];

            if (!settingsNode["gain"].is_null()) {
                sdr.gain = settingsNode["gain"].get_value<double>();
            }
            if (!settingsNode["gain_mode"].is_null()) {
                sdr.gainMode = parseGainMode(
                    settingsNode["gain_mode"].get_value<std::string>());
            }

            if (!settingsNode["rx"].is_null()) {
                auto rxNode = settingsNode["rx"];
                if (!rxNode["frequency"].is_null()) {
                    sdr.rxFrequency = parseValueWithMultiplier(
                        rxNode["frequency"].get_value<std::string>());
                }
                if (!rxNode["sample_rate"].is_null()) {
                    sdr.rxSampleRate = parseValueWithMultiplier(
                        rxNode["sample_rate"].get_value<std::string>());
                }
                if (!rxNode["bandwidth"].is_null()) {
                    sdr.rxBandwidth = parseValueWithMultiplier(
                        rxNode["bandwidth"].get_value<std::string>());
                }
            }

            if (!settingsNode["tx"].is_null()) {
                auto txNode = settingsNode["tx"];
                if (!txNode["frequency"].is_null()) {
                    sdr.txFrequency = parseValueWithMultiplier(
                        txNode["frequency"].get_value<std::string>());
                }
                if (!txNode["sample_rate"].is_null()) {
                    sdr.txSampleRate = parseValueWithMultiplier(
                        txNode["sample_rate"].get_value<std::string>());
                }
                if (!txNode["bandwidth"].is_null()) {
                    sdr.txBandwidth = parseValueWithMultiplier(
                        txNode["bandwidth"].get_value<std::string>());
                }
            }
        }

        // Источник данных
        if (!node["data_source"].is_null()) {
            auto dataSourceNode = node["data_source"];

            if (!dataSourceNode["type"].is_null()) {
                sdr.dataSourceType = parseDataSourceType(
                    dataSourceNode["type"].get_value<std::string>());
            }
            if (!dataSourceNode["file_path"].is_null()) {
                sdr.dataSourcePath =
                    dataSourceNode["file_path"].get_value<std::string>();
            }
            if (!dataSourceNode["repeat_count"].is_null()) {
                if (dataSourceNode["repeat_count"].is_string()) {
                    std::string repeatCountValue =
                        dataSourceNode["repeat_count"].get_value<std::string>();
                    if (repeatCountValue == "inf") {
                        sdr.repeatCount =
                            static_cast<size_t>(-1);  // Бесконечно
                    } else {
                        throw std::invalid_argument(
                            "Invalid string value for repeat_count: " +
                            repeatCountValue);
                    }
                } else if (dataSourceNode["repeat_count"].is_integer()) {
                    size_t repeatCount =
                        dataSourceNode["repeat_count"].get_value<size_t>();
                    sdr.repeatCount = (repeatCount == 0)
                                          ? static_cast<size_t>(-1)
                                          : repeatCount;
                } else {
                    throw std::invalid_argument(
                        "repeat_count must be a number or 'inf'");
                }
            }
        }

        sdrConfigs.push_back(sdr);
    }
}

const std::vector<SDRcfg::SDRConfig>& SDRConfigManager::getConfigs() const {
    return sdrConfigs;
}
