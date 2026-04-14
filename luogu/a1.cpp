
#include <iostream>
using namespace std;

bool hasDigit2019(int x) {
    while (x > 0) {
        int d = x % 10;
        if (d == 2 || d == 0 || d == 1 || d == 9) {
            return true;
        }
        x /= 10;
    }
    return false;
}

int main() {
    int n;
    cin >> n;

    long long sum = 0;
    for (int i = 1; i <= n; i++) {
        if (hasDigit2019(i)) {
            sum += i;
        }
    }

    cout << sum << endl;
    return 0;
}