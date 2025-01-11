#include "Config.hpp"

#include <fstream>
#include <stdexcept>

void Config::loadFromFile(const std::string& filepath) {
    std::ifstream ifs(filepath);
    if (!ifs.is_open()) {
        throw std::runtime_error("Failed to open config file: " + filepath);
    }

    fkyaml::node root = fkyaml::node::deserialize(ifs);

    // Парсинг системной конфигурации
    if (!root["system"].is_null() && !root["system"].empty()) {
        systemConfig.loadFromNode(root["system"]);
        systemConfig.validate();
    } else {
        throw std::runtime_error(
            "System configuration is missing in YAML file.");
    }

    // Парсинг конфигурации SDR
    if (!root["sdr"].is_null() && !root["sdr"].empty()) {
        sdrConfigManager.loadFromNode(root["sdr"]);
    } else {
        throw std::runtime_error("SDR configuration is missing in YAML file.");
    }
}

const SystemConfig& Config::getSystemConfig() const { return systemConfig; }

const std::vector<SDRcfg::SDRConfig>& Config::getSDRConfigs() const {
    return sdrConfigManager.getConfigs();
}
