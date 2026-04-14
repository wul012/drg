#include<bits/stdc++.h>
using namespace std;
const int N=1e6+9;
char s[N];

int main() {
    // 优化输入输出流
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    
    // C++20 中 cin 不再支持直接读取到 char* 指针(s+1 会退化为 char*)
    // 为了防止缓冲区溢出，所以这里改用 scanf 读取
    scanf("%s", s + 1); 
    
    // 获取字符串长度，因为从 s+1 开始存，所以传给 strlen 的也是 s+1
    int n = strlen(s+1);
    
    // 双指针判断回文串
    // l 指向开头，r 指向结尾
    int l = 1, r = n;
    bool ans = true;
    
    while (l < r && ans) {
        // 如果对应位置字符不相等，说明不是回文串
        if (s[l] != s[r]) ans = false;
        l++, r--; // 左右指针向中间靠拢
    }
    
    // ans 为 true 输出 Y，否则输出 N
    cout << (ans ? "Y" : "N");

    return 0;
}