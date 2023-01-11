mov 1 ar;
mov 0 br;

loop:
    mov ar ap;

    alu add ar br cr;
    mov ar br;
    mov cr ar;
jmp loop;