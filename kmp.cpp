#include "kmp.h"

/*
 * KMP 实现（入门友好说明）
 * - buildNext：构建失配跳转表 next，时间 O(M)
 * - indexOf：利用 next 在 O(N+M) 时间查找首次匹配
 * 核心思想：失配时不回退文本指针，只回退模式指针到“最长可匹配的前缀”。
 */

namespace kmp {

// 构建 next 数组：next[i] 表示在 i 位置失配时，模式指针应跳转到的位置
std::vector<int> buildNext(const std::string& m) {
    // 只有一个字符时，next 只有哨兵 -1
    if (m.size() == 1) return {-1};
    std::vector<int> next(m.size());
    next[0] = -1;                    // 哨兵：表示还在开头，遇到失配只能右移文本指针
    if (m.size() >= 2) next[1] = 0;  // 第二位只能回到 0
    size_t i = 2;                    // 当前正在填写 next 的位置
    int cn = 0;                      // 目前已匹配的最长前后缀长度（candidate）
    while (i < m.size()) {
        if (m[i - 1] == m[cn]) {     // 扩展成功：前一位与 cn 位置相等
            next[i++] = ++cn;        // 记录扩展后的长度，并继续处理下一位
        } else if (cn > 0) {         // 扩展失败：缩短候选，尝试更短的前后缀
            cn = next[cn];
        } else {                     // 已无法再缩短：该位置的值为 0
            next[i++] = 0;
        }
    }
    return next;
}

int indexOf(const std::string& s, const std::string& m) {
    // 特判：空模式或更长模式直接返回 -1
    if (m.empty() || s.size() < m.size()) return -1;
    const std::vector<int> next = buildNext(m); // 预处理表
    size_t i1 = 0; // s 的指针
    size_t i2 = 0; // m 的指针
    while (i1 < s.size() && i2 < m.size()) {
        if (s[i1] == m[i2]) { // 字符相等，双指针前进
            ++i1;
            ++i2;
        } else if (next[i2] == -1) { // 仍在模式开头：只能右移文本指针
            ++i1;
        } else { // 根据 next 跳到最长可匹配的前缀位置
            i2 = static_cast<size_t>(next[i2]);
        }
    }
    // i2 到达模式末尾表示匹配成功，返回起始位置
    return i2 == m.size() ? static_cast<int>(i1 - i2) : -1;
}

} // namespace kmp
