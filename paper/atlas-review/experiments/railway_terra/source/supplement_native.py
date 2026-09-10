"""Independent scoring on the exact artifact files emitted by the pipeline."""
from pathlib import Path
import hashlib,json,uuid
from raw_native_score import run_native,score_native_receipt

HERE=Path(__file__).resolve().parent
JAVA=HERE/"workspace/native_validation/toolchain/jdk8/jdk8u504-b01/bin/java.exe"
LIB=HERE/"workspace/native_validation/legacy_build/native-verifier/build/native-dist/lib"
EVIDENCE=HERE/"native_evidence"

def evaluate_artifact_files(xmi_path,identity_path,public,native=None):
    del native
    xmi_path,identity_path=Path(xmi_path),Path(identity_path)
    before=hashlib.sha256(xmi_path.read_bytes()).hexdigest()
    directory=EVIDENCE/(before[:16]+"_"+uuid.uuid4().hex[:12]); directory.mkdir(parents=True)
    receipt=run_native(xmi_path,identity_path,directory/"native.json",JAVA,LIB)
    score=score_native_receipt(receipt,public)
    score.update(artifact_sha256=before,native_receipt=receipt,source="ORIGINAL_XMI_NATIVE_REPLAY",native_evidence=str(directory),
                 identity_sha256=hashlib.sha256(identity_path.read_bytes()).hexdigest())
    (directory/"score.json").write_text(json.dumps(score,ensure_ascii=False,indent=2),encoding="utf-8")
    return score
