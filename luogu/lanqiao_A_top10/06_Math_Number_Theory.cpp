#include <iostream>

using namespace std;

// 题型 6：数学论题与数论基础 
// 【具体真题】：快速幂计算 (洛谷 P1226 类似 / 蓝桥杯多次考查大数快速幂)
// 题目描述：
// 给你三个整数 a, b, p，求 a^b mod p 的值。
// a, b, p 都在 10^9 级别，直接用 for 循环乘 10^9 次必定超时。必须使用快速幂算法。

// 辗转相除法求最大公约数 (蓝桥杯也是必背)
long long gcd(long long a, long long b) {
    return b == 0 ? a : gcd(b, a % b);
}

// 快速幂取模：求 a^b % p，时间复杂度 O(log b)
long long fast_pow(long long a, long long b, long long p) {
    long long res = 1;
    a %= p;
    while (b > 0) {
        if (b & 1) res = (res * a) % p; // 如果当前二进制位是 1，把当前的 a 乘进结果
        a = (a * a) % p;               // 底数每次翻倍平方
        b >>= 1;                       // 指数右移一位
    }
    return res;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long a, b, p;
    if (cin >> a >> b >> p) {
        cout << a << "^" << b << " mod " << p << "=" << fast_pow(a, b, p) << "\n";
    }
    
    return 0;
}

/*
========== 测试数据 ==========
输入：
2 10 9

输出：
2^10 mod 9=7

解释：
2^10 = 1024
1024 mod 9 = 7
============================
*/
