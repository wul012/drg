# N 皇后问题 (N-Queens Problem) 说明文档

## 1. 问题描述

N 皇后问题是一个经典的回溯算法问题：

**目标**: 在一个 N × N 的国际象棋棋盘上放置 N 个皇后，使得任意两个皇后都不能互相攻击。

**约束条件**:
- 任意两个皇后不能在同一行
- 任意两个皇后不能在同一列
- 任意两个皇后不能在同一条对角线上（包括主对角线和副对角线）

**问题**: 求出所有可能的摆放方案的总数。

## 2. 实现方案

本项目提供了两种求解方法：

### 2.1 普通回溯法 `countNQueensSimple(int n)`

#### 算法思路
- 从第 0 行开始，逐行放置皇后
- 对于每一行，尝试在每一列放置皇后
- 每次放置前，检查该位置是否与之前放置的皇后冲突
- 如果合法，继续递归处理下一行
- 如果所有 N 行都成功放置，计数器加 1

#### 冲突检测
使用 `isValidPosition()` 函数检查位置 `(row, col)` 是否合法：

```cpp
bool isValidPosition(const std::vector<int>& record, int row, int col) {
    for (int i = 0; i < row; ++i) {
        int placedCol = record[i];
        // 检查同一列
        if (placedCol == col) return false;
        // 检查对角线: 行差 == 列差
        if (std::abs(row - i) == std::abs(col - placedCol)) return false;
    }
    return true;
}
```

**冲突判断依据**:
1. **同一列**: `record[i] == col`
2. **同一对角线**: `|row - i| == |col - record[i]|`
   - 主对角线和副对角线都可以用这个公式统一判断

#### 复杂度分析
- **时间复杂度**: O(N!)，当 N > 13 时会非常慢
- **空间复杂度**: O(N)，用于存储 record 数组和递归栈
- **适用场景**: 适合学习理解，直观易懂，但效率较低

### 2.2 位运算优化法 `countNQueensBitmask(int n)`

#### 核心思想
使用三个 32 位整数作为位掩码（bitmask）来表示哪些列和对角线已经被占用：
- `colLim`: 列限制，某一位为 1 表示该列已有皇后
- `leftDiaLim`: 左斜线限制（左上到右下方向）
- `rightDiaLim`: 右斜线限制（左下到右上方向）

#### 算法流程

```cpp
long long processBitmask(uint32_t limit, uint32_t colLim,
                         uint32_t leftDiaLim, uint32_t rightDiaLim) {
    // 终止条件: 所有列都已放置皇后
    if (colLim == limit) return 1;

    // 计算当前行可以放置皇后的位置
    uint32_t pos = limit & (~(colLim | leftDiaLim | rightDiaLim));

    long long res = 0;
    while (pos != 0) {
        // 提取最右侧的 1（可放置的列）
        uint32_t mostRightOne = pos & -pos;
        pos -= mostRightOne;  // 移除这个 1

        // 递归: 更新三种限制
        res += processBitmask(
            limit,
            colLim | mostRightOne,              // 新增列限制
            (leftDiaLim | mostRightOne) << 1,   // 左斜线向左移
            (rightDiaLim | mostRightOne) >> 1   // 右斜线向右移
        );
    }
    return res;
}
```

#### 位运算技巧详解

1. **提取最右侧的 1**: `mostRightOne = pos & -pos`
   - 例如: `pos = 0b010100`，则 `mostRightOne = 0b000100`
   - 原理: 负数的补码表示使得 `-pos` 只在最右侧的 1 及其右边与 pos 相同

2. **计算可用位置**: `pos = limit & (~(colLim | leftDiaLim | rightDiaLim))`
   - `colLim | leftDiaLim | rightDiaLim`: 所有被占用的位置
   - `~(...)`: 取反得到可用位置
   - `& limit`: 只保留有效的 N 位

3. **斜线移动**:
   - 左斜线（`/` 方向）向下移动时，列索引 +1，所以左移: `<< 1`
   - 右斜线（`\` 方向）向下移动时，列索引 -1，所以右移: `>> 1`

#### 复杂度分析
- **时间复杂度**: 仍然是 O(N!)，但常数项大幅优化
- **空间复杂度**: O(N)，仅递归栈空间
- **支持范围**: 1 ≤ N ≤ 32（受 32 位整数限制）
- **性能**: 即使 N = 20 也能在极短时间内计算出结果

#### 性能对比
对于 N = 8（经典 8 皇后问题）：
- 普通回溯: 需要多次函数调用和数组访问
- 位运算优化: 直接通过位操作完成，速度提升数倍到数十倍

## 3. 使用示例

```cpp
#include "nQueens.h"
#include <iostream>

int main() {
    int n = 8;

    // 方法 1: 普通回溯（适合小规模）
    long long result1 = nQueens::countNQueensSimple(n);
    std::cout << n << " 皇后问题的解个数（普通回溯）: " << result1 << std::endl;

    // 方法 2: 位运算优化（推荐）
    long long result2 = nQueens::countNQueensBitmask(n);
    std::cout << n << " 皇后问题的解个数（位运算优化）: " << result2 << std::endl;

    return 0;
}
```

**8 皇后问题的标准答案**: 92 种摆放方案

## 4. 经典答案参考

| N  | 解的个数 |
|----|---------|
| 1  | 1       |
| 4  | 2       |
| 8  | 92      |
| 12 | 14,200  |
| 15 | 2,279,184 |

## 5. 选择建议

- **学习理解**: 使用 `countNQueensSimple()`，代码清晰直观
- **实际应用**: 使用 `countNQueensBitmask()`，性能优异
- **大规模问题** (N > 15): 必须使用位运算优化版本

## 6. 扩展思考

1. 如果要输出所有具体的摆放方案（而不只是计数），如何修改代码？
2. 如何将位运算方法扩展到 N > 32 的情况？（提示: 使用 `std::bitset` 或长整型数组）
3. 能否进一步优化，利用对称性减少计算量？

## 7. 相关文件

- `nQueens.h`: 接口声明
- `nQueens.cpp`: 具体实现
