#include <stdlib.h>
#include <string.h>

#include "accents.h"

/* Letras acentuadas do português são gravadas na ROM como códigos gregos Shift-JIS (a fonte da
   ROM recebe glifos novos nesses códigos; ver tools/accents_font.py). */
static const struct { const char* from; const char* to; } accent_map[] = {
    {"á", "α"},
    {"à", "β"},
    {"â", "γ"},
    {"ã", "δ"},
    {"ç", "ε"},
    {"é", "ζ"},
    {"ê", "η"},
    {"í", "θ"},
    {"ó", "ι"},
    {"ô", "κ"},
    {"õ", "λ"},
    {"ú", "μ"},
    {"ü", "ν"},
    {"Á", "Α"},
    {"À", "Β"},
    {"Â", "Γ"},
    {"Ã", "Δ"},
    {"Ç", "Ε"},
    {"É", "Ζ"},
    {"Ê", "Η"},
    {"Í", "Θ"},
    {"Ó", "Ι"},
    {"Ô", "Κ"},
    {"Õ", "Λ"},
    {"Ú", "Μ"},
};

char* accent_remap_utf8(const char* u8) {
    size_t n = strlen(u8);
    /* cada acentuada (2 bytes) vira grega (2 bytes): o tamanho não cresce */
    char* out = malloc(n + 1);
    if (!out)
        return NULL;
    size_t o = 0;
    for (size_t i = 0; i < n;) {
        size_t k;
        for (k = 0; k < sizeof(accent_map) / sizeof(*accent_map); k++) {
            size_t l = strlen(accent_map[k].from);
            if (!strncmp(&u8[i], accent_map[k].from, l)) {
                memcpy(&out[o], accent_map[k].to, strlen(accent_map[k].to));
                o += strlen(accent_map[k].to);
                i += l;
                break;
            }
        }
        if (k == sizeof(accent_map) / sizeof(*accent_map))
            out[o++] = u8[i++];
    }
    out[o] = '\0';
    return out;
}
