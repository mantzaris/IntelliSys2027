"""One command regenerates review tables from completed saved artifacts."""
from . import audit,exposure,analyze,packets,report


def main():
    audit.main();exposure.main();analyze.main();packets.main();report.main()


if __name__=='__main__':main()
