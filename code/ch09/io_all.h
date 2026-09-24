/*
 * io_all.h -- read or write exactly COUNT bytes. Make It Parallel, Ch 9.
 *
 * read() and write() on pipes and sockets may transfer fewer bytes
 * than requested; these helpers loop until the job is done.
 * Return 0 on success, -1 on error or unexpected end of input.
 */
#ifndef IO_ALL_H
#define IO_ALL_H

#include <errno.h>
#include <unistd.h>

static inline int write_all(int fd, const void *buf, size_t count)
{
    const char *p = buf;
    while (count > 0) {
        ssize_t k = write(fd, p, count);
        if (k < 0) {
            if (errno == EINTR)
                continue;               /* interrupted: try again */
            return -1;
        }
        p += k;
        count -= (size_t)k;
    }
    return 0;
}

static inline int read_all(int fd, void *buf, size_t count)
{
    char *p = buf;
    while (count > 0) {
        ssize_t k = read(fd, p, count);
        if (k < 0) {
            if (errno == EINTR)
                continue;
            return -1;
        }
        if (k == 0)
            return -1;                  /* end of input too early */
        p += k;
        count -= (size_t)k;
    }
    return 0;
}

#endif
