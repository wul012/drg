cmake_minimum_required(VERSION 3.31)
project(C)

set(CMAKE_CXX_STANDARD 20)

add_executable(C
        selectionSort.cpp
        quickSort.cpp
        mergeSort.cpp
        nQueens.cpp
        graph.cpp
        dijkstra.cpp
        kmp.cpp
        manacher.cpp
        morris.cpp
        coins_min.cpp
        test.cpp
)

add_subdirectory(luogu)
