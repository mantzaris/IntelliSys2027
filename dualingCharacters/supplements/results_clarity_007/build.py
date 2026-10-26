"""Rebuild only007 products from committed inputs. No model, GPU or remote imports."""
from . import numbers,worksheet,reader,claims,brief,figures
from .ratings_v2 import prepare_forms

def main():
 prepare_forms()
 for module in [numbers,worksheet,reader,claims,brief,figures]:module.run()
 print('CPU reproduction complete. PDFs: /usr/bin/python3 supplements/results_clarity_007/pdf_build.py')
if __name__=='__main__':main()
