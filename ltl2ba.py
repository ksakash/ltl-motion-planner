#!/usr/bin/env python3

from subprocess import Popen, PIPE
import re
import argparse
import sys
import __main__

class Ltl2baParser:
    prog_title = re.compile('^never\s+{\s+/\* (.+?) \*/$')
    prog_node = re.compile('^([^_]+?)_([^_]+?):$')
    prog_edge = re.compile('^\s+:: (.+?) -> goto (.+?)$')
    prog_skip = re.compile('^\s+(?:skip)$')
    prog_ignore = re.compile('(?:^\s+do)|(?:^\s+if)|(?:^\s+od)|'
                             '(?:^\s+fi)|(?:})|(?:^\s+false);?$')
    g = dict()

    @staticmethod
    def parse(ltl2ba_output, ignore_title=True):
        graph = Graph()
        src_node = None
        for line in ltl2ba_output.split('\n'):
            if Ltl2baParser.is_title(line):
                title = Ltl2baParser.get_title(line)
                # print ("The title is: ", title)
            elif Ltl2baParser.is_node(line):
                name, label, accepting = Ltl2baParser.get_node(line)
                # print ("name: ", name, " label: ", label, " accepting: ", accepting)
                src_node = name
            elif Ltl2baParser.is_edge(line):
                dst_node, label = Ltl2baParser.get_edge(line)
                assert src_node is not None
                # print ("src_node: ", src_node, " dst_node: ", dst_node, " label: ", label)
                if src_node not in Ltl2baParser.g:
                    s = dict()
                    s[label] = []
                    s[label].append(dst_node)
                    Ltl2baParser.g[src_node] = s
                else:
                    if label not in Ltl2baParser.g[src_node]:
                        Ltl2baParser.g[src_node][label] = []
                        Ltl2baParser.g[src_node][label].append(dst_node)
                    else:
                        Ltl2baParser.g[src_node][label].append(dst_node)
            elif Ltl2baParser.is_skip(line):
                assert src_node is not None
            elif Ltl2baParser.is_ignore(line):
                pass
            else:
                print("--{}--".format(line))
                raise ValueError("{}: invalid input:\n{}"
                                 .format(Ltl2baParser.__name__, line))

        return g

    @staticmethod
    def is_title(line):
        return Ltl2baParser.prog_title.match(line) is not None

    @staticmethod
    def get_title(line):
        assert Ltl2baParser.is_title(line)
        return Ltl2baParser.prog_title.search(line).group(1)

    @staticmethod
    def is_node(line):
        return Ltl2baParser.prog_node.match(line) is not None

    @staticmethod
    def get_node(line):
        assert Ltl2baParser.is_node(line)
        prefix, label = Ltl2baParser.prog_node.search(line).groups()
        return (prefix + "_" + label, label,
                True if prefix == "accept" else False)

    @staticmethod
    def is_edge(line):
        return Ltl2baParser.prog_edge.match(line) is not None

    @staticmethod
    def get_edge(line):
        assert Ltl2baParser.is_edge(line)
        label, dst_node = Ltl2baParser.prog_edge.search(line).groups()
        return (dst_node, label)

    @staticmethod
    def is_skip(line):
        return Ltl2baParser.prog_skip.match(line) is not None

    @staticmethod
    def is_ignore(line):
        return Ltl2baParser.prog_ignore.match(line) is not None


def gltl2ba():
    args = parse_args()

    ltl = get_ltl_formula(args.file, args.formula)

    (output, err, exit_code) = run_ltl2ba(args, ltl)

    if exit_code != 1:

        print(output)

        if (True):

            prog = re.compile("^[\s\S\w\W]*?"
                              "(never\s+{[\s\S\w\W]+?})"
                              "[\s\S\w\W]+$")
            match = prog.search(output)
            assert match, output

            graph = Ltl2baParser.parse(match.group(1))
            print(graph)

    else:
        eprint("{}: ltl2ba error:".format(__main__.__file__))
        eprint(output)
        sys.exit(exit_code)

    return


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--formula",
                       help="translate LTL into never claim", type=str)
    group.add_argument("-F", "--file",
                       help="like -f, but with the LTL formula stored in a "
                       "1-line file", type=argparse.FileType('r'))
    parser.add_argument("-d",
                        help="display automata (D)escription at each step",
                        action='store_true')
    parser.add_argument("-s",
                        help="computing time and automata sizes (S)tatistics",
                        action='store_true')
    parser.add_argument("-l",
                        help="disable (L)ogic formula simplification",
                        action='store_true')
    parser.add_argument("-p",
                        help="disable a-(P)osteriori simplification",
                        action='store_true')
    parser.add_argument("-o",
                        help="disable (O)n-the-fly simplification",
                        action='store_true')
    parser.add_argument("-c",
                        help="disable strongly (C)onnected components "
                        "simplification", action='store_true')
    parser.add_argument("-a",
                        help="disable trick in (A)ccepting conditions",
                        action='store_true')
    parser.add_argument("-g", "--graph",
                        help="display buchi automaton graph",
                        action='store_true')
    parser.add_argument("-G", "--output-graph",
                        help="save buchi automaton graph in pdf file",
                        type=argparse.FileType('w'))
    parser.add_argument("-t", "--dot",
                        help="print buchi automaton graph in DOT notation",
                        action='store_true')
    parser.add_argument("-T", "--output-dot",
                        help="save buchi automaton graph in DOT file",
                        type=argparse.FileType('w'))
    return parser.parse_args()


def get_ltl_formula(file, formula):
    assert file is not None or formula is not None
    if file:
        try:
            ltl = file.read()
        except Exception as e:
            eprint("{}: {}".format(__main__.__file__, str(e)))
            sys.exit(1)
    else:
        ltl = formula
    ltl = re.sub('\s+', ' ', ltl)
    if len(ltl) == 0 or ltl == ' ':
        eprint("{}: empty ltl formula.".format(__main__.__file__))
        sys.exit(1)
    return ltl


def run_ltl2ba(args, ltl):
    ltl2ba_args = ["ltl2ba", "-f", ltl]

    ltl2ba_args += list("-{}".format(x) for x in "dslpoca"
                        if getattr(args, x))

    try:
        process = Popen(ltl2ba_args, stdout=PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
    except FileNotFoundError as e:
        eprint("{}: ltl2ba not found.\n".format(__main__.__file__))
        eprint("Please download ltl2ba from\n")
        eprint("\thttp://www.lsv.fr/~gastin/ltl2ba/ltl2ba-1.2b1.tar.gz\n")
        eprint("compile the sources and add the binary to your $PATH, e.g.\n")
        eprint("\t~$ export PATH=$PATH:path-to-ltlb2ba-dir\n")
        sys.exit(1)

    output = output.decode('utf-8')

    return output, err, exit_code


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

if __name__ == '__main__':
    gltl2ba()
