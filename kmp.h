#pragma once
#include <string>
#include <vector>

// KMP 字符串匹配模块（入门友好注释）
// 使用方式：
// 1) 调用 buildNext(m) 预处理模式串 m，得到 next 数组；
// 2) 调用 indexOf(s, m) 在文本 s 中查找 m 的首次出现位置；若不存在返回 -1。
//
// 关于 next 数组（亦称「失配表」）：
// next[i] 表示当模式串在位置 i 发生失配时，模式指针应当跳到的位置。
// 本实现使用经典的「next[0] = -1」哨兵写法：当 i2==0 仍然失配，直接右移文本指针。

namespace kmp {
    // 构建 next 数组。复杂度 O(M)。
    // 参数：m 为模式串。
    // 约定：当 m 长度为 1 时，返回 {-1}（只含哨兵）。
    std::vector<int> buildNext(const std::string& m);

    // 在文本 s 中查找模式 m 的首次出现位置，若不存在返回 -1。复杂度 O(N+M)。
    // 约定：当 m 为空或 m 长于 s，直接返回 -1（避免空匹配带来的语义歧义）。
    int indexOf(const std::string& s, const std::string& m);
}
