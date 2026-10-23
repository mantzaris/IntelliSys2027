"""Public interface constraints only: no correct decisions or oracle references."""
from .environment import FIELDS, OPTIONS


def fixed_array(items):
    return {"type":"array","prefixItems":items,"minItems":len(items),"maxItems":len(items),"items":False}


def defender_schema():
    values=[{"enum":[*options,None]} for options in OPTIONS]
    properties={"state":fixed_array(values),"plan":fixed_array(values+[{"type":["string","null"]},{"type":["string","null"]}]),
                "evidence":fixed_array([{"type":["integer","null"]} for _ in FIELDS]),
                "clarify":{"type":"array","items":{"enum":list(FIELDS)},"maxItems":6}}
    return {"type":"object","properties":properties,"required":list(properties),"additionalProperties":False}


def character_schema():
    # Public slot-value compatibility is enforced, not semantic truth. A false
    # but well-formed recollection remains fully possible in every condition.
    common={"claim":{"type":"string"},"source":{"type":["integer","null"]},"target":{"type":["string","null"]}}
    variants=[]
    for slot,options in enumerate(OPTIONS):
        props={"kind":{"enum":["edit","recollect","propose"]},"slot":{"const":slot},"value":{"enum":list(options)},**common}
        variants.append({"type":"object","properties":props,"required":list(props),"additionalProperties":False})
    props={"kind":{"enum":["peer","pass"]},"slot":{"type":["integer","null"]},"value":{"type":["string","null"]},**common}
    variants.append({"type":"object","properties":props,"required":list(props),"additionalProperties":False})
    return {"anyOf":variants}
