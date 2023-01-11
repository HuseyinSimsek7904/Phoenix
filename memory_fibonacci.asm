first-number = 1;
second-number = 1;

mov 0 ar; Address register
svm ar first-number;
alu add ar 1 ar;
svm ar second-number;

loop:
    mov ar ap;

    ldm ar br;
    alu sub ar 1 ar;
    ldm ar cr;
    alu add ar 2 ar;

    alu add br cr br;
    svm ar cr;
jmp loop;