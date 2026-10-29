/* Gerado a partir de tools/accents_font.py -- não edite à mão. */
#ifndef ACCENTS_TBL_H
#define ACCENTS_TBL_H

/* código Shift-JIS (grego reaproveitado) -> letra base ASCII, para as margens do glifo */
static const struct { unsigned short sjis; char base; } accent_glyphs[] = {
    {0x83BF, 'a'}, /* á -> α */
    {0x83C0, 'a'}, /* à -> β */
    {0x83C1, 'a'}, /* â -> γ */
    {0x83C2, 'a'}, /* ã -> δ */
    {0x83C3, 'c'}, /* ç -> ε */
    {0x83C4, 'e'}, /* é -> ζ */
    {0x83C5, 'e'}, /* ê -> η */
    {0x83C6, 'i'}, /* í -> θ */
    {0x83C7, 'o'}, /* ó -> ι */
    {0x83C8, 'o'}, /* ô -> κ */
    {0x83C9, 'o'}, /* õ -> λ */
    {0x83CA, 'u'}, /* ú -> μ */
    {0x83CB, 'u'}, /* ü -> ν */
    {0x839F, 'A'}, /* Á -> Α */
    {0x83A0, 'A'}, /* À -> Β */
    {0x83A1, 'A'}, /* Â -> Γ */
    {0x83A2, 'A'}, /* Ã -> Δ */
    {0x83A3, 'C'}, /* Ç -> Ε */
    {0x83A4, 'E'}, /* É -> Ζ */
    {0x83A5, 'E'}, /* Ê -> Η */
    {0x83A6, 'I'}, /* Í -> Θ */
    {0x83A7, 'O'}, /* Ó -> Ι */
    {0x83A8, 'O'}, /* Ô -> Κ */
    {0x83A9, 'O'}, /* Õ -> Λ */
    {0x83AA, 'U'}, /* Ú -> Μ */
};

#endif
