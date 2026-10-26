"""Small presentation helpers; all numbers come from saved measured tables."""
from .common import *
from .dialogues import tex
import csv

def latex_table(headers,rows,alignment=None):
 alignment=alignment or ('l'+'r'*(len(headers)-1));out=[r'\begin{tabular}{'+alignment+'}',r'\toprule',' & '.join(tex(h) for h in headers)+r' \\',r'\midrule']
 out+=[' & '.join(tex(v) for v in row)+r' \\' for row in rows];out +=[r'\bottomrule',r'\end{tabular}'];return '\n'.join(out)
def markdown_table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n'
def percent(x):return 'unavailable' if x is None else f'{100*x:.1f}%'
def pp(x):return f'{100*x:+.2f}'
def read_csv(path):
 with Path(path).open() as f:return list(csv.DictReader(f))
