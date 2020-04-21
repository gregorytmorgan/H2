#!/usr/bin/python3.6
#
# h2.py
#

def main():
    import sys
    import getopt
    import fileinput

    debug = 0
    verbose = 0

    def usage():
        program_name = sys.argv[0]
        print("Usage: {} [options]".format(program_name))
        print("  -d,\t --debug\tDebug.")
        print("  -h,\t --help\t\tHelp.")
        print("  -v,\t --verbose\tVerbose.")

    try:
        opts, args = getopt.getopt(sys.argv[1:] , "dhv", ["debug", "help", "verbose"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    #print("argv: {}".format(sys.argv))

    for o, a in opts:
        if o in ("-d", "--debug"):
            debug = 0
            verbose = 9999
        elif o in ("-h", "--help"):
            sys.argv.remove(o)
            usage()
            sys.exit(0)
        elif o in ("-v", "--verbose"):
            verbose += 1
        else:
            assert False, "Invalid option"

    with fileinput.input() as f:
        #parser.parse(''.join(f), tracking=True)
        print("{}".format(''.join(f)))


if __name__ == "__main__":
    main()

# end file
