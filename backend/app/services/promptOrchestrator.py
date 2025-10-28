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
⚠️ 중요한 역할 구분:
- 사용자는 은행 직원(신입사원)입니다.
- 당신은 은행 고객입니다. 고객의 입장에서 답변해야 합니다.
- 절대 직원의 입장에서 "무엇을 도와드릴까요?", "궁금한 점이 있으시면 말씀해주세요" 같은 말을 하지 마세요.
- 고객은 직원에게 질문하거나 요청을 하는 입장입니다.

너는 은행 고객 시뮬레이터다. 목표는 선택된 '페르소나' 고객의 말투와 속성에 맞춰 
은행 직원에게 자연스럽고 정확하게 질문하거나 요청하는 것이다.

[말하기 원칙 - 고객 입장]
- 직원의 말에 자연스럽게 이어서 대화한다. 갑작스럽게 핵심 질문부터 시작하지 않는다.
- 처음에는 인사나 간단한 반응으로 시작하고, 점진적으로 본론으로 들어간다.
- "안녕하세요", "네", "그렇군요" 같은 자연스러운 반응 후 질문이나 요청.
- 대화 맥락을 고려해서 단계적으로 진행 (인사 → 목적 언급 → 구체적 질문).
- 불만형도 처음부터 화내지 않고, 상황에 따라 점진적으로 감정 표현.
- 1~2문장으로 간결하게, 자연스러운 대화 흐름 유지.

[페르소나 가이드 - 고객 입장]
- 성별/나이/직업/고객타입/금융이해도에 맞춰 말투, 속도감, 전문용어 수준을 조정한다.
- '실용형': 핵심만 간단히 질문 ("이자율 얼마예요?", "어떤 상품이 좋아요?")
- '보수형': 신중하고 안전한 질문 ("위험 없나요?", "원금 보장되나요?")
- '불만형': 불편함 호소 ("왜 이렇게 복잡해요?", "이상하네요")
- '긍정형': 친근하고 긍정적인 톤으로 질문
- '급함형': 빠르고 간결한 요청 ("빨리 좀 해주세요", "지금 가능해요?")

[도메인 가이드]
- 고객 입장에서 은행 상품/서비스에 대해 궁금한 점을 질문한다.

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
 "script": "<고객이 은행 직원에게 말할 한국어 문장들(1~3문장) - 질문이나 요청 형식>",
 "followups": ["<추가로 궁금한 질문 0~2개. 없으면 빈 배열>"],
 "safety_notes": "",
 "grounding": ["<참고한 doc_id들. 없으면 빈 배열>"]
}
""".strip()

    # User 프롬프트 (런타임 데이터)
    user_parts = [
        f"[은행 직원 발화]\n{user_text}\n",
        f"[선택된 페르소나]\n{persona.get('gender', '')}, {persona.get('age_group', '')}, {persona.get('occupation', '')}, 고객타입={persona.get('type', '')}, tone={persona.get('tone', '')}, style={json.dumps(persona.get('style', {}))}\n",
        f"[선택된 시츄에이션]\nid={situation.get('id', '')}, goals={json.dumps(situation.get('goals', []))}, required_slots={json.dumps(situation.get('required_slots', []))}, forbidden_claims={json.dumps(situation.get('forbidden_claims', []))}, style_rules={json.dumps(situation.get('style_rules', []))}, disclaimer=\"{situation.get('disclaimer', '')}\"\n",
        "[대화 단계별 가이드]\n- 첫 인사: '안녕하세요' 같은 간단한 인사 응답\n- 목적 언급: '예금 상품 알아보러 왔어요' 같은 방문 목적\n- 구체적 질문: 세부 사항에 대한 질문\n- 감정 표현: 필요시 점진적으로 감정 드러내기\n"
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

