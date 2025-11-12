/*
 * =====================================================================================
 *
 *       Filename:  main.cpp
 *
 *    Description:  这是一个用于测试选择排序算法的程序。
 *                  它会生成大量随机数组，然后分别用我们自己实现的
 *                  selectionSort 和标准库的 std::sort 进行排序，
 *                  最后比对两个排序结果是否一致，以此来验证我们算法的正确性。
 *
 * =====================================================================================
 */

#include <iostream>
#include <vector>
#include <algorithm> // 包含了 std::sort
#include <ctime>     // 包含了 time()，用于生成随机数种子
#include <cstdlib>   // 包含了 rand() 和 srand()
#include "mergeSort.h"

#ifdef _WIN32
#include <windows.h>
#endif

/*
 * =====================================================================================
 * 关于为什么不使用 "using namespace std;"
 * =====================================================================================
 *
 * 在这个项目中，我们所有的标准库功能都带有 "std::" 前缀，例如 std::cout, std::vector。
 * 我们没有在文件开头写 "using namespace std;"，这是一种推荐的编程习惯，原因如下：
 *
 * 1. 避免命名冲突 (Name Ambiguity):
 *    `std` 命名空间包含了大量常见的名称（如 sort, find, count, string, list 等）。
 *    如果你自己的代码中也定义了同名函数或变量，或者引入了另一个也定义了同名函数的
 *    第三方库，就会导致命名冲突，编译器不知道你到底想用哪一个，从而产生编译错误。
 *    例如，如果你自己实现了一个 sort 函数，`sort(arr)` 的调用就会有歧义。
 *
 * 2. 提高代码清晰度和可读性 (Clarity and Readability):
 *    当代码中明确写作 std::sort 时，任何阅读代码的人都能立刻明白这里调用的是 C++
 *    标准库的排序函数，而不是某个自定义函数。这种明确性对于代码的长期维护至关重要。
 *
 * 3. 避免污染头文件 (Header File Pollution):
 *    在头文件(.h)中使用 "using namespace std;" 是极其危险的。因为任何包含了这个
 *    头文件的源文件，都会被迫引入整个 `std` 命名空间，极大地增加了在整个项目中
 *    出现命名冲突的风险。
 *
 * 总结：坚持使用 `std::` 前缀是一种更安全、更专业、更易于维护的编程习惯。
 */


// 函数：打印一个整型向量的所有元素
void printVector(const std::vector<int>& arr) {
    for (int num : arr) {
        std::cout << num << " ";
    }
    std::cout << std::endl;
}

// 对照组函数：使用 C++ 标准库提供的 std::sort 进行排序
// 它的功能是绝对正确的，我们可以用它来检验我们自己写的排序算法是否正确。
void comparator(std::vector<int>& arr) {
    std::sort(arr.begin(), arr.end());
}

// 函数：生成一个随机长度、随机元素的整型向量
// @param maxSize 向量的最大可能长度
// @param maxValue 向量中元素的最大可能值
std::vector<int> generateRandomVector(int maxSize, int maxValue) {
    // 随机生成数组长度，范围在 [0, maxSize]
    int size = rand() % (maxSize + 1);
    std::vector<int> arr(size);
    for (int i = 0; i < size; i++) {
        // 随机生成元素值，范围大致在 [-maxValue, maxValue]
        arr[i] = rand() % (maxValue + 1) - rand() % (maxValue);
    }
    return arr;
}

// 函数：比较两个向量是否完全相等（长度和所有对应元素都相等）
bool areVectorsEqual(const std::vector<int>& arr1, const std::vector<int>& arr2) {
    if (arr1.size() != arr2.size()) {
        return false;
    }
    for (size_t i = 0; i < arr1.size(); i++) {
        if (arr1[i] != arr2[i]) {
            return false;
        }
    }
    return true;
}

int main() {
#ifdef _WIN32
    // 解决 Windows 控制台输出中文乱码的问题
    // 这行代码会将控制台的输出编码设置为 UTF-8 (代码页 65001)
    SetConsoleOutputCP(65001);
#endif

    // 初始化随机数种子，确保每次运行程序时生成的随机数序列都不同
    srand(time(0));

    // 定义测试参数
    int testTime = 500000; // 总共要进行的测试次数
    int maxSize = 100;     // 数组的最大长度
    int maxValue = 100;    // 数组元素的最大值
    bool succeed = true;   // 测试成功标志，默认为 true

    // --- 主要测试循环 ---
    // 这个循环会进行 `testTime` 次随机测试
    for (int i = 0; i < testTime; i++) {
        // 1. 生成一个原始的随机数组
        std::vector<int> originalArr = generateRandomVector(maxSize, maxValue);
        // 2. 复制两份，用于不同的排序算法
        std::vector<int> arr1 = originalArr; // 用于归并排序
        std::vector<int> arr2 = originalArr; // 用于标准库排序 (对照组)

        // 3. 分别用两种方法进行排序
        mergeSort::sort(arr1);     // 使用我们自己实现的 mergeSort
        comparator(arr2);          // 使用标准库的 std::sort 作为对照

        // 4. 比较排序结果
        if (!areVectorsEqual(arr1, arr2)) {
            // 如果归并排序的结果与标准库不一致，说明有 bug
            succeed = false;
            std::cout << "Oops! 排序算法出错了!" << std::endl;
            // 打印出出错时的原始数组和各种排序的结果，方便调试
            std::cout << "原始数组: ";
            printVector(originalArr);
            std::cout << "--> mergeSort 结果错误: ";
            printVector(arr1);
            std::cout << "正确结果 (comparator): ";
            printVector(arr2);
            break; // 只要有一次出错，就立即停止测试
        }
    }

    // 根据测试结果输出最终信息
    if (succeed) {
        std::cout << "Nice! " << testTime << "全部通过!" << std::endl;
    }

    // --- 单次运行演示 (mergeSort) ---
    std::cout << "\n--- 单次运行演示 (mergeSort) ---" << std::endl;
    std::vector<int> arr = generateRandomVector(maxSize, maxValue);
    std::cout << "排序前: ";
    printVector(arr);
    mergeSort::sort(arr);
    std::cout << "排序后: ";
    printVector(arr);

    return 0;
}//
// Created by 吴林东 on 2025/11/9.
//
