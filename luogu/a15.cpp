#include<bits/stdc++.h>
using namespace std;

const int N=1e5+9;
int a[N],prefix[35][N];
 int main() {

     int n,q;cin>>n>>q;
     for (int i = 1;i<=n;++i)cin>>a[i];
     for (int w=0;w<=30;++w)
         for (int i=1;i<=n;++i)prefix[w][i]=prefix[w][i-1]+(a[i]>>w&1);
     while (q--) {
         int l,r;
         cin>>l>>r;
         int ans=0;
         for (int w=0;w<=30;++w) {
             ans+=(l<<w)*(prefix[w][r]-prefix[w][l-1]?1:0);
         }

         cout<<ans<<'\n';

     }
     return 0;


 }
