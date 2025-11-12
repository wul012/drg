// #include "selectionSort.h"
// #include <algorithm> // 包含 std::swap 和 std::sort
// #include <vector>
//
// /*
//  * public static void selectionSort(int[] arr) {
//  *     if (arr == null || arr.length < 2) {
//  *         return;
//  *     }
//  *     for (int i = 0; i < arr.length - 1; i++) {
//  *         int minIndex = i;
//  *         for (int j = i + 1; j < arr.length; j++) {
//  *             minIndex = arr[j] < arr[minIndex] ? j : minIndex;
//  *         }
//  *         swap(arr, i, minIndex);
//  *     }
//  * }
//  */
// namespace selectionSort {
//     void sort(std::vector<int>& arr) {
//         // 在C++中，我们通常使用 .size() 来获取容器的大小。
//         // 如果向量的大小小于2，则无需排序。
//         if (arr.size() < 2) {
//             return;
//         }
//
//         // 外部循环遍历数组，范围是 0 到 n-2
//         for (size_t i = 0; i < arr.size() - 1; i++) {
//             // 假设当前位置 i 的元素是最小的
//             size_t minIndex = i;
//
//             // 内部循环从 i+1 开始，寻找 [i...n-1] 范围内的最小值
//             for (size_t j = i + 1; j < arr.size(); j++) {
//                 // 如果找到一个更小的元素，就更新最小元素的索引
//                 if (arr[j] < arr[minIndex]) {
//                     minIndex = j;
//                 }
//             }
//
//             // 找到最小元素的索引后，将其与当前位置 i 的元素交换。
//             // std::swap 是C++标准库提供的交换函数，更推荐使用。
//             if (i != minIndex) {
//                 std::swap(arr[i], arr[minIndex]);
//             }
//         }
//     }
// }

#include<vector>
#include<algorithm>
#include "selectionSort.h"

namespace selectionSort {
    void sort(std::vector<int>& arr) {
        if (arr.size()<2){
        return;}
        for (size_t i = 0;i<arr.size()-1;i++) {
            size_t minIndex = i;
            for (size_t j=i+1;j<arr.size();j++) {
                if (arr[j]<arr[minIndex]) {
                    minIndex = j;
                }


            }
            if (i!=minIndex) {
                std::swap(arr[i],arr[minIndex]);
            }
        }




    }
}
