"""Readable spacing in authored prose only; never applied to source quotations."""
import re
WORDS='turn|turns|seed|seeds|Figure|Table|Finding|all|with|the|of|in|per|and|at|from|for|has|is|same|gives|retains|supplies|episode|across|these|than|only|mean|count|prior|original|fixed|unchanged|clarification|denominator|Edit|Recollect|Propose|continues|available|recorded|after|before|their|our|its|every|each|within|a|an'
def tidy(text):
 text=re.sub(r'\b('+WORDS+r')(?=\d)',r'\1 ',text)
 return re.sub(r'(?<=\d)(episodes|families|opportunities|events|paired|turns|hours|points|words)\b',r' \1',text)
