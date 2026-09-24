/*
 * float_order.c -- floating-point addition is not associative.
 * Make It Parallel, Chapter 2.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o float_order float_order.c
 */
#include <stdio.h>

int main(void)
{
    double a = 0.1, b = 0.2, c = 0.3;
    double left = (a + b) + c;
    double right = a + (b + c);

    printf("(a + b) + c = %.17g\n", left);
    printf("a + (b + c) = %.17g\n", right);
    printf("equal? %s\n", left == right ? "yes" : "no");
    return 0;
}
