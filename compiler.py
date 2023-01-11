def convert_to_rom(items):
    text = "v2.0 raw\n"

    for item in items:
        text += hex(item)[2:] + " "

    return text + "\n"


class Token:
    def __init__(self, type_, arg):
        self.type = type_
        self.arg = arg

    def __repr__(self):
        return f"{self.type}: {self.arg}"


class Command:
    def __init__(self, line, command, args):
        self.line = line
        self.command = command
        self.args = args

    def __repr__(self):
        return f"command: {self.command} {self.args}"


class Compiler:
    def __init__(self):
        self.program = ""
        self.process = "IDLE"

        self.log = ""

        self.tokens = []
        self.decoded = []
        self.commands = []
        self.defined = {}
        self.library_contents = {}

        self.error_count = 0
        self.warning_count = 0

        self.char_no = 0

    @property
    def line_no(self):
        line_no = 1

        for char in self.program[:self.char_no]:
            if char == "\n":
                line_no += 1

        return line_no

    @property
    def char_no_in_line(self):
        char_no = 0

        for i in self.program[::-1]:
            if i == "\n":
                break

            char_no += 1

        return char_no

    @property
    def end_of_program(self):
        return self.char_no >= len(self.program)

    @property
    def char(self):
        return self.program[self.char_no]

    def next_line(self):
        while True:
            if self.end_of_program:
                break

            if self.char == "\n":
                break

            self.char_no += 1

        self.char_no += 1

        self.tokens.clear()

    def load_string(self, program):
        self.program = program
        self.message("INFO", "Loaded program.")

    def load_file(self, file_name):
        self.message("INFO", f"Loading program from {file_name}.")
        try:
            with open(file_name) as file:
                self.load_string(file.read())

        except FileNotFoundError:
            self.message("LOADER_ERROR", "Could not find the file.")

    def message(self, type_, message):
        self.log += f"{self.process}: [{type_}] {message}\n"

    def message_line(self, type_, message):
        self.message(type_, f"({self.line_no}) {message}")

    def error(self, message):
        self.message("ERROR", message)
        self.error_count += 1

    def error_line(self, message):
        self.error(f"(line {self.line_no}) {message}")

    def error_line_(self, message, line):
        self.error(f"(line {line}) {message}")

    def warning(self, message):
        self.message("WARNING", message)
        self.warning_count += 1

    def warning_line(self, message):
        self.warning(f"({self.line_no}) {message}")

    def success_message(self, success, fail):
        if self.error_count == 0:
            self.message("INFO", "Found no errors.")
            self.message("INFO", success)

        else:
            self.message("INFO", f"Found {self.error_count} errors.")
            self.message("INFO", fail)

    def dump_log(self, file_name):
        with open(file_name, "w") as file:
            file.write(self.log)

    def get_token(self):
        token = ""

        while True:
            if self.end_of_program:
                break

            if self.char in END_OF_TOKEN:
                break

            token += self.char
            self.char_no += 1

        return token

    def compile(self):
        self.process = "PARSE"
        self.error_count = 0
        self.char_no = 0

        self.tokens = []
        self.defined = PRE_DEFINITIONS.copy()
        self.commands = []

        while not self.end_of_program:
            if self.char in DECIMALS:
                number = int(self.get_token())
                self.tokens.append(Token("number", number))

            elif self.char == ":":
                if len(self.tokens) != 1 or self.tokens[0].type != "keyword":
                    self.error_line(f"Invalid syntax.")

                else:
                    self.defined[self.tokens[0].arg] = Token("number", len(self.commands))

                self.next_line()

            elif self.char in ";\n":
                if self.tokens:
                    cmd, *args = self.tokens

                    if cmd.type == "keyword":
                        if cmd == "call":
                            pass

                        elif cmd == "ret":
                            pass

                        else:
                            self.commands.append(Command(self.line_no, cmd.arg, list(args)))

                    elif cmd.type == "definition":
                        if len(args) != 1 or args[0].type != "number":
                            self.error_line(f"Expected only one number after equals sign.")

                        elif cmd.arg in self.defined:
                            self.error_line(f"Constant '{cmd.arg}' was already defined.")

                        else:
                            self.defined[cmd.arg] = args[0]

                    else:
                        self.error_line(f"Invalid syntax.")

                self.next_line()

            elif self.char == "=":
                if len(self.tokens) != 1 or self.tokens[0].type != "keyword":
                    self.error_line(f"A definition should have one keyword before equals sign.")

                self.tokens[0].type = "definition"
                self.char_no += 1

            elif self.char in " ":
                self.char_no += 1

            else:
                word = self.get_token()
                self.tokens.append(Token("keyword", word))

        self.message("INFO", f"Found {len(self.defined)} definitions.")
        self.success_message("Successfully parsed.", "Could not parse.")

        if self.error_count > 0:
            return

        self.process = "DECODING"
        self.error_count = 0
        self.decoded = []

        for command in self.commands:
            for i, arg in enumerate(command.args):
                if arg.type == "keyword":
                    if arg.arg not in self.defined:
                        self.error_line_(f"Unknown name '{arg.arg}'.", command.line)

                    else:
                        command.args[i] = self.defined[arg.arg]

                elif arg.type == "number":
                    pass

                else:
                    self.error_line_(f"Invalid syntax", command.line)

            cmd = command.command
            args = command.args

            if cmd == "mov":
                if len(args) != 2:
                    self.error_line_(f"'mov' takes exactly 2 arguments", command.line)
                    continue

                if args[1].type == "register":
                    if args[0].type == "register":
                        self.add_decoded(args[0].arg * 2 ** 20 + args[1].arg * 2 ** 16)

                    elif args[0].type == "number":
                        self.add_decoded(1 * 2 ** 24 + args[0].arg + args[1].arg * 2 ** 16)

                    elif args[0].type == "port":
                        self.add_decoded(3 * 2 ** 24 + args[0].arg * 2 ** 22 + args[1].arg * 2 ** 16)

                    else:
                        self.error_line_("'mov' should take a register, a number or a port as first argument here.", command.line)
                        continue

                elif args[1].type == "port":
                    if args[0].type == "register":
                        self.add_decoded(7 * 2 ** 24 + args[0].arg * 2 ** 20 + args[1].arg * 2 ** 22)

                    elif args[0].type == "number":
                        self.add_decoded(8 * 2 ** 24 + args[0].arg + args[1].arg * 2 ** 22)

                    else:
                        self.error_line_("'mov' should take a register or a number as first argument here.", command.line)
                        continue

                else:
                    self.error_line_(f"'mov' takes a register or a port as second argument.", command.line)
                    continue

            elif cmd == "ldm":
                if len(args) != 2:
                    self.error_line_(f"'ldm' takes exactly 2 arguments.", command.line)
                    continue

                if args[0].type != "register":
                    self.error_line_(f"'ldm' takes a register as first argument.", command.line)
                    continue

                if args[1].type == "register":
                    self.add_decoded(2 * 2 ** 24 + args[0].arg * 2 ** 18 + args[1].arg * 2 ** 16)

                elif args[1].type == "port":
                    self.add_decoded(9 * 2 ** 24 + args[0].arg * 2 ** 18 + args[1].arg * 2 ** 22)

                else:
                    self.error_line_(f"'ldm' takes a register or a port as second argument.", command.line)
                    continue

            elif cmd == "svm":
                if len(args) != 2:
                    self.error_line_(f"'svm' takes exactly 2 arguments.", command.line)
                    continue

                if len(args) != 2:
                    self.error_line_(f"'svm' takes exactly 2 arguments.", command.line)
                    continue

                if args[1].type != "register":
                    self.error_line_(f"'svm' takes a register as second argument.", command.line)
                    continue

                if args[0].type == "register":
                    self.add_decoded(4 * 2 ** 24 + args[0].arg * 2 ** 20 + args[1].arg * 2 ** 18)

                elif args[0].type == "number":
                    self.add_decoded(5 * 2 ** 24 + args[0].arg + args[1].arg * 2 ** 18)

                elif args[0].type == "port":
                    self.add_decoded(6 * 2 ** 24 + args[0].arg * 2 ** 22 + args[1].arg * 2 ** 18)

                else:
                    self.error_line_(f"'svm' takes a register, a number or a port as first argument.", command.line)
                    continue

            elif cmd == "jmp":
                if len(args) != 1:
                    self.error_line_(f"'jmp' takes exactly 2 arguments.", command.line)
                    continue

                if args[0].type == "register":
                    self.add_decoded(1 * 2 ** 28 + args[0].arg * 2 ** 20)

                elif args[0].type == "number":
                    self.add_decoded(2 * 2 ** 28 + args[0].arg)

                else:
                    self.error_line_(f"'jmp' takes a register or a number as argument.", command.line)
                    continue

            elif cmd == "ijp":
                if len(args) != 3:
                    self.error_line_(f"'ijp' takes exactly 3 arguments.", command.line)
                    continue

                # todo

            elif cmd == "jpm":
                if len(args) != 1:
                    self.error_line_(f"'jpm' takes exactly 2 arguments.", command.line)
                    continue

                # todo

            elif cmd == "ijm":
                if len(args) != 3:
                    self.error_line_(f"'ijm' takes exactly 3 arguments.", command.line)
                    continue

                # todo

            elif cmd == "alu":
                if len(args) != 4:
                    self.error_line_(f"'alu' takes exactly 4 arguments.", command.line)
                    continue

                if args[0].type != "operator":
                    self.error_line_(f"'alu' takes a register for first argument.", command.line)
                    continue

                if args[1].type != "register":
                    self.error_line_(f"'alu' takes a register for second argument.", command.line)
                    continue

                if args[3].type != "register":
                    self.error_line_(f"'alu' takes a register for fourth argument.", command.line)
                    continue

                if args[2].type == "register":
                    self.add_decoded(4 * 2 ** 28 + args[0].arg * 2 ** 24 + args[1].arg * 2 ** 18 + args[2].arg * 2 ** 20 + args[3].arg * 2 ** 16)
                    print(command, hex(self.decoded[-1]))

                elif args[2].type == "number":
                    self.add_decoded(5 * 2 ** 28 + args[0].arg * 2 ** 24 + args[1].arg * 2 ** 18 + args[2].arg + args[3].arg * 2 ** 16)

                else:
                    self.error_line_(f"'alu' takes a register or a number for third argument.", command.line)
                    continue

            elif cmd == "alp":
                if len(args) != 4:
                    self.error_line_(f"'alu' takes exactly 4 arguments.", command.line)
                    continue

                if args[0].type != "operator":
                    self.error_line_(f"'alu' takes a register for first argument.", command.line)
                    continue

                if args[1].type != "register":
                    self.error_line_(f"'alu' takes a register for second argument.", command.line)
                    continue

                if args[3].type != "register":
                    self.error_line_(f"'alu' takes a register for fourth argument.", command.line)
                    continue

                if args[2].type == "register":
                    self.add_decoded(4 * 2 ** 28 + args[0].arg * 2 ** 24 + args[1].arg * 2 ** 18 + args[2].arg * 2 ** 20 + args[3].arg * 2 ** 16 + 2 ** 23)

                elif args[2].type == "number":
                    self.add_decoded(5 * 2 ** 28 + args[0].arg * 2 ** 24 + args[1].arg * 2 ** 18 + args[2].arg + args[3].arg * 2 ** 16 + 2 ** 23)

                else:
                    self.error_line_(f"'alu' takes a register or a number for third argument.", command.line)
                    continue

            else:
                self.error_line_(f"Unknown command '{cmd}'.", command.line)
                continue

        self.message("INFO", f"Using {len(self.decoded)} bytes in ROM.")
        self.success_message("Successfully decoded.", "Could not decode.")

        self.process = "IDLE"

    def add_decoded(self, value):
        self.decoded.append(value)

    def save_file(self, file_name):
        self.message("INFO", "Saving ROM file.")
        with open(file_name, "w") as file:
            file.write(convert_to_rom(self.decoded))


