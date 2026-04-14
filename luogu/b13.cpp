#include <bits/stdc++.h>
using namespace std;

// 题目：斤斤计较的小Z (lanqiao OJ 2047)
// 题意：给定两个字符串 S1 和 S2，求 S1 在 S2 中出现了多少次。
// 典型的字符串匹配问题，这里提供了两种解法：KMP 算法 和 字符串哈希算法。
// 注意：题目描述中第一行是 S1，第二行是 S2。但是示例输入中第一行较长，第二行较短，
// 这说明示例中其实第一行是 S2（主串），第二行是 S1（模式串）。
// 为防止歧义，我们代码里统一把短的叫 pattern (模式串)，长的叫 text (主串)。

const int N = 1e6 + 5;

// ==========================================
// 解法一：KMP 算法
// 时间复杂度：O(N + M)，空间复杂度：O(M)
// ==========================================
namespace KMP {
    int nxt[N]; // next 数组，记录模式串的前缀和后缀的最长公共部分长度

    // 构建 next 数组（针对模式串 P）
    void build_next(const string& p) {
        int m = p.length();
        nxt[0] = 0; // 第一个字符没有前后缀，所以是 0
        int j = 0;  // j 表示当前最长相等前后缀的长度
        
        // i 从 1 开始遍历模式串
        for (int i = 1; i < m; i++) {
            // 当遇到不匹配的字符时，j 回退到上一个可能匹配的位置（通过 nxt 数组）
            while (j > 0 && p[i] != p[j]) {
                j = nxt[j - 1];
            }
            // 如果字符匹配，最长相等前后缀长度加 1
            if (p[i] == p[j]) {
                j++;
            }
            // 记录当前位置的 nxt 值
            nxt[i] = j;
        }
    }

    // 在主串 T 中查找模式串 P 出现的次数
    int search(const string& t, const string& p) {
        if (p.empty() || t.empty() || p.length() > t.length()) return 0;
        
        build_next(p);
        
        int ans = 0;
        int j = 0; // j 记录模式串中已经匹配的长度
        int n = t.length(), m = p.length();
        
        // 遍历主串
        for (int i = 0; i < n; i++) {
            // 当字符不匹配时，利用 nxt 数组让模式串快速向右滑动，避免主串指针回退
            while (j > 0 && t[i] != p[j]) {
                j = nxt[j - 1];
            }
            // 如果字符匹配，模式串指针 j 前进一步
            if (t[i] == p[j]) {
                j++;
            }
            // 当 j 等于模式串长度时，说明找到了一个完整的匹配
            if (j == m) {
                ans++;
                // 找到一个匹配后，继续寻找下一个匹配（利用 nxt 数组回退）
                // 比如找 "ABA" 在 "ABABA" 中的次数，会找到 2 次
                j = nxt[j - 1];
            }
        }
        return ans;
    }
}

// ==========================================
// 解法二：字符串哈希算法 (String Hash)
// 时间复杂度：O(N + M)，空间复杂度：O(N)
// ==========================================
namespace Hash {
    // 使用 unsigned long long 自然溢出，相当于对 2^64 取模，省去显式取模操作
    typedef unsigned long long ull;
    
    const int P = 131; // 经验质数（进制数），也可以是 13331 等
    ull h[N];   // 记录主串的前缀哈希值
    ull p_pow[N]; // 记录 P 的各次方
    
    // 初始化前缀哈希数组和 P 的次方数组
    void init(const string& s) {
        int n = s.length();
        p_pow[0] = 1;
        h[0] = 0;
        for (int i = 1; i <= n; i++) {
            p_pow[i] = p_pow[i - 1] * P;
            h[i] = h[i - 1] * P + s[i - 1]; // s[i-1] 即当前字符的 ASCII 码
        }
    }
    
    // 获取主串中区间 [l, r] (下标从 1 开始) 的子串哈希值
    ull get_hash(int l, int r) {
        // 相当于把高位的哈希值左移 (r-l+1) 位，然后减去，留下低位的目标区间哈希值
        return h[r] - h[l - 1] * p_pow[r - l + 1];
    }
    
    // 在主串 T 中查找模式串 P 出现的次数
    int search(const string& t, const string& p) {
        if (p.empty() || t.empty() || p.length() > t.length()) return 0;
        
        int n = t.length();
        int m = p.length();
        
        // 1. 初始化主串的前缀哈希数组
        init(t);
        
        // 2. 计算模式串的整体哈希值
        ull target_hash = 0;
        for (int i = 0; i < m; i++) {
            target_hash = target_hash * P + p[i];
        }
        
        int ans = 0;
        
        // 3. 用一个长度为 m 的“滑动窗口”在主串上滑动
        // 窗口左端点从 1 移动到 n - m + 1
        for (int i = 1; i <= n - m + 1; i++) {
            int l = i, r = i + m - 1;
            // 如果窗口内的子串哈希值 == 模式串哈希值，说明找到了一个匹配
            if (get_hash(l, r) == target_hash) {
                ans++;
            }
        }
        
        return ans;
    }
}

int main() {
    ios::sync_with_stdio(0), cin.tie(0), cout.tie(0);
    
    string s1, s2;
    // 坑点注意：题目文字描述说 S1 是模式串，但在给的图片样例里，第一行明明是长的(S2)，第二行是短的(S1)。
    // 所以我们读入后自己判断长短，保证短的是模式串 (pattern)，长的是主串 (text)。
    if (cin >> s1 >> s2) {
        string text = s1.length() >= s2.length() ? s1 : s2;
        string pattern = s1.length() < s2.length() ? s1 : s2;
        
        // 这里提供两种调用方式，你可以选择其中一种：
        
        // 1. 调用 KMP 算法
        cout << KMP::search(text, pattern) << "\n";
        
        // 2. 调用 字符串哈希算法 (结果应该是一模一样的，可以取消注释测试)
         cout << Hash::search(text, pattern) << "\n";
    }
    
    return 0;
}
