// #include "mergeSort.h"
// #include <vector>
//
// namespace mergeSort {
//
//     /**
//      * @brief 合并两个已排序的子数组
//      * @param arr 原始数组
//      * @param left 左边界
//      * @param mid 中间位置
//      * @param right 右边界
//      */
//     void merge(std::vector<int>& arr, int left, int mid, int right) {
//         // 创建临时数组用于合并
//         std::vector<int> temp(right - left + 1);
//
//         int i = left;      // 左子数组的起始索引
//         int j = mid + 1;   // 右子数组的起始索引
//         int k = 0;         // 临时数组的索引
//
//         // 比较左右两个子数组的元素，将较小的元素放入临时数组
//         while (i <= mid && j <= right) {
//             if (arr[i] <= arr[j]) {
//                 temp[k++] = arr[i++];
//             } else {
//                 temp[k++] = arr[j++];
//             }
//         }
//
//         // 如果左子数组还有剩余元素，将它们复制到临时数组
//         while (i <= mid) {
//             temp[k++] = arr[i++];
//         }
//
//         // 如果右子数组还有剩余元素，将它们复制到临时数组
//         while (j <= right) {
//             temp[k++] = arr[j++];
//         }
//
//         // 将临时数组的内容复制回原数组
//         for (int p = 0; p < k; p++) {
//             arr[left + p] = temp[p];
//         }
//     }
//
//     /**
//      * @brief 归并排序的递归实现
//      * @param arr 要排序的数组
//      * @param left 左边界
//      * @param right 右边界
//      */
//     void mergeSortRecursive(std::vector<int>& arr, int left, int right) {
//         if (left < right) {
//             // 计算中间位置
//             int mid = left + (right - left) / 2;
//
//             // 递归排序左半部分
//             mergeSortRecursive(arr, left, mid);
//
//             // 递归排序右半部分
//             mergeSortRecursive(arr, mid + 1, right);
//
//             // 合并两个已排序的子数组
//             merge(arr, left, mid, right);
//         }
//     }
//
//     /**
//      * @brief 归并排序的公共接口
//      * @param arr 要排序的向量
//      */
//     void sort(std::vector<int>& arr) {
//         if (arr.size() < 2) {
//             return;
//         }
//         mergeSortRecursive(arr, 0, arr.size() - 1);
//     }
// }


#include "mergeSort.h"
#include<vector>
namespace mergeSort {
    void merge(std::vector<int>& arr,int left,int mid,int right) {
        std::vector<int> temp(right-left+1);
        int i = left;
        int j = mid + 1;
        int k = 0;
        while (i <= mid && j<=right) {
            if (arr[i]<=arr[j]) {
                temp[k++]=arr[i++];
            }else {
                temp[k++] = arr[j++];
            }
        }
        while (i<=mid ) {
            temp[k++] = arr[i++];
        }
        while (j<=right) {
            temp[k++] = arr[j++];
        }

        for (int p = 0; p < (right - left + 1); p++) {
            arr[left + p] = temp[p];
        }
    }


    void mergeSortRecursive(std::vector<int> &arr,int left ,int right) {
        if (left < right) {
            int mid = left + (right-left)/2;
            mergeSortRecursive(arr,left,mid);
            mergeSortRecursive(arr,mid+1,right);
            merge(arr,left,mid,right);
        }
    }

    void sort(std::vector<int>& arr) {
        if (arr.size()<2) {
            return;
        }
        mergeSortRecursive(arr,0,arr.size()-1);
    }
}