def main():
    compiler = None

    try:
        while True:
            com, *args_ = input("> ").split(" ")
            args = []
            options = []

            for arg in args_:
                arg = arg.strip()

                if arg == "":
                    continue

                if arg[0] == "-":
                    options.append(arg[1:])
                    continue

                args.append(arg)

            try:
                if com in ("exit", "quit"):
                    if args:
                        print(f"{com} expects no arguments")
                        continue

                    print("Exiting")
                    return

                elif com in ("init",):
                    if args:
                        print(f"{com} expects no arguments")
                        continue

                    compiler = Compiler()
                    print("Initialized")

                elif com in ("load",):
                    if len(args) != 1:
                        print(f"{com} expects only one argument")
                        continue

                    try:
                        compiler.load_file(args[0])

                    except FileNotFoundError:
                        print(f"Could not find file {args[0]}")

                    else:
                        print(f"Loaded {args[0]}")

                elif com in ("save",):
                    if len(args) != 1:
                        print(f"{com} expects only one argument")
                        continue

                    compiler.save_file(args[0])
                    print(f"Loaded {args[0]}")

                elif com in ("comp",):
                    if args:
                        print(f"{com} expects no arguments")
                        continue

                    compiler.compile()
                    print(f"Compiled")
                    print(compiler.log)

                elif com in ("asm",):
                    if len(args) != 2:
                        print(f"{com} expects only 2 argument")
                        continue

                    compiler = Compiler()
                    compiler.load_file(args[0])
                    compiler.compile()

                    if compiler.error_count == 0:
                        compiler.save_file(args[1])

                    print(compiler.log)

            except Exception as e:
                print(f"{type(e).__name__}: {e}")

    except KeyboardInterrupt:
        print("Exiting")


DECIMALS = "0123456798"
END_OF_TOKEN = "\n :;="
PRE_DEFINITIONS = {
    "ar": Token("register", 0),
    "br": Token("register", 1),
    "cr": Token("register", 2),
    "dr": Token("register", 3),

    "ap": Token("port", 0),
    "bp": Token("port", 1),
    "cp": Token("port", 2),
    "dp": Token("port", 3),

    "add": Token("operator", 0),
    "adc": Token("operator", 1),
    "sub": Token("operator", 2),
    "sbb": Token("operator", 3),
    "mul": Token("operator", 4),
    "mlh": Token("operator", 5),
    "div": Token("operator", 6),
    "mod": Token("operator", 7),
    "and": Token("operator", 8),
    "bor": Token("operator", 9),
    "xor": Token("operator", 10),
    "sar": Token("operator", 11),
    "rtl": Token("operator", 12),
    "rtr": Token("operator", 13),

    "upd": Token("alu-mode", 2),

    "ltz": Token("flag", 0),
    "lez": Token("flag", 1),
    "eqz": Token("flag", 2),
    "gez": Token("flag", 3),
    "gtz": Token("flag", 4),
    "nez": Token("flag", 5),
}


if __name__ == '__main__':
    main()
