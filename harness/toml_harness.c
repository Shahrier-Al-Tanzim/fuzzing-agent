/*
 * toml_harness.c — single-input driver for tomlc99 under ASan/UBSan.
 *
 * Reads TOML from argv[1] (a file) or stdin, parses it, then walks the
 * entire resulting tree and converts every scalar. The walk matters: a
 * bare toml_parse() misses bugs that only fire in the accessor and
 * conversion paths, which is where a lot of tomlc99's pointer arithmetic
 * actually lives.
 *
 * Exit codes:
 *   0  valid parse, full walk completed
 *   2  well-formed rejection (parse returned NULL with an error message)
 *   64 harness usage error - NOT a finding
 *
 * Sanitizer aborts and fatal signals bypass these entirely, which is the
 * point.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#include "toml.h"

#define EXIT_ACCEPT 0
#define EXIT_REJECT 2
#define EXIT_USAGE  64

/* 1 MiB. Generated inputs should never approach this; if one does, the
   strategy has gone pathological and we want to know via code 64 rather
   than by exhausting memory. */
#define MAX_INPUT (1024UL * 1024UL)

/* Bound on tree-walk recursion. tomlc99's own parser may or may not have a
   depth limit; ours must, otherwise a deeply nested input blows the
   harness stack and we would report our own bug as the library's. */
#define MAX_WALK_DEPTH 200

static char *read_all(FILE *fp, size_t *out_len)
{
    size_t cap = 8192, len = 0;
    char *buf = malloc(cap);
    if (!buf) return NULL;

    for (;;) {
        if (len + 1 >= cap) {
            if (cap >= MAX_INPUT) { free(buf); return NULL; }
            cap *= 2;
            char *nb = realloc(buf, cap);
            if (!nb) { free(buf); return NULL; }
            buf = nb;
        }
        size_t n = fread(buf + len, 1, cap - len - 1, fp);
        len += n;
        if (n == 0) {
            if (feof(fp)) break;
            if (ferror(fp)) { free(buf); return NULL; }
        }
        if (len >= MAX_INPUT) { free(buf); return NULL; }
    }

    buf[len] = '\0';
    *out_len = len;
    return buf;
}

static void walk_table(toml_table_t *tab, int depth);

static void walk_array(toml_array_t *arr, int depth)
{
    if (!arr || depth > MAX_WALK_DEPTH) return;

    int n = toml_array_nelem(arr);
    for (int i = 0; i < n; i++) {
        toml_raw_t raw = toml_raw_at(arr, i);
        if (raw) {
            char *s = NULL;
            if (toml_rtos(raw, &s) == 0) free(s);

            int64_t iv;      (void)toml_rtoi(raw, &iv);
            double  dv;      (void)toml_rtod(raw, &dv);
            int     bv;      (void)toml_rtob(raw, &bv);
            toml_timestamp_t ts; (void)toml_rtots(raw, &ts);
            continue;
        }

        toml_array_t *sub = toml_array_at(arr, i);
        if (sub) { walk_array(sub, depth + 1); continue; }

        toml_table_t *subt = toml_table_at(arr, i);
        if (subt) { walk_table(subt, depth + 1); }
    }
}

static void walk_table(toml_table_t *tab, int depth)
{
    if (!tab || depth > MAX_WALK_DEPTH) return;

    for (int i = 0; ; i++) {
        const char *key = toml_key_in(tab, i);
        if (!key) break;

        toml_raw_t raw = toml_raw_in(tab, key);
        if (raw) {
            char *s = NULL;
            if (toml_rtos(raw, &s) == 0) free(s);

            int64_t iv;      (void)toml_rtoi(raw, &iv);
            double  dv;      (void)toml_rtod(raw, &dv);
            int     bv;      (void)toml_rtob(raw, &bv);
            toml_timestamp_t ts; (void)toml_rtots(raw, &ts);
            continue;
        }

        toml_array_t *arr = toml_array_in(tab, key);
        if (arr) { walk_array(arr, depth + 1); continue; }

        toml_table_t *sub = toml_table_in(tab, key);
        if (sub) { walk_table(sub, depth + 1); }
    }
}

int main(int argc, char **argv)
{
    FILE *fp = stdin;

    if (argc > 2) {
        fprintf(stderr, "harness: usage: %s [file]\n", argv[0]);
        return EXIT_USAGE;
    }
    if (argc == 2) {
        fp = fopen(argv[1], "rb");
        if (!fp) {
            fprintf(stderr, "harness: cannot open %s: %s\n",
                    argv[1], strerror(errno));
            return EXIT_USAGE;
        }
    }

    size_t len = 0;
    char *input = read_all(fp, &len);
    if (fp != stdin) fclose(fp);

    if (!input) {
        fprintf(stderr, "harness: input too large or unreadable\n");
        return EXIT_USAGE;
    }

    char errbuf[512];
    errbuf[0] = '\0';

    /* toml_parse mutates its buffer in place - that is expected, and it is
       why we pass our own heap copy rather than a literal. */
    toml_table_t *root = toml_parse(input, errbuf, sizeof(errbuf));

    if (!root) {
        /* Well-formed rejection. Print the library's own message: Module 5
           mines these to tell the LLM *why* inputs are being refused. */
        fprintf(stderr, "REJECT: %s\n",
                errbuf[0] ? errbuf : "(no error message)");
        free(input);
        return EXIT_REJECT;
    }

    walk_table(root, 0);

    toml_free(root);
    free(input);
    return EXIT_ACCEPT;
}