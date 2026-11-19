# Host build of the portable core and its tests. The Teensy build (PlatformIO) compiles the same core/
# sources; nothing in core/ may depend on Arduino, the heap after start-up, exceptions or RTTI.
cmake_minimum_required(VERSION 3.16)
project(tuner_fw CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif()

add_library(tuner_core STATIC
  core/src/as5048.cpp
  core/src/bridge.cpp
  core/src/curve.cpp
  core/src/faults.cpp
  core/src/freq.cpp
  core/src/fsm.cpp
  core/src/motion.cpp
  core/src/seed.cpp
  core/src/sense.cpp
  core/src/tnet.cpp)
target_include_directories(tuner_core PUBLIC core/include)
target_compile_options(tuner_core PRIVATE -Wall -Wextra -Wpedantic -Wshadow -Werror
  -fno-exceptions -fno-rtti)

enable_testing()
foreach(name tnet bridge freq_faults fsm hw)
  add_executable(test_${name} test/test_${name}.cpp test/test_main.cpp)
  target_link_libraries(test_${name} PRIVATE tuner_core)
  target_compile_options(test_${name} PRIVATE -Wall -Wextra)
  add_test(NAME ${name} COMMAND test_${name})
endforeach()
