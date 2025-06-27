# test_real_constraints.py
import asyncio
import aiohttp
import json
import time


async def check_constraint_application():
    """测试真实约束效果"""

    print("🧪 Testing Real Constraint Effectiveness...")

    # 测试用例：不同约束级别
    test_cases = [
        {
            "name": "No Constraints",
            "constraint_info": {
                "gbnf_enabled": False,
                "fsm_enabled": False
            }
        },
        {
            "name": "GBNF Only",
            "constraint_info": {
                "gbnf_enabled": True,
                "fsm_enabled": False,
                "grammar_rules": "start ::= element\nelement ::= \"<AUTOSAR>\" content \"</AUTOSAR>\"\ncontent ::= [a-zA-Z0-9\\s<>/=-]+"
            }
        },
        {
            "name": "FSM Only",
            "constraint_info": {
                "gbnf_enabled": False,
                "fsm_enabled": True,
                "allowed_tokens": ["AUTOSAR", "AR-PACKAGES", "APPLICATION-SW-COMPONENT-TYPE", "SHORT-NAME"]
            }
        },
        {
            "name": "Full Constraints",
            "constraint_info": {
                "gbnf_enabled": True,
                "fsm_enabled": True,
                "grammar_rules": "start ::= element\nelement ::= \"<AUTOSAR>\" content \"</AUTOSAR>\"\ncontent ::= [a-zA-Z0-9\\s<>/=-]+",
                "allowed_tokens": ["AUTOSAR", "AR-PACKAGES", "APPLICATION-SW-COMPONENT-TYPE", "SHORT-NAME"]
            }
        }
    ]

    results = []

    async with aiohttp.ClientSession() as session:
        for case in test_cases:
            print(f"\n🔬 Testing: {case['name']}")

            request_data = {
                "request_id": f"test-{case['name'].lower().replace(' ', '-')}",
                "prompt": "Generate AUTOSAR battery monitor component",
                "constraint_info": case["constraint_info"],
                "autosar_context": {"domain": "test"},
                "max_tokens": 500,
                "temperature": 0.3
            }

            start_time = time.time()

            try:
                async with session.post(
                        "http://117.50.190.248:8002/enhanced_generate",
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    result = await resp.json()

                    end_time = time.time()

                    if result.get("success"):
                        xml_content = result.get("generated_xml", "")
                        constraints_applied = result.get("constraints_applied", {})
                        violations = result.get("constraint_violations", [])

                        print(f"  ✅ Success: {len(xml_content)} chars")
                        print(f"  🎯 Constraints Applied: {constraints_applied}")
                        print(f"  ⚠️ Violations: {len(violations)}")
                        print(f"  ⏱️ Time: {end_time - start_time:.2f}s")

                        results.append({
                            "case": case["name"],
                            "success": True,
                            "xml_length": len(xml_content),
                            "constraints_applied": constraints_applied,
                            "violations": violations,
                            "generation_time": end_time - start_time,
                            "effectiveness_score": sum(constraints_applied.values()) / max(len(constraints_applied), 1)
                        })
                    else:
                        print(f"  ❌ Failed: {result.get('error_message', 'Unknown error')}")
                        results.append({
                            "case": case["name"],
                            "success": False,
                            "error": result.get("error_message", "Unknown error")
                        })

            except Exception as e:
                print(f"  💥 Exception: {e}")
                results.append({
                    "case": case["name"],
                    "success": False,
                    "error": str(e)
                })

    # 生成约束效果报告
    print(f"\n📊 Constraint Effectiveness Report")
    print("=" * 60)

    for result in results:
        if result["success"]:
            print(f"\n{result['case']}:")
            print(f"  XML Length: {result['xml_length']} chars")
            print(f"  Constraints Applied: {result['constraints_applied']}")
            print(f"  Violations: {len(result['violations'])}")
            print(f"  Generation Time: {result['generation_time']:.2f}s")
            print(f"  Effectiveness Score: {result['effectiveness_score']:.2f}")
        else:
            print(f"\n{result['case']}: ❌ {result['error']}")

    return results


if __name__ == "__main__":
    asyncio.run(check_constraint_application())