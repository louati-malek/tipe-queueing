cmake_minimum_required(VERSION 3.15)
project(mmck_sim LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release)
endif()
if(MSVC)
  add_compile_options(/W4)
else()
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

add_library(mmck STATIC src/mmck.cpp)
target_include_directories(mmck PUBLIC include)

add_executable(mmck_sim src/main.cpp)
target_link_libraries(mmck_sim PRIVATE mmck)

enable_testing()
add_executable(test_mmck tests/test_mmck.cpp)
target_link_libraries(test_mmck PRIVATE mmck)
add_test(NAME simulator_vs_theory COMMAND test_mmck)
