# count_bytecode.py
# Usage:
#   python count_bytecode.py path/to/script.py
#   or
#   python count_bytecode.py <<'PYCODE'
#   print("hi")
#   PYCODE

import dis, types, fileinput


def collect_code_objects(root: types.CodeType):
    objs, stack = [], [root]
    while stack:
        co = stack.pop()
        objs.append(co)
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                stack.append(c)
    return objs


def count_bytecode(src: str, name="<input>"):
    top = compile(src, name, "exec")
    total = 0
    for co in collect_code_objects(top):
        for _ in dis.get_instructions(co):
            total += 1
    return total


def main():
    src = "".join(fileinput.input())  # Reads from files or stdin
    print(count_bytecode(src))


if __name__ == "__main__":
    main()
