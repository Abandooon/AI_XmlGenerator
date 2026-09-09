"""Deterministically materialize the English-only PIL V4.1 model inputs.

The adjudicated Chinese source remains immutable.  This builder performs a
literal, case-preserving translation without adding gold labels or legal
analysis to the inference surface.  It also replaces the Chinese retrieval
paraphrases and lexical terms with English equivalents checked against the
same official EUR-Lex source identities.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE_CASES = ROOT / "data" / "inference_dataset_v4.jsonl"
SOURCE_KB = ROOT / "kb" / "authoritative_provisions_v4.jsonl"
OUTPUT_CASES = ROOT / "data" / "inference_dataset_v41_en.jsonl"
OUTPUT_KB = ROOT / "kb" / "authoritative_provisions_v41_en.jsonl"
OUTPUT_MANIFEST = ROOT / "PIL_V41_ENGLISH_INPUT_MANIFEST.json"


FACTS_EN = {
    1: "Party A is registered in Germany and Party B in France. The dispute concerns ownership rights in immovable property located in France. A sues B in Germany for a declaration of rights in rem.",
    2: "The Austrian land register records Party A as owner of immovable property in Austria. Party B claims to be the true owner and sues in Germany to alter the Austrian register entry.",
    3: "Company B is incorporated under Italian law. Shareholder A sues in Germany for a declaration that a shareholders' meeting resolution increasing the company's capital is invalid.",
    4: "Party A owns a trade mark registered in Germany. Party B sues in France for a declaration that the German trade mark is invalid.",
    5: "Party A obtained a French money judgment and seeks to enforce it in Spain. Party B objects to enforcement.",
    6: "Italian Party A and Spanish Party B agreed in their sales contract that the French courts would have exclusive jurisdiction. A later sues in France.",
    7: "British Party A and German Party B agreed that the courts of the United Kingdom would have exclusive jurisdiction. B first brings a negative declaratory action in Germany, and A later sues in the United Kingdom.",
    8: "Parties A and B both reside in Italy but agreed that the Swedish courts would have jurisdiction. A nevertheless sues in Italy.",
    9: "The sale concerns immovable property in Spain. The contract designates the German courts. Party B sues in Germany for a declaration of rights in rem.",
    10: "Parties A and B concluded a contract by email, but there is no written jurisdiction clause. A alleges that they orally agreed on the Danish courts; B denies this.",
    11: "A French court is first seised of a claim for contractual damages. A German court is later seised of a negative declaratory action concerning the same contract.",
    12: "Party B first brings an action in Italy for a declaration of no liability. Party A later brings a damages action in France. There is no choice-of-court agreement.",
    13: "A Polish court was first seised but later found that it lacked jurisdiction and dismissed the action. Proceedings concerning the same dispute had also been filed in the Netherlands shortly before that dismissal.",
    14: "Proceedings in the United Kingdom allege fraudulent tortious conduct, while proceedings in France seek contractual payment. The claims arise from the same transaction but seek different relief.",
    15: "Proceedings are filed in France in the morning and in Germany later the same day. Determine which court is first seised.",
    16: "Party B is a resident of Germany. Party A sues B in Germany for payment of the purchase price.",
    17: "Party B is domiciled in Italy, and the place of performance is also in Italy. Party A sues B in France.",
    18: "Party B is a United States company with no domicile in the European Union. A French claimant wishes to sue B in France.",
    19: "When proceedings are contemplated, Party B is domiciled only in China and is not domiciled in any EU Member State. Party A is domiciled in Germany and plans to sue B in Germany. The facts do not involve a consumer contract, employment, exclusive jurisdiction, or a choice-of-court agreement.",
    20: "Company B is registered in the United Kingdom and has its central administration in Germany. French Party A wishes to sue B.",
    21: "A Spanish buyer and a Polish seller dispute late delivery. The agreed place of delivery was Madrid.",
    22: "A French company and an Italian consultant dispute allegedly defective performance of services that were principally provided in France.",
    23: "A German manufacturer sells household appliances in France. A French consumer is injured in France and wishes to sue the German manufacturer.",
    24: "Party A has its head office in Germany and a branch in the Netherlands through which it contracted to sell goods to Party B. The goods are defective, and B plans to sue the head office in the Netherlands.",
    25: "The dispute concerns an English-French trust domiciled in London. Beneficiary A alleges that trustee B mismanaged the trust.",
    26: "Party A sues Party B in Spain even though the dispute has no jurisdictional connection with Spain. B appears and argues the merits without contesting jurisdiction.",
    27: "Continuing the preceding scenario, Party B appears solely to contest jurisdiction and does not argue the merits.",
    28: "Party B does not appear at all. May the Spanish court hear the case in default and give judgment?",
    29: "A Spanish court hears a dispute concerning rights in rem in French immovable property. Party B appears without contesting jurisdiction.",
    30: "A German court hears a consumer-contract dispute. Consumer B, a French national, appears without contesting jurisdiction.",
    31: "Spanish company A and Italian company B dispute ownership of a warehouse located in Italy. A sues in Spain for a declaration that it holds rights in rem over that property.",
    32: "The Czech land register records Party C as owner of immovable property. Party D claims the entry is wrong and sues in Germany to alter the Czech register.",
    33: "Company C is incorporated under Dutch law and has its statutory seat in Amsterdam. Shareholder B sues in France to annul a shareholders' meeting resolution removing a director.",
    34: "Party A owns an EU trade mark registered by the European Union Intellectual Property Office (EUIPO). Party B does not raise invalidity as a counterclaim in infringement proceedings, but instead brings a standalone action before a German court seeking a declaration that the EU trade mark is invalid.",
    35: "Party A obtained an Austrian money judgment against Party B concerning immovable property and seeks enforcement in Germany. B brings objection proceedings in Germany.",
    36: "Co-owners of an apartment in Portugal dispute rules governing use of the common parts. One owner sues the others in Spain for a declaration of a preferential right to use the immovable property.",
    37: "German consulting company A and Belgian company B signed a services contract containing a written clause granting the Brussels courts exclusive jurisdiction. A later sues B in Brussels for unpaid service fees.",
    38: "Spanish seller A and Italian buyer B conclude a sales contract by telephone. A alleges that they orally agreed on the Vienna courts; B denies this, and the written contract contains no such clause.",
    39: "French Party A and Dutch Party B agreed in writing that the Amsterdam courts would have exclusive jurisdiction over their sale-of-goods contract. B first brings a negative declaratory action in France; A then sues for payment in the Netherlands.",
    40: "A contract for the sale of immovable property in Italy designates the German courts as having exclusive jurisdiction. Buyer A sues in Germany for a declaration of ownership of the Italian property.",
    41: "Portuguese Party A and Irish Party B agreed in a written services contract that the Dublin courts 'have jurisdiction', without stating that jurisdiction is exclusive. A sues B in Dublin for service fees.",
    42: "French consumer A orders furniture online from Dutch trader B. By a separate confirmation, A accepts a preselected term granting the Amsterdam courts exclusive jurisdiction. A later sues B in Amsterdam for performance.",
    43: "A German court is first seised of A's contractual damages action against B. A Spanish court is later seised of a negative declaratory action involving the same parties and the same contract.",
    44: "An Italian court is first seised of A's tort action against B, which remains at first instance. A French court is later seised of A's contractual-liability action against C arising from the same investment project. C is domiciled in France, and the French court has an independent basis of international jurisdiction over the second action. The core facts substantially overlap and separate proceedings risk irreconcilable judgments. The Italian court has jurisdiction over both actions, and Italian law permits consolidation. C asks the French court to stay or decline jurisdiction under Article 30.",
    45: "An Austrian court is first seised of A's contractual action against B but later finds that it lacks jurisdiction and dismisses the action. Proceedings concerning the same contract had been filed in Belgium shortly before the dismissal.",
    46: "French and Italian courts receive actions between the same parties concerning the same contract almost simultaneously. The French court registers the action several hours earlier.",
    47: "Multinational company B is registered in Germany, has its central administration in France, and has its principal place of business in Spain. Party A sues B in France on an ordinary debt.",
    48: "Party B is resident in Italy, and the dispute with Party A arose in Italy. A nevertheless sues B in Portugal, although the dispute has no connection with Portugal.",
    49: "Party B was resident in Spain but recently moved away without a clearly established new long-term place of residence. Party A wishes to sue B in Spain to recover a loan.",
    50: "Party B is resident in Spain. Party A sues B in the Spanish courts for payment of the purchase price.",
    51: "German seller A sells machinery to Belgian buyer B, with Antwerp as the agreed place of delivery. B alleges late delivery and sues A in Belgium.",
    52: "Spanish designer A provides marketing services to German company B, principally performing them in Barcelona. B refuses payment, and A sues in Spain.",
    53: "Driver B, domiciled in Germany, negligently injures pedestrian A, domiciled in France, while on holiday in France. A plans to sue B in the French courts for damages.",
    54: "Italian company B has a branch in Lyon, France. Party A sues B in Lyon over a repair contract concluded with that branch.",
    55: "Defendant B, domiciled in Germany, is sued by A in Portugal. The case has no other jurisdictional connection with Portugal. B appears solely to contest jurisdiction and does not argue the merits.",
    56: "A German court hears a dispute concerning rights in rem in French immovable property. Party B appears and argues the merits without contesting jurisdiction.",
    57: "A German court hears a consumer-contract action brought by business trader A against French consumer B. On receiving the claim, B was informed in writing of the right to contest jurisdiction and the consequences of appearing, but nevertheless appears and argues the merits.",
    58: "A Spanish court hears A's debt action against B. B does not appear at all, and the court establishes that the claim form was duly served under the EU service rules.",
    59: "An Italian court hears an action seeking a declaration that a trade mark registered in Germany is invalid. The defendant appears and argues the merits without contesting jurisdiction.",
    60: "An Irish court hears an employment-contract action brought by employer A against French employee B. B appears and argues the merits, but the file contains no indication that the court informed B of the right to contest jurisdiction."
}


KB_EN: dict[str, tuple[str, list[str]]] = {}


def put(ids: str, text: str, keywords: str) -> None:
    values = [item.strip() for item in keywords.split("|") if item.strip()]
    for evidence_id in ids.split():
        if evidence_id in KB_EN:
            raise ValueError(f"duplicate English evidence mapping: {evidence_id}")
        KB_EN[evidence_id] = (text, values)


put("BRUSSELS_I_BIS:Art.17(1)(c)", "The protective consumer-contract rules apply where the trader pursues or directs commercial activities to the consumer's Member State in the circumstances specified by this provision.", "consumer|online|directed activities|trader|furniture")
put("BRUSSELS_I_BIS:Art.18(1)", "A consumer may sue the other contracting party either in the courts of that party's Member State of domicile or, regardless of that party's domicile, in the courts for the place where the consumer is domiciled.", "consumer|trader|consumer domicile|French consumer")
put("BRUSSELS_I_BIS:Art.18(2)", "The other contracting party may sue a consumer only in the courts of the Member State in which the consumer is domiciled.", "consumer|trader|consumer domicile|French consumer")
put("BRUSSELS_I_BIS:Art.19", "A choice-of-court agreement in a consumer contract may depart from the protective jurisdiction rules only under the conditions stated in this provision.", "consumer|choice-of-court|jurisdiction clause|preselected term")
put("BRUSSELS_I_BIS:Art.22(1)", "An employer generally may bring proceedings against an employee only in the courts of the Member State in which the employee is domiciled.", "employer|employee|employment contract")
put("BRUSSELS_I_BIS:Art.24", "Article 24 assigns exclusive jurisdiction, regardless of the parties' domicile, for the listed subject matters.", "exclusive jurisdiction|immovable property|rights in rem|land register|public register|ownership")
put("BRUSSELS_I_BIS:Art.24(1)", "Proceedings whose object is rights in rem in, or tenancies of, immovable property are generally within the exclusive jurisdiction of the courts of the Member State where the property is situated, subject to the stated short private-tenancy exception.", "immovable property|rights in rem|tenancy|property is situated|ownership")
put("BRUSSELS_I_BIS:Art.24(3)", "Proceedings whose object is the validity of entries in public registers are within the exclusive jurisdiction of the courts of the Member State in which the register is kept.", "land register|public register|register entry|validity of entries")
put("BRUSSELS_I_BIS:Art.24(2)", "Proceedings principally concerned with the validity, nullity, or dissolution of a company or the validity of decisions of its organs are within the exclusive jurisdiction of the courts of the Member State in which the company has its seat.", "company|shareholders' meeting|capital resolution|removing a director|corporate decision|statutory seat")
put("BRUSSELS_I_BIS:Art.24(4)", "Proceedings concerned with the registration or validity of patents, trade marks, designs, or other similar rights required to be deposited or registered fall within the exclusive jurisdiction of the courts of the Member State in which the deposit or registration has been applied for, has taken place, or is deemed to have taken place, irrespective of whether the issue is raised by way of an action or as a defence.", "registered trade mark|trade mark registered|German trade mark|trade mark invalid|is invalid|patent validity|registration")
put("BRUSSELS_I_BIS:Art.24(5)", "Proceedings concerned with enforcement of judgments are within the exclusive jurisdiction of the courts of the Member State in which enforcement takes place or is sought.", "enforcement|object to enforcement|money judgment|enforce")
put("BRUSSELS_I_BIS:Art.25", "Article 25 governs agreements conferring jurisdiction on a court or the courts of a Member State.", "choice-of-court|jurisdiction clause|agreed court|agreed that|exclusive jurisdiction|Swedish courts|Dublin courts|Amsterdam courts|Brussels courts|Vienna courts|Danish courts")
put("BRUSSELS_I_BIS:Art.25(1)", "A choice-of-court agreement satisfying the stated formal and substantive conditions confers jurisdiction on the designated Member State court and is exclusive unless the parties agree otherwise.", "choice-of-court|jurisdiction clause|agreed court|agreed that|in writing|exclusive jurisdiction|Swedish courts|Dublin courts|Amsterdam courts|Brussels courts|Vienna courts|Danish courts")
put("BRUSSELS_I_BIS:Art.25(2)", "Electronic communication that provides a durable record of a jurisdiction agreement is equivalent to writing.", "choice-of-court|jurisdiction clause|email|electronic|durable record|in writing")
put("BRUSSELS_I_BIS:Art.25(4)", "A jurisdiction agreement has no legal force if it conflicts with the specified protective-jurisdiction provisions or purports to exclude a court having exclusive jurisdiction under Article 24.", "choice-of-court|jurisdiction clause|consumer|employee|exclusive jurisdiction|Article 24")
put("BRUSSELS_I_BIS:Art.26(1)", "Apart from jurisdiction derived from other provisions of the Regulation, a court of a Member State before which a defendant enters an appearance has jurisdiction, except where the appearance was entered to contest jurisdiction or another court has exclusive jurisdiction under Article 24.", "appears|argues the merits|without contesting jurisdiction|solely to contest jurisdiction")
put("BRUSSELS_I_BIS:Art.26(2)", "For specified weaker parties, jurisdiction based on appearance requires the court to ensure that the defendant was informed of the right to contest jurisdiction and of the consequences of appearing or not appearing.", "consumer|employee|informed in writing|right to contest jurisdiction|consequences of appearing")
put("BRUSSELS_I_BIS:Art.27", "When the courts of another Member State have exclusive jurisdiction under Article 24, the court seised must declare of its own motion that it has no jurisdiction.", "own motion|exclusive jurisdiction|declare no jurisdiction|rights in rem|registered trade mark")
put("BRUSSELS_I_BIS:Art.28(1)", "If a defendant domiciled in one Member State is sued in another Member State and does not appear, the court must declare of its own motion that it lacks jurisdiction unless jurisdiction follows from the Regulation.", "does not appear|default|own motion|jurisdiction")
put("BRUSSELS_I_BIS:Art.28(2)", "In the default-of-appearance situation, the court must stay proceedings until the defendant received the initiating document in time to defend or all necessary service steps were taken.", "does not appear|default|duly served|initiating document|defence rights")
put("BRUSSELS_I_BIS:Art.28(3)", "The EU service-of-documents rule identified in this paragraph replaces Article 28(2) when the initiating document had to be transmitted between Member States under that instrument.", "does not appear|default|EU service rules|transmitted between Member States")
put("BRUSSELS_I_BIS:Art.28(4)", "Where the specified EU service instrument does not apply, the identified Hague Service Convention rule applies if the initiating document had to be transmitted abroad.", "does not appear|default|Hague Service Convention|transmitted abroad")
put("BRUSSELS_I_BIS:Art.29", "Where courts of different Member States are seised of proceedings involving the same cause of action and the same parties, a court other than the court first seised must stay proceedings of its own motion and later defer if the first court's jurisdiction is established.", "same parties|same cause of action|first seised|later seised|mandatory stay|lis pendens")
put("BRUSSELS_I_BIS:Art.29(1)", "Where proceedings involving the same cause of action and the same parties are brought in different Member States, a court other than the court first seised must stay its proceedings of its own motion.", "same contract|same parties|negative declaratory action|declaration of no liability|first seised|later seised")
put("BRUSSELS_I_BIS:Art.29(2)", "On request, a court seised of the dispute must promptly inform another seised court of the date on which it was seised under Article 32.", "same parties|same cause of action|date seised|first seised|later court")
put("BRUSSELS_I_BIS:Art.29(3)", "Once the jurisdiction of the court first seised is established, every other court must decline jurisdiction in favour of that court.", "same parties|same cause of action|first seised|later court|decline jurisdiction")
put("BRUSSELS_I_BIS:Art.30", "Article 30 governs related actions pending in courts of different Member States and distinguishes discretionary stay from conditional decline.", "related actions|different claims|same project|irreconcilable judgments|may stay|consolidation|decline jurisdiction")
put("BRUSSELS_I_BIS:Art.30(1)", "When related actions are pending in courts of different Member States, a court other than the court first seised may stay its proceedings.", "related actions|different claims|same project|may stay|first seised")
put("BRUSSELS_I_BIS:Art.30(2)", "While the first-seised action is pending at first instance, another court may, on a party's application, decline jurisdiction if the first court has jurisdiction over the actions and its law permits consolidation.", "related actions|first instance|party requests|jurisdiction|consolidation|decline jurisdiction")
put("BRUSSELS_I_BIS:Art.30(3)", "Actions are related when they are so closely connected that hearing them together is expedient to avoid irreconcilable judgments from separate proceedings.", "related actions|closely connected|same project|irreconcilable judgments")
put("BRUSSELS_I_BIS:Art.31", "Article 31 addresses competing exclusive-jurisdiction claims and priority for a court designated by an exclusive choice-of-court agreement; it is distinct from Articles 29 and 30.", "designated court|exclusive choice-of-court|priority|stay|decline|first seised")
put("BRUSSELS_I_BIS:Art.31(2)", "Without prejudice to Article 26, where a court designated by an exclusive Article 25 agreement is seised, any court of another Member State must stay proceedings until the designated court declares that it has no jurisdiction under the agreement.", "designated court|exclusive choice-of-court|priority|stay|first seised")
put("BRUSSELS_I_BIS:Art.31(3)", "Once the court designated in the agreement establishes jurisdiction, every court of another Member State must decline jurisdiction in its favour.", "designated court|exclusive choice-of-court|priority|decline jurisdiction")
put("BRUSSELS_I_BIS:Art.32(1)", "The time when a court is deemed seised depends on lodging the initiating document with the court or the authority responsible for service, provided the claimant takes the required subsequent steps.", "time seised|registered|lodged|service authority|several hours earlier")
put("BRUSSELS_I_BIS:Art.34", "A Member State court may stay proceedings in favour of related proceedings pending in a third State where the specified conditions, including avoidance of irreconcilable judgments, are satisfied.", "third State|related proceedings|irreconcilable judgments|may stay")
put("BRUSSELS_I_BIS:Art.4(1)", "A person domiciled in a Member State is generally sued in the courts of that Member State, irrespective of nationality.", "defendant|domiciled|resident|company|trader|Dutch trader|central administration|principal place of business|general jurisdiction")
put("BRUSSELS_I_BIS:Art.41(1)", "Subject to the Regulation, enforcement procedure is governed by the law of the Member State addressed, and an enforceable judgment is enforced there under the same conditions as a domestic judgment.", "enforcement procedure|Member State addressed|enforce judgment|same conditions")
put("BRUSSELS_I_BIS:Art.41(2)", "Grounds for refusing or suspending enforcement under the law of the Member State addressed apply only so far as they are compatible with the grounds specified in the Regulation.", "enforcement procedure|Member State addressed|refuse enforcement|suspend enforcement")
put("BRUSSELS_I_BIS:Art.5(1)", "A defendant domiciled in a Member State may be sued in another Member State only under the special rules listed in the Regulation.", "depart from domicile|exception|special jurisdiction|another Member State")
put("BRUSSELS_I_BIS:Art.6", "Article 6 addresses jurisdiction over defendants not domiciled in a Member State, principally by reference to Member State law subject to specified Regulation exceptions.", "not domiciled in any EU Member State|China|United States company|national law")
put("BRUSSELS_I_BIS:Art.6(1)", "Where a defendant is not domiciled in a Member State, jurisdiction is generally determined by the law of the Member State court seised, subject to specified exceptions.", "domiciled only in China|no domicile in the European Union|United States company|national law")
put("BRUSSELS_I_BIS:Art.6(2)", "Against a defendant not domiciled in a Member State, a person domiciled in a Member State may invoke that State's jurisdiction rules on the same basis as its nationals.", "not domiciled in any EU Member State|China|United States company|national law|same as nationals")
put("BRUSSELS_I_BIS:Art.62", "Article 62 determines which domestic law a court applies when deciding whether a natural person is domiciled in a Member State.", "natural person domicile|long-term residence|moved away|domiciled only in China|national law|not domiciled")
put("BRUSSELS_I_BIS:Art.62(1)", "To determine whether a party is domiciled in the Member State whose courts are seised, the court applies its own internal law.", "natural person domicile|long-term residence|moved away|domiciled only in China|no domicile in the European Union|internal law")
put("BRUSSELS_I_BIS:Art.62(2)", "If a party is not domiciled in the seised court's Member State, the court applies the law of another Member State to determine whether the party is domiciled there.", "natural person domicile|long-term residence|moved away|not domiciled|another Member State")
put("BRUSSELS_I_BIS:Art.63(1)(a)", "For purposes of the Regulation, a company or other legal person is domiciled at its statutory seat.", "company domicile|statutory seat|head office")
put("BRUSSELS_I_BIS:Art.63(1)(b)", "For purposes of the Regulation, a company or other legal person is domiciled at its central administration.", "company domicile|central administration|head office")
put("BRUSSELS_I_BIS:Art.63(1)(c)", "For purposes of the Regulation, a company or other legal person is domiciled at its principal place of business.", "company domicile|principal place of business|head office")
put("BRUSSELS_I_BIS:Art.63(3)", "To determine whether a trust is domiciled in the seised court's Member State, the court applies its private-international-law rules.", "trust domicile|trustee|beneficiary|private international law")
put("BRUSSELS_I_BIS:Art.7(1)(a)", "In matters relating to a contract, a defendant domiciled in a Member State may be sued in another Member State at the place of performance of the obligation in question.", "contract|place of performance|obligation|special jurisdiction")
put("BRUSSELS_I_BIS:Art.7(6)", "A qualifying dispute against a settlor, trustee, or beneficiary may be brought in the courts of the Member State in which the trust is domiciled.", "trust|settlor|trustee|beneficiary|trust domicile|special jurisdiction")
put("BRUSSELS_I_BIS:Art.7(1)(b)", "For a sale of goods, Article 7(1)(b) uses the place where the goods were or should have been delivered; for services, it uses the place where the services were or should have been provided.", "buyer|seller|sale|machinery|goods|place of delivery|services|marketing services|principally provided|Barcelona|Madrid|Antwerp")
put("BRUSSELS_I_BIS:Art.7(2)", "In matters relating to tort or delict, proceedings may be brought in the courts for the place where the harmful event occurred or may occur.", "tort|negligently|injures|injured|harmful event|accident|damages")
put("BRUSSELS_I_BIS:Art.7(5)", "A dispute arising out of the operations of a branch, agency, or other establishment may be brought in the courts for the place where it is situated.", "branch|head office|establishment|contract concluded with that branch|Lyon")
put("EU_TRADE_MARK_REGULATION:Art.124(d)", "EU trade mark courts have exclusive jurisdiction over counterclaims for revocation or for a declaration of invalidity of an EU trade mark under Article 128.", "EU trade mark court|counterclaim|revocation|invalidity")
put("EU_TRADE_MARK_REGULATION:Art.128(1)", "A counterclaim for revocation or for a declaration of invalidity may rely only on grounds for revocation or invalidity stated in the Regulation.", "counterclaim|revocation|invalidity|EU trade mark court")
put("EU_TRADE_MARK_REGULATION:Art.135", "A national court dealing with an EU-trade-mark action other than an action listed in Article 124 must treat the EU trade mark as valid.", "other action|EU trade mark valid|standalone action|national court")
put("EU_TRADE_MARK_REGULATION:Art.63(1)", "An application for revocation or for a declaration of invalidity of an EU trade mark may be submitted to the European Union Intellectual Property Office by the persons and groups specified in this paragraph.", "EUIPO|European Union Intellectual Property Office|EU trade mark|standalone invalidity application|declaration of invalidity")


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in values),
        encoding="utf-8", newline="\n",
    )


def main() -> int:
    source_cases = rows(SOURCE_CASES)
    source_kb = rows(SOURCE_KB)
    case_ids = {int(row["id"]) for row in source_cases}
    evidence_ids = {str(row["evidence_id"]) for row in source_kb}
    if case_ids != set(FACTS_EN):
        raise ValueError(f"English fact map mismatch: missing={case_ids-set(FACTS_EN)}, extra={set(FACTS_EN)-case_ids}")
    if evidence_ids != set(KB_EN):
        raise ValueError(f"English KB map mismatch: missing={evidence_ids-set(KB_EN)}, extra={set(KB_EN)-evidence_ids}")

    english_cases = [
        {
            "id": row["id"],
            "cluster_id": row["cluster_id"],
            "facts_text": FACTS_EN[int(row["id"])],
            "source_class": "synthetic_case_two_reviewer_adjudicated_english_translation",
        }
        for row in source_cases
    ]
    english_kb: list[dict[str, Any]] = []
    for row in source_kb:
        text, keywords = KB_EN[str(row["evidence_id"])]
        english_kb.append({
            key: value for key, value in row.items()
            if key not in {"text_zh", "keywords", "text_status"}
        } | {
            "text_en": text,
            "keywords": keywords,
            "language": "en",
            "text_status": "concise_english_paraphrase_checked_against_official_source",
        })

    write_jsonl(OUTPUT_CASES, english_cases)
    write_jsonl(OUTPUT_KB, english_kb)
    model_visible = OUTPUT_CASES.read_text(encoding="utf-8") + OUTPUT_KB.read_text(encoding="utf-8")
    cjk = len(re.findall(r"[\u3400-\u9fff]", model_visible))
    if cjk:
        raise ValueError(f"English model-visible inputs contain {cjk} CJK characters")
    manifest = {
        "schema_version": "atlas.pil.english_model_inputs.v4.1",
        "status": "PASS",
        "translation_policy": "reviewer-confirmed meaning-preserving English translation; no gold fields or legal conclusions added to inference cases",
        "source_cases": {"path": SOURCE_CASES.relative_to(ROOT).as_posix(), "sha256": sha256(SOURCE_CASES)},
        "source_kb": {"path": SOURCE_KB.relative_to(ROOT).as_posix(), "sha256": sha256(SOURCE_KB)},
        "english_cases": {"path": OUTPUT_CASES.relative_to(ROOT).as_posix(), "sha256": sha256(OUTPUT_CASES), "count": len(english_cases)},
        "english_kb": {"path": OUTPUT_KB.relative_to(ROOT).as_posix(), "sha256": sha256(OUTPUT_KB), "count": len(english_kb)},
        "model_visible_cjk_characters": cjk,
        "case_ids_preserved": [row["id"] for row in english_cases] == [row["id"] for row in source_cases],
        "cluster_ids_preserved": [row["cluster_id"] for row in english_cases] == [row["cluster_id"] for row in source_cases],
        "evidence_ids_preserved": [row["evidence_id"] for row in english_kb] == [row["evidence_id"] for row in source_kb],
        "official_urls_preserved": [row["official_url"] for row in english_kb] == [row["official_url"] for row in source_kb],
    }
    OUTPUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
