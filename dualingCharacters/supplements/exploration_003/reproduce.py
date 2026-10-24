"""One-command local CPU reproduction; never captures or expands eligibility."""
from .analysis import main as analyze
from .packet import main as packet
from .reports.prepare_review import main as reviewer_presentation
from .reports.build_report import main as report
from .reports.plot_results import main as figures
from .reports.verify_package import main as verify


def main() -> None:
    analyze()
    packet()
    reviewer_presentation()
    report()
    figures()
    verify()


if __name__=='__main__':main()
