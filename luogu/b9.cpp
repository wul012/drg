#include<bits/stdc++.h>
using namespace std;
using ll = long long;

// 题目：特殊的三角形
// a, b, c 是三条边，且 a < b < c（互不相等）
// 必须满足三角形不等式：a + b > c
// 定义体积 v = a * b * c
// 有 t 次查询，每次查询区间 [l, r] 内的合法三角形个数

// 根据样例和常见题目数据范围，假设最大查询体积不会超过 10^6
// 如果实际题目给的 r 更大，需要把 MAXV 调大
const int MAXV = 1000000; 

// ans[i] 在预处理第一阶段表示体积刚好为 i 的三角形个数
// 在第二阶段（求前缀和后）表示体积 <= i 的三角形总数
int ans[MAXV + 5];

void precompute() {
    // 预处理所有合法的三角形体积
    // 设 a < b < c
    
    // a 的下限是 2（如果 a=1，那么 1+b>c，但 c>b，矛盾，所以 a 至少为 2）
    // a 的上限可以通过体积推导：a * a * a < a * b * c = v <= MAXV
    // 对于 MAXV = 10^6，a 的最大值是 100
    for (int a = 2; a <= 100; ++a) {
        
        // b 的下限是 a + 1
        // b 的上限推导：a * b * b < a * b * c = v <= MAXV
        // a * b^2 <= MAXV，即 b * b <= MAXV / a
        for (int b = a + 1; a * b * b < MAXV; ++b) {
            
            // c 的下限是 b + 1
            // c 的上限由三角形不等式决定：c < a + b
            for (int c = b + 1; c < a + b; ++c) {
                
                // 计算当前三角形的体积
                ll v = 1LL * a * b * c;
                
                // 如果体积超出了我们设定的上限，直接跳出 c 的循环
                // 因为 c 越往后越大，体积只会更大
                if (v > MAXV) break; 
                
                // 体积为 v 的合法三角形数量加 1
                ans[v]++; 
            }
        }
    }
    
    // 将 ans 数组从“单点频次”转换为“前缀和”
    // ans[i] = ans[i-1] + ans[i]
    // 这样我们就可以在 O(1) 的时间复杂度内回答任何区间 [l, r] 的总数
    for (int i = 1; i <= MAXV; ++i) {
        ans[i] += ans[i - 1];
    }
}

int main() {
    // 优化 C++ 的标准输入输出流，防止读写大量数据时超时
    ios::sync_with_stdio(0), cin.tie(0), cout.tie(0);
    
    // 在处理任何查询之前，先进行一次全量预处理
    precompute(); 
    
    int t;
    if (cin >> t) { // 读入查询次数
        while (t--) {
            int l, r;
            cin >> l >> r;
            
            // 防止查询的右端点超过我们预处理的最大值
            // 如果实际比赛中 r 非常大，需要调整 MAXV
            if (l < 1) l = 1;
            if (r > MAXV) r = MAXV;
            
            if (l > r) {
                cout << 0 << '\n';
            } else {
                // 利用前缀和，O(1) 时间内得出区间 [l, r] 里的总个数
                // 原理：[l, r] 的个数 = [1, r] 的个数 - [1, l-1] 的个数
                cout << ans[r] - ans[l - 1] << '\n';
            }
        }
    }
    return 0;
}
