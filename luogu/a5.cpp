//
// Created by 吴林东 on 2026/3/24.
//
#include<bits/stdc++.h>
using namespace std;
using ll=long long;
const int N = 50;
int a[N];
int main() {

    // 待转换的十六进制字符串（字符范围可包含 0-9、A-F）
    string s= "2021ABCD";
    // 先把每一位字符映射为对应数值：'0'~'9' -> 0~9, 'A'~'F' -> 10~15
    for (int i=0;i<s.length();++i) {
        if ('0'<=s[i]&&s[i]<='9')a[i+1]=s[i]-'0';
        else a[i+1]=s[i]-'A'+10;
    }

// 按十六进制进位规则累加：x = x * 16 + 当前位
ll x = 0;
for(int i = 1;i<=s.length();++i) {
    x=x*16+a[i];
}
// 输出转换后的十进制结果
cout<<x<<'\n';
    return 0;
}