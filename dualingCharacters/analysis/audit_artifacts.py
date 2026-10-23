"""Read-only integrity audit of completed local artifacts, independent of scores.

Early pilots lacking source snapshots remain explicitly qualified. Active/failed
runs are listed separately; unfinished writes are never treated as final evidence.
This checks recorded hashes and trace counts, not scientific validity of a pilot.
"""
from pathlib import Path
import gzip
import hashlib
import json
import tarfile
from pcc.freeze import verify_freeze
from pcc.resources import sha256


def audit(root: Path) -> dict:
    frozen=verify_freeze(root);results=[];unfinished=[]
    for status_path in sorted((root/"artifacts/runs").glob("*/status.json")):
        data=status_path.read_bytes();meta=json.loads(data);run=status_path.parent
        if meta["status"]!="completed":
            unfinished.append({"run_id":run.name,"status":meta["status"]});continue
        record={"run_id":run.name,"status_sha256":hashlib.sha256(data).hexdigest(),
                "source_files_verified":0,"checkpoint_files_verified":0,"archives":[],"qualifications":[]}
        expected=meta.get("source_snapshot_sha256")
        if expected:
            snapshot=run/"source_snapshot.tar.gz"
            assert sha256(snapshot)==expected,(run.name,"snapshot hash")
            with tarfile.open(snapshot) as archive:
                for name,digest in meta["source_hashes"].items():
                    member=archive.extractfile(name)
                    assert member is not None,(run.name,name)
                    assert hashlib.sha256(member.read()).hexdigest()==digest,(run.name,name,"archived source hash")
                    record["source_files_verified"]+=1
            record["source_snapshot_sha256"]=expected
        else:
            assert meta["config"]["phase"]!="confirmatory",(run.name,"confirmatory snapshot missing")
            record["source_qualification"]="Early pilot predates per-run source snapshot; consult historical commit and pilot-specific provenance qualifications."
        if "supplement_runner_sha256" in meta:
            assert sha256(run/"unseen_profiles.py")==meta["supplement_runner_sha256"],(run.name,"supplement runner")
            assert sha256(run/"unseen_profiles_protocol.json")==meta["supplement_protocol_sha256"],(run.name,"supplement protocol")
            record["supplemental_sources_verified"]=2
        for checksums in sorted(run.glob("training/*/checksums.json")):
            for name,digest in json.loads(checksums.read_text()).items():
                if name=="checksums.json":
                    assert meta["config"]["phase"]!="confirmatory",(run.name,"self-referential confirmatory manifest")
                    record["qualifications"].append({"path":str(checksums.relative_to(root)),
                        "issue":"Historical pilot manifest includes a previous-version self hash; that self-entry cannot verify the current manifest. All actual checkpoint files are checked separately; original metadata is preserved."})
                    continue
                assert sha256(checksums.parent/name)==digest,(run.name,str(checksums.parent),name,"checkpoint hash")
                record["checkpoint_files_verified"]+=1
        manifest=run/"trace_archives.json"
        if manifest.exists():
            for name,spec in sorted(json.loads(manifest.read_text()).items()):
                path=run/spec["archive"]
                assert sha256(path)==spec["archive_sha256"],(run.name,name,"compressed hash")
                digest=hashlib.sha256();size=0;lines=0
                with gzip.open(path,"rb") as stream:
                    for chunk in iter(lambda:stream.read(1024*1024),b""):
                        digest.update(chunk);size+=len(chunk);lines+=chunk.count(b"\n")
                assert digest.hexdigest()==spec["original_sha256"],(run.name,name,"original hash")
                assert size==spec["original_bytes"],(run.name,name,"original bytes")
                stem="natural_structured" if name.startswith("natural_structured") else Path(name).stem
                summary=run/(stem+"_summary.json")
                if summary.exists():
                    expected_rows=sum(r["horizon"] for r in json.loads(summary.read_text()))
                    assert lines==expected_rows,(run.name,name,lines,expected_rows)
                record["archives"].append({"path":str(path.relative_to(root)),"records":lines,
                                           "original_sha256":digest.hexdigest(),"archive_sha256":spec["archive_sha256"]})
        results.append(record)
    report={"scope":"Completed local runs only; verifies recorded source/checkpoint/archive hashes and summary-based conversational trace counts. Does not establish scientific validity, remote persistence, or completeness of files without recorded hashes.",
            "frozen_files_verified":len(frozen["files"]),"analysis_source_sha256":sha256(Path(__file__).resolve()),
            "completed_runs":results,"unfinished_runs_excluded":unfinished}
    destination=root/"reports/tables/artifact_integrity.json"
    destination.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"completed_runs_audited":len(results),"unfinished_excluded":len(unfinished),
                      "source_files_verified":sum(r["source_files_verified"] for r in results),
                      "checkpoint_files_verified":sum(r["checkpoint_files_verified"] for r in results),
                      "archives_verified":sum(len(r["archives"]) for r in results)}))
    return report


if __name__=="__main__":audit(Path(__file__).resolve().parents[1])
