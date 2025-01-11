#include "SystemConfig.hpp"

#include <stdexcept>

SystemConfig::SystemConfig() : logLevel("INFO"), logFile(""), maxThreads(1) {}

void SystemConfig::loadFromNode(const fkyaml::node& systemNode) {
    if (!systemNode["log_level"].is_null()) {
        logLevel = systemNode["log_level"].get_value<std::string>();
    } else {
        logLevel = "INFO";
    }

    if (!systemNode["log_file"].is_null()) {
        logFile = systemNode["log_file"].get_value<std::string>();
    } else {
        logFile = "";
    }

    if (!systemNode["max_threads"].is_null()) {
        maxThreads = systemNode["max_threads"].get_value<size_t>();
    } else {
        maxThreads = 1;
    }
}

void SystemConfig::validate() const {
    if (logLevel != "DEBUG" && logLevel != "INFO" && logLevel != "WARN" &&
        logLevel != "ERROR") {
        throw std::invalid_argument("Invalid log level: " + logLevel);
    }
    if (maxThreads == 0) {
        throw std::invalid_argument("Max threads must be greater than 0");
    }
}
