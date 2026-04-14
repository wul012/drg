#include<bits/stdc++.h>
using namespace std;

int a,b,c;

bool f(int i) {
    return i%a!=0&&i%b!=0&&i%c!=0;
}



int main() {
    int n;cin>>n;
    cin>>a>>b>>c;
    int ans=0;
    for (int i=1;i<=n;i++) {
        if (f(i))ans++;
    }
    cout<<ans<<'\n';
    return 0;
}