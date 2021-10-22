cmake_minimum_required(VERSION 3.14.3)
project(asa_powersupplay)

set(CMAKE_CXX_STANDARD 14)
set(THREADS_PREFER_PTHREAD_FLAG ON)
set(GCC_COVERAGE_COMPILE_FLAGS "-D_GLIBCXX_USE_NANOSLEEP -pthread ")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${GCC_COVERAGE_COMPILE_FLAGS}" )
#find_package(Threads REQUIRED)
#option(MINGW_STDTHREADS_GENERATE_STDHEADERS "" ON)
add_executable(asa_powersupplay windows.cpp)

