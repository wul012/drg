// #include "nQueens.h"
//
// #include <cstdlib>   // std::abs
// #include <iostream>  // 仅用于必要的调试输出(本实现中没有强制使用)
//
// namespace {
//
//     // ============================= 普通回溯实现相关辅助函数 =============================
//
//     /**
//      * @brief 检查在第 row 行、第 col 列放置皇后是否和之前的皇后冲突
//      *
//      * @param record  记录数组, record[i] 表示第 i 行皇后所在的列号
//      * @param row     当前准备放皇后的行号 (0 ~ n-1)
//      * @param col     当前准备放皇后的列号 (0 ~ n-1)
//      * @return        如果不冲突(合法位置)返回 true, 否则返回 false
//      *
//      * 冲突的三种情况:
//      *   1) 同一列:     之前某一行 i 的皇后所在列 record[i] == col;
//      *   2) 主对角线:   行差 == 列差，即 abs(row - i) == abs(col - record[i]);
//      *   3) 副对角线:   与主对角线同样通过上式即可覆盖(两种斜线统一用绝对值判断)。
//      */
//     bool isValidPosition(const std::vector<int>& record, int row, int col) {
//         for (int i = 0; i < row; ++i) {
//             int placedCol = record[i];
//             // 1) 同一列
//             if (placedCol == col) {
//                 return false;
//             }
//             // 2) 同一条斜线(主对角线或副对角线)
//             if (std::abs(row - i) == std::abs(col - placedCol)) {
//                 return false;
//             }
//         }
//         return true;
//     }
//
//     /**
//      * @brief 递归尝试在第 row 行放置皇后 (普通回溯版本)
//      *
//      * @param n       棋盘大小(N × N)
//      * @param row     当前正在处理的行号
//      * @param record  record[i] 表示第 i 行皇后所在列号, -1 表示当前行还未放皇后
//      * @param count   通过引用返回累计的解个数
//      */
//     void processSimple(int n, int row, std::vector<int>& record, long long& count) {
//         // 递归终止条件: row == n, 说明前 0..n-1 行都已经成功放置皇后
//         if (row == n) {
//             ++count;  // 找到一种合法的全局摆放方式
//             return;
//         }
//
//         // 尝试在当前行的每一列放置皇后
//         for (int col = 0; col < n; ++col) {
//             if (isValidPosition(record, row, col)) {
//                 record[row] = col;                   // 记录当前行皇后所在的列
//                 processSimple(n, row + 1, record, count);  // 递归处理下一行
//                 record[row] = -1;                    // 回溯(可省略, 这里写出来更直观)
//             }
//         }
//     }
//
//     // ============================= 位运算优化实现相关辅助函数 =============================
//
//     /**
//      * @brief 使用位运算优化的递归过程(对应截图中的 process2 函数)
//      *
//      * @param limit        用于限制有效列的 bitmask, 低 n 位为 1, 其余为 0。
//      * @param colLim       列限制: 某一位为 1 表示该列已经有皇后, 不能再放。
//      * @param leftDiaLim   左斜线限制: 某一位为 1 表示该左斜线上已有皇后。
//      * @param rightDiaLim  右斜线限制: 某一位为 1 表示该右斜线上已有皇后。
//      * @return             从当前状态继续往下摆放, 最终能够形成的合法摆放方案个数。
//      *
//      * 解释:
//      *   - 我们按 "行" 递归, 第一层递归放第 0 行的皇后, 第二层放第 1 行, 依此类推。
//      *   - 每一层递归时, 通过三种限制(colLim, leftDiaLim, rightDiaLim) 计算出
//      *     当前行哪些列可以放皇后, 这些位置组成一个 bitmask, 记为 "pos"。
//      *   - 然后我们从 pos 中每次取出最右侧的那一个 1(对应的一列), 把皇后放在
//      *     该列上, 并更新三种限制, 递归处理下一行。
//      */
//     long long processBitmask(std::uint32_t limit,
//                              std::uint32_t colLim,
//                              std::uint32_t leftDiaLim,
//                              std::uint32_t rightDiaLim) {
//         // 如果列限制已经等于 limit, 说明低 n 位全部为 1,
//         // 即前 n 列上都已经成功放置了皇后, 得到一种完整解。
//         if (colLim == limit) {
//             return 1;  // 找到一种合法方案
//         }
//
//         // pos 中的 1 表示该列可以放皇后
//         // 先把已经不能放的位置都置为 1(colLim | leftDiaLim | rightDiaLim),
//         // 取反之后得到可以放的位置, 最后再与 limit 做一次与运算, 去掉高位的无效 bit。
//         std::uint32_t pos = limit & (~(colLim | leftDiaLim | rightDiaLim));
//
//         long long res = 0;  // 用来累加方案数
//
//         while (pos != 0) {
//             // 提取 pos 中最右侧的那一个 1, 对应一个可以放皇后的列。
//             // 例如 pos = 0b010100, 则 mostRightOne = 0b000100。
//             // 这里利用二进制补码性质: x & (-x) 只留下最右侧的 1。
//             std::uint32_t mostRightOne = pos & -pos;
//
//             // 从 pos 中删掉这一个 1, 继续枚举其它可用列。
//             pos -= mostRightOne;
//
//             // 更新三种限制并递归:
//             //   - 新的列限制: 原来占用的列 + 当前放置的列
//             //   - 左斜线限制: (原来左斜线限制 | 当前列) 整体左移一位
//             //   - 右斜线限制: (原来右斜线限制 | 当前列) 整体右移一位
//             res += processBitmask(limit,
//                                   colLim | mostRightOne,
//                                   (leftDiaLim | mostRightOne) << 1,
//                                   (rightDiaLim | mostRightOne) >> 1);
//         }
//
//         return res;
//     }
//
// } // 匿名命名空间结束, 辅助函数仅在本文件可见
//
// // =================================== 对外接口实现 =====================================
//
// namespace nQueens {
//
//     long long countNQueensSimple(int n) {
//         if (n <= 0) {
//             return 0;  // 非法输入直接返回 0
//         }
//
//         std::vector<int> record(n, -1);  // record[i] = 第 i 行皇后的列号
//         long long count = 0;
//         processSimple(n, 0, record, count);
//         return count;
//     }
//
//     long long countNQueensBitmask(int n) {
//         // 题目限制: 不允许超过 32 皇后 (使用 32 位整型作为 bitmask)
//         if (n < 1 || n > 32) {
//             return 0;
//         }
//
//         // 如果 n == 32, 那么低 32 位全部为 1, 即 0xFFFFFFFF;
//         // 否则, 只保留低 n 位为 1: (1u << n) - 1。
//         std::uint32_t limit = (n == 32) ? 0xFFFFFFFFu : ((1u << n) - 1u);
//
//         return processBitmask(limit, 0u, 0u, 0u);
//     }
//
// } // namespace nQueens


