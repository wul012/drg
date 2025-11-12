// #include "quickSort.h"
// #include <algorithm> // 用于 std::swap
//
// namespace { // 使用匿名命名空间来隐藏辅助函数，避免污染全局命名空间
//
//     /**
//      * @brief 分区函数 (Partition) - Lomuto 分区方案
//      *        选择最后一个元素作为 pivot，将数组分为两部分：
//      *        一部分小于等于 pivot，另一部分大于 pivot。
//      * @param arr 要分区的向量
//      * @param low 子数组的起始索引
//      * @param high 子数组的结束索引
//      * @return pivot 最终所在位置的索引
//      */
//     int partition(std::vector<int>& arr, int low, int high) {
//         int pivot = arr[high]; // 选择最后一个元素作为基准值 (pivot)
//         int i = low - 1;       // i 指向小于 pivot 区域的最后一个元素
//
//         for (int j = low; j < high; j++) {
//             // 如果当前元素小于等于 pivot
//             if (arr[j] <= pivot) {
//                 i++; // 扩展小于 pivot 的区域
//                 std::swap(arr[i], arr[j]);
//             }
//         }
//         // 将 pivot 放到正确的位置 (i+1)
//         std::swap(arr[i + 1], arr[high]);
//         return (i + 1);
//     }
//
//     /**
//      * @brief 快速排序的递归辅助函数
//      * @param arr 要排序的向量
//      * @param low 子数组的起始索引
//      * @param high 子数组的结束索引
//      */
//     void quickSortRecursive(std::vector<int>& arr, int low, int high) {
//         if (low < high) {
//             // pi 是分区后 pivot 的索引
//             int pi = partition(arr, low, high);
//
//             // 分别对 pivot 左右两边的子数组进行递归排序
//             quickSortRecursive(arr, low, pi - 1);
//             quickSortRecursive(arr, pi + 1, high);
//         }
//     }
//
// } // 匿名命名空间结束
//
// namespace quickSort {
//
//     void sort(std::vector<int>& arr) {
//         if (arr.size() < 2) {
//             return; // 元素个数小于2，无需排序
//         }
//         quickSortRecursive(arr, 0, arr.size() - 1);
//     }
//
// }
#include "quickSort.h"
#include<algorithm>

namespace {
    int partition(std::vector<int>& arr,int low,int high) {
        int pivot = arr[high];
        int i = low-1;
        for (int j = low ;j<high;j++) {
            if (arr[j]<pivot) {
                i++;
                std::swap(arr[i],arr[j]);
            }
        }
        std::swap(arr[i+1],arr[high]);
        return i+1;



    }
    void quickSortRecursive(std::vector<int>& arr,int low,int high) {
        if (low<high) {
            int pi = partition(arr,low,high);
            quickSortRecursive(arr,low,pi-1);
            quickSortRecursive(arr,pi+1,high);
        }
    }





}


namespace quickSort {
    void sort(std::vector<int>& arr) {
        if (arr.size()<2) {
            return;

        }
        quickSortRecursive(arr,0,arr.size()-1);
    }

}
