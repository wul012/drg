#include<bits/stdc++.h>
using namespace std;
using ll=long long;
const int N=1000;
int a[N];  // 存储每一位的数值（0-15）
// 字符映射表：0-9对应'0'-'9'，10-15对应'A'-'F'
char ch[]={'0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'};
// n进制转m进制：先转十进制，再转目标进制
void solve() {
    int n,m;cin>>n>>m;  // n=原进制，m=目标进制
    string s;cin>>s;     // 原进制字符串
    int len=s.length();
    s='#'+s;             // 前置'#'使下标从1开始
    // 步骤1：将字符转换为数值
    for (int i=1;i<=len;++i) {
        if('0'<=s[i]&&s[i]<='9')a[i]=s[i]-'0';      // '0'-'9' -> 0-9
        else a[i]=s[i]-'A'+10;                      // 'A'-'F' -> 10-15
    }
    // 步骤2：n进制转十进制，按位权展开 x = x*n + a[i]
    ll x = 0;
    for (int i =1;i<=len;++i)x=x*n+a[i];  // 注意：是 x= 不是 x+=
    // 步骤3：十进制转m进制，短除法取余
    string ans;
    if(x==0)ans="0";  // 特判：输入为0
    else {
        while (x){
            ans+=ch[x%m];  // 取最低位（逆序）
            x/=m;          // 去掉最低位
        }
    }
    reverse(ans.begin(),ans.end());  // 反转得到正序
    cout<<ans<<'\n';
}

int main() {
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    int _;cin>>_;
    while (_--)solve();
    return 0;
}