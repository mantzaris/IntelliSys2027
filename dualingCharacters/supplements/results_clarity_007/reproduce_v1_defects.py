"""Explicitly synthetic software reproduction, not human ratings or research results."""
from supplements.evidence_validation_006 import ratings as old
from .common import HERE,write

def run():
 row=dict.fromkeys(old.FIELDS,'')|{'item_id':'SYNTHETIC_FIXTURE_ONLY','status':'rated','response':'continues_prior_position','correctness':'normative_preference','citation_support':'no_citation','claimed_authority':'own_preference','visibility':'visible','confidence':'medium','supporting_turns':'SYNTHETIC t1/t2'}
 old.validate_rows([row],['SYNTHETIC_FIXTURE_ONLY'])
 result=old.agreement([row],[row]);assert all(r['negative_agreement']==1 for r in result['statement_labels'])
 try:old.validate_rows([row|{'statement_labels':'explicit_acknowledgment'}],['SYNTHETIC_FIXTURE_ONLY'])
 except ValueError as e:error=str(e)
 else:raise AssertionError('Expected v1 response/claim vocabulary mismatch')
 output={'classification':'SYNTHETIC SOFTWARE FIXTURE ONLY; not research agreement','defect_A':{'optional_labels_blank':True,'v1_joint_denominator':result['jointly_rated_including_uncertain'],'labels_incorrectly_counted_both_negative':len(result['statement_labels']),'negative_agreement_returned':1.0},'defect_B':{'rubric_instruction':'record other readings in statement_labels and notes','secondary_response_example':'explicit_acknowledgment','validator_error':error},'actual_human_ratings':0}
 write(HERE/'reports/SYNTHETIC_V1_DEFECT_REPRODUCTION.json',output);print(output)
if __name__=='__main__':run()
