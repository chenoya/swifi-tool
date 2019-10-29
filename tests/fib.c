int fib(int num) {
    if (num == 0 || num == 1) {
        return 1;    
    } else {
        return fib(num-1) + fib(num-2);
    }
}

int main() {
    int r = fib(50);
    return 0;
}