#include<vector>
#include "nQueens.h"
#include<cstdlib>
namespace {

    bool isValidPosition(const std::vector<int>& record,int row,int col) {
        for(int i = 0; i < row;++i ) {
            if (record[i] == col || std::abs(row-i) == std::abs(col - record[i]))return false;
        }

        return true;
    }


    void processSimple(int n , int row , std::vector<int>& record,long long& count) {
        if (row == n) {
            ++count;
            return;
        }
        for (int col = 0;col < n;++col) {
            if (isValidPosition(record,row,col)) {
                record[row] = col;
                processSimple(n,row+1,record,count);
                record[row] = -1;


            }
        }

        }
    long long processBitmask(std::uint32_t limit,std::uint32_t collim,
        std::uint32_t leftDialim,std::uint32_t rightDialim) {
        if (collim == limit) {
            return 1;
        }

        std::uint32_t pos = limit & (~(collim | leftDialim | rightDialim));
        long long res = 0;
        while (pos!=0) {
            std::uint32_t mostRightOne = pos & -pos;
            pos -= mostRightOne;
            res+= processBitmask(limit,collim | mostRightOne, (leftDialim | mostRightOne) << 1, (rightDialim | mostRightOne) >> 1);
        }

        return res;
    }



    }

namespace nQueens {
    long long countNQueensSimple(int n ) {
        if (n<=0) return 0;
        std::vector<int> record(n,-1);
        long long count =0;
        processSimple(n,0,record,count);
        return count;
    }

    long long countNQueensBitmask(int n ) {
        if (n<=0 || n>32) return 0;
        std::uint32_t limit = (n == 32) ? 0xFFFFFFFFu : ((1u << n) - 1u);
        return processBitmask(limit,0u,0u,0u);
    }
}

