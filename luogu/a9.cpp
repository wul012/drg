#include<bits/stdc++.h>
using namespace std;
const int N=1000;
char s[N];      // 存储字符串（下标从1开始）
int prefix[N];  // 前缀和：'L'计为+1，'R'计为-1
int main() {
    scanf("%s", s+1);  // 从下标1开始读入字符串
    int n = strlen(s+1);
    
    // 计算前缀和：'L'=+1, 'R'=-1
    // prefix[i] 表示前 i 个字符的权值和
    for (int i=1;i<=n;++i)prefix[i]=prefix[i-1]+(s[i]=='L'?1:-1);

    // 枚举所有子串 [i, j]，找最长的平衡串
    // 平衡串定义：'L' 和 'R' 数量相等，即区间和为0
    int ans = 0;
    for (int i=1;i<=n;++i) {
        for (int j=i;j<=n;++j) {  // j 从 i 开始，不是从1开始
            // 区间 [i,j] 的和 = prefix[j] - prefix[i-1]
            if (prefix[j]-prefix[i-1]==0) {
                ans=max(ans,j-i+1);  // 长度是 j-i+1，不是 j-1+i
            }
        }
    }
    cout<<ans<<'\n';

    return 0;
}