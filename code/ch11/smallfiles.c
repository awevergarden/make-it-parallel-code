/*
 * smallfiles.c -- the same data as many small files or one big one.
 * Make It Parallel, Chapter 11.
 *
 * Writes COUNT records of 1 KB each, either as COUNT separate files
 * or as one file of COUNT KB, into DIR, and reports microseconds per
 * record. Then removes everything it wrote.
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o smallfiles smallfiles.c
 * Run:    ./smallfiles many|one COUNT DIR
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "../common/timer.h"

#define RECORD 1024

int main(int argc, char *argv[])
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s many|one COUNT DIR\n", argv[0]);
        return 1;
    }
    int many = strcmp(argv[1], "many") == 0;
    long count = atol(argv[2]);
    const char *dir = argv[3];
    if (count < 1 || mkdir(dir, 0755) != 0) {
        perror(dir);
        return 1;
    }
    char rec[RECORD], path[4096];
    memset(rec, 'x', sizeof rec);
    double t0 = now_seconds();
    if (many) {
        for (long k = 0; k < count; k++) {
            snprintf(path, sizeof path, "%s/rec%06ld.dat", dir, k);
            FILE *f = fopen(path, "wb");
            if (f == NULL || fwrite(rec, 1, RECORD, f) != RECORD || fclose(f) != 0) {
                perror(path);
                return 1;
            }
        }
    } else {
        snprintf(path, sizeof path, "%s/all.dat", dir);
        FILE *f = fopen(path, "wb");
        if (f == NULL) {
            perror(path);
            return 1;
        }
        for (long k = 0; k < count; k++)
            if (fwrite(rec, 1, RECORD, f) != RECORD) {
                perror(path);
                return 1;
            }
        if (fclose(f) != 0) {
            perror(path);
            return 1;
        }
    }
    double t = now_seconds() - t0;
    printf("%s,%ld,%.2f\n", many ? "many" : "one", count, t / count * 1e6);
    if (many)                                  /* clean up */
        for (long k = 0; k < count; k++) {
            snprintf(path, sizeof path, "%s/rec%06ld.dat", dir, k);
            unlink(path);
        }
    else
        unlink(path);
    rmdir(dir);
    return 0;
}
