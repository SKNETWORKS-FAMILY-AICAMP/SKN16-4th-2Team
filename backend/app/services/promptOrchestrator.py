"""
프롬프트 오케스트레이터
페르소나 + 시츄에이션 + 대화 히스토리 + RAG 기반 자연스러운 고객 응답 생성
"""
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def compose_llm_messages(
    persona: Dict,
    situation: Dict,
    user_text: str,
    rag_hits: Optional[List[Dict]] = None,
    history: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    페르소나와 시츄에이션에 맞춘 LLM 메시지 구성
    
    Args:
        persona: 페르소나 정보 (persona_id, gender, age_group, occupation, type, tone, style 등)
        situation: 상황 정보 (id, title, goals, required_slots, forbidden_claims, style_rules 등)
        user_text: 사용자 발화
        rag_hits: RAG 검색 결과 (doc_id, title, snippet)
        history: 대화 히스토리 (최근 4턴)
    
    Returns:
        OpenAI API에 전달할 messages 리스트
    """
    rag_hits = rag_hits or []
    history = (history or [])[-4:]  # 최근 4턴만
    
    # System 프롬프트
    system = """
너는 은행 고객 응대 시뮬레이터다. 목표는 사용자의 의도를 빠르게 파악하고, 
선택된 '페르소나'의 말투와 속성에 맞춰 자연스럽고 정확하게 대답하는 것이다.

[말하기 원칙]
- 시나리오 없이, 사용자 발화를 우선한다. 불필요한 가정/추측을 줄이고, 필요한 경우에만 짧게 확인 질문을 한다.
- 숫자/수수료/기간 등은 예시로만 제시하고, 확정처럼 말하지 않는다.
- 모르는 정보나 지점별로 다른 내용은 "확인 후 안내"라고 명확히 말한다.
- 불만형: [공감→요약→해결옵션→재확인], 급함형: [간결→절차→주의], 보수형: [차분→상세→안전] 구조를 따른다.
- 답변은 2~4문장 이내로 간결하게. 필요한 경우 질문 1~2개로 슬롯을 채운다.

[페르소나 가이드]
- 성별/나이/직업/고객타입/금융이해도에 맞춰 말투, 속도감, 전문용어 수준을 조정한다.
- '실용형'은 결론과 절차, '보수형'은 안정감 있는 설명, '불만형'은 공감과 복구옵션, 
  '긍정형'은 긍정적 피드백, '급함형'은 짧고 빠른 안내를 우선한다.

[도메인 가이드]
- Situation에 적힌 goals/required_slots/style_rules/forbidden_claims를 지켜라.

[근거 사용]
- 제공된 RAG 스니펫이 있을 때만 수치/절차를 인용한다. 출처 문서 id를 내부적으로 추적하고, 
  출력 JSON의 grounding 배열에 doc_id를 넣는다(문장 내 출처 표시는 생략).

[출력 형식]
- 아래 developer 메시지의 JSON 스키마만 출력한다.
""".strip()

    # Developer 프롬프트 (출력 스키마)
    developer = """
다음 JSON만 출력한다. 여분 텍스트나 설명을 절대 추가하지 마라.
{
 "script": "<고객에게 말할 한국어 문장들(2~4문장)>",
 "followups": ["<슬롯 보완용 추가 질문 0~2개>"],
 "safety_notes": "<주의/면책 한 줄. 없으면 빈 문자열>",
 "grounding": ["<참고한 doc_id들. 없으면 빈 배열>"]
}
""".strip()

    # User 프롬프트 (런타임 데이터)
    user_parts = [
        f"[사용자 발화]\n{user_text}\n",
        f"[선택된 페르소나]\n{persona.get('gender', '')}, {persona.get('age_group', '')}, {persona.get('occupation', '')}, 고객타입={persona.get('type', '')}, tone={persona.get('tone', '')}, style={json.dumps(persona.get('style', {}))}\n",
        f"[선택된 시츄에이션]\nid={situation.get('id', '')}, goals={json.dumps(situation.get('goals', []))}, required_slots={json.dumps(situation.get('required_slots', []))}, forbidden_claims={json.dumps(situation.get('forbidden_claims', []))}, style_rules={json.dumps(situation.get('style_rules', []))}, disclaimer=\"{situation.get('disclaimer', '')}\"\n",
    ]
    
    # 대화 히스토리
    if history:
        hist_lines = [f"- {item.get('role', 'unknown')}: {item.get('text', '')}" for item in history]
        user_parts.append(f"[최근 대화(최대 4턴)]\n" + "\n".join(hist_lines) + "\n")
    
    # RAG 검색 결과
    if rag_hits:
        rag_lines = [f"({i+1}) [{hit.get('doc_id', '')}] {hit.get('title', '')}: {hit.get('snippet', '')}" 
                    for i, hit in enumerate(rag_hits)]
        user_parts.append(f"[사실 근거(RAG 스니펫, 0~{len(rag_hits)}개)]\n" + "\n".join(rag_lines))
    
    user = "\n".join(user_parts).strip()
    
    # System + Developer 프롬프트를 하나로 합침
    system_full = f"{system}\n\n{developer}"
    
    messages = [
        {"role": "system", "content": system_full},
        {"role": "user", "content": user}
    ]
    
    return messages


def parse_llm_response(content: str) -> Dict:
    """
    LLM 응답을 파싱하여 {script, followups, safety_notes, grounding} 반환
    """
    try:
        # JSON 추출 (```json``` 블록 제거)
        content_clean = content.strip()
        if content_clean.startswith("```"):
            content_clean = content_clean.split("```")[1]
            if content_clean.startswith("json"):
                content_clean = content_clean[4:]
        content_clean = content_clean.strip()
        
        parsed = json.loads(content_clean)
        return {
            "script": parsed.get("script", ""),
            "followups": parsed.get("followups", []),
            "safety_notes": parsed.get("safety_notes", ""),
            "grounding": parsed.get("grounding", [])
        }
    except json.JSONDecodeError as e:
        print(f"LLM 응답 파싱 실패: {e}")
        print(f"응답 내용: {content[:200]}")
        # 폴백: 첫 번째 문단을 script로 사용
        first_line = content.split('\n')[0].strip()
        return {
            "script": first_line if first_line else "네, 이해했습니다.",
            "followups": [],
            "safety_notes": "",
            "grounding": []
        }


def to_ssml(script: str, age_group: str) -> str:
    """
    script를 SSML로 변환 (나이대별 속도/음성 조정)
    """
    rate_map = {
        "20s": "1.05",
        "30s": "1.0",
        "40s": "0.95",
        "50s": "0.90",
        "60s 이상": "0.85"
    }
    pitch_map = {
        "20s": "+1st",
        "30s": "0st",
        "40s": "-1st",
        "50s": "-1st",
        "60s 이상": "-2st"
    }
    
    rate = rate_map.get(age_group, "1.0")
    pitch = pitch_map.get(age_group, "0st")
    
    # 줄바꿈을 pause로 변환
    script_cleaned = script.replace('\n', '<break time="200ms"/>')
    
    return f'<speak><prosody rate="{rate}" pitch="{pitch}">{script_cleaned}</prosody></speak>'


def get_situation_defaults(situation_id: str) -> Dict:
    """
    시츄에이션 기본값 반환
    """
    defaults = {
        "deposit": {
            "id": "deposit",
            "title": "수신 상담",
            "goals": ["고객 요구사항 파악", "적합한 상품 제안", "절차 안내"],
            "required_slots": ["목적", "금액", "기간"],
            "forbidden_claims": ["원금 보장", "수익률 보장"],
            "style_rules": ["수익률은 참고용 예시로만", "실제 수익률은 차등 적용"],
            "disclaimer": "실제 수익률은 상품 조건과 시장 상황에 따라 달라질 수 있습니다."
        },
        "loan": {
            "id": "loan",
            "title": "여신 상담",
            "goals": ["대출 목적 확인", "신용도 파악", "가능한 한도 안내"],
            "required_slots": ["목적", "직업", "소득"],
            "forbidden_claims": ["심사 통과 보장", "확정 금리 보장"],
            "style_rules": ["한도/금리는 심사 결과에 따름", "필요 서류 안내"],
            "disclaimer": "대출 한도 및 금리는 심사 결과에 따라 달라질 수 있습니다."
        },
        "card": {
            "id": "card",
            "title": "카드 상담",
            "goals": ["카드 용도 파악", "적합한 혜택 제안"],
            "required_slots": ["사용 목적", "월 사용 금액"],
            "forbidden_claims": ["승인 보장"],
            "style_rules": ["혜택은 카드 종류별 상이", "연회비 안내"],
            "disclaimer": "카드 승인은 신용평가에 따라 달라질 수 있습니다."
        },
        "fx": {
            "id": "fx",
            "title": "외환/송금 상담",
            "goals": ["송금 목적 확인", "수수료 안내", "절차 설명"],
            "required_slots": ["송금 국가", "금액"],
            "forbidden_claims": ["환율 보장"],
            "style_rules": ["환율은 변동 가능", "추가 서류 확인 필요 여부 안내"],
            "disclaimer": "환율은 환전 시점의 시장 환율이 적용됩니다."
        },
        "digital": {
            "id": "digital",
            "title": "디지털 뱅킹 상담",
            "goals": ["문제 파악", "해결 방법 안내", "FAQ 제공"],
            "required_slots": ["문제 유형", "기기 종류"],
            "forbidden_claims": ["해결 보장"],
            "style_rules": ["단계별 안내", "스크린샷 추천"],
            "disclaimer": "문제가 지속되면 고객센터로 문의해주세요."
        },
        "complaint": {
            "id": "complaint",
            "title": "민원 처리",
            "goals": ["문제 상황 파악", "공감", "해결 방안 제시"],
            "required_slots": ["문제 내용", "발생 시점"],
            "forbidden_claims": ["빠른 해결 보장"],
            "style_rules": ["공감 표현 우선", "상세 기록 필요"],
            "disclaimer": "민원은 처리 절차에 따라 시간이 소요될 수 있습니다."
        }
    }
    
    return defaults.get(situation_id, defaults["deposit"])

