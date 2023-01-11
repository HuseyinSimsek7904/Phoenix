mov 0 ar;
svm 0 ar;

alu add ar 1 ar;
svm 0 ar;

alu add ar 1 ar;
svm 0 ar;

alu add ar 1 ar;
svm 0 ar;

alu add ar 1 ar;
svm 0 ar;

alu add ar 1 ar;
svm 0 ar;

alu add ar 1 ar;
svm 0 ar;

alu add ar 1 ar;
svm 1 ar;

loop:
    mov 0 cr;
    ldm cr ar;
    mov ar ap;

    mov 1 cr;
    ldm cr ar;
    mov ar bp;

    mov 2 cr;
    ldm cr ar;
    mov ar cp;

    mov 3 cr;
    ldm cr ar;
    mov ar dp;

    ; 0 word
    mov 3 cr;
    ldm cr ar;

    mov 7 cr;
    ldm cr br;

    alp add ar br ar;

    svm ar cr;

    mov 3 cr;
    svm br cr;

    ; 1 word
    mov 2 cr;
    ldm cr ar;

    mov 6 cr;
    ldm cr br;

    alp adc ar br ar;

    svm ar cr;

    mov 2 cr;
    svm br cr;

    ; 2 word
    mov 1 cr;
    ldm cr ar;

    mov 5 cr;
    ldm cr br;

    alp adc ar br ar;

    svm ar cr;

    mov 1 cr;
    svm br cr;

    ; 3 word
    mov 0 cr;
    ldm cr ar;

    mov 4 cr;
    ldm cr br;

    alp adc ar br ar;

    svm ar cr;

    mov 0 cr;
    svm br cr;
jmp loop;