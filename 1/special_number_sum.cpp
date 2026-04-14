#include <iostream>
using namespace std;

// 判断一个数的数位中是否包含 2, 0, 1, 9
bool isSpecialNumber(int num) {
    while (num > 0) {
        int digit = num % 10;
        if (digit == 2 || digit == 0 || digit == 1 || digit == 9) {
            return true;
        }
        num /= 10;
    }
    return false;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    int n;
    cin >> n;
    
    int sum = 0;
    for (int i = 1; i <= n; i++) {
        if (isSpecialNumber(i)) {
            sum += i;
        }
    }
    
    cout << sum << endl;
    
    return 0;
}
