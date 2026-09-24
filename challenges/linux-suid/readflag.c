/* Binario SUID root: imprime el contenido de /root/flag.txt.
   Lee el fichero directamente (sin shell) para no perder privilegios. */
#include <fcntl.h>
#include <unistd.h>
int main(void) {
    int fd = open("/root/flag.txt", O_RDONLY);
    if (fd < 0) return 1;
    char buf[512];
    ssize_t n;
    while ((n = read(fd, buf, sizeof buf)) > 0) write(1, buf, n);
    return 0;
}
