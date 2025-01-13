cmake_minimum_required(VERSION 3.20)

project(TRXProject)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Werror -Wpedantic -Wconversion -std=c++20")

set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -fsanitize=undefined -fsanitize=address")
set(CMAKE_CXX_FLAGS_DEBUG_THREAD "${CMAKE_CXX_FLAGS_DEBUG_THREAD} -g -fsanitize=thread")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3") 

include_directories(
    ${CMAKE_SOURCE_DIR}/src/include
    ${CMAKE_SOURCE_DIR}/src/SDR/modules/include
)

### THRID PARTY ###
include_directories(
    ${CMAKE_SOURCE_DIR}/third_party
)
### THRID PARTY ###

set(CONFIG_SOURCES 
    src/config/Config.cpp
    src/config/SDRConfigManager.cpp
    src/config/SystemConfig.cpp
)

set(SDR_SOURCES
    src/SDR/SDRConfig.cpp
    src/SDR/SDRDriver.cpp
    # Soapy
    src/SDR/modules/SoapySDR/SoapySDRDriver.cpp
    src/SDR/modules/SoapySDR/SoapySDRUtils.cpp
    # ...
)

set(UTILS_SOURCES
    src/utils/Logger.cpp
    src/utils/Utils.cpp
)

set(THREAD_MANAGER_SOURCES
    src/ThreadManager/ThreadManager.cpp
)

add_executable(TRX
    src/main.cpp
)

### THRID PARTY ###
add_library(fkYAML INTERFACE)
target_include_directories(fkYAML INTERFACE ${CMAKE_SOURCE_DIR}/third_party/fkYAML)
target_compile_options(fkYAML INTERFACE -Wno-shadow)
### THRID PARTY ###

add_library(THREAD_MANAGER ${THREAD_MANAGER_SOURCES})
add_library(CONFIG ${CONFIG_SOURCES})
add_library(SDR ${SDR_SOURCES})
add_library(utils ${UTILS_SOURCES})

target_link_libraries(TRX PRIVATE CONFIG utils fkYAML SDR THREAD_MANAGER atomic)
target_include_directories(TRX PRIVATE ${CMAKE_SOURCE_DIR}/src/include)


# Пока не доверять компиляции с флагами:
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(TRX PRIVATE -fsanitize=undefined -fsanitize=address)
    target_compile_options(CONFIG PRIVATE -fsanitize=undefined -fsanitize=address)
    target_compile_options(SDR PRIVATE -fsanitize=undefined -fsanitize=address)
    target_compile_options(utils PRIVATE -fsanitize=undefined -fsanitize=address)
elseif(CMAKE_BUILD_TYPE STREQUAL "DebugThread")
    target_compile_options(TRX PRIVATE -fsanitize=thread)
    target_compile_options(CONFIG PRIVATE -fsanitize=thread)
    target_compile_options(SDR PRIVATE -fsanitize=thread)
    target_compile_options(utils PRIVATE -fsanitize=thread)
endif()

# add_subdirectory(src/tests)
