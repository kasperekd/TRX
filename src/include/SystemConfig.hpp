#ifndef SYSTEMCONFIG_HPP
#define SYSTEMCONFIG_HPP

#include <string>

#include "fkYAML/node.hpp"

struct SystemConfig {
    std::string logLevel;
    std::string logFile;
    size_t maxThreads;

    SystemConfig();

    void loadFromNode(const fkyaml::node& systemNode);
    void validate() const;
};

#endif  // SYSTEMCONFIG_HPP
