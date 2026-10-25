"""CPU-only reproduction from the locked local mirrors; never touches the queue."""
from .common import verify_science

def main():
    verify_science()
    from . import analysis,secondary,exposure_join_v2,semantic_review_v2,prepare_review_presentation,reporting,write_narrative,verify_package
    analysis.run();secondary.run();exposure_join_v2.run();semantic_review_v2.run()
    prepare_review_presentation.run();reporting.run();write_narrative.run();verify_package.run()

if __name__=='__main__':main()
