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
    history: Optional[List[Dict]] = None,
    extras: Optional[Dict] = None
) -> List[Dict]:
    """
    페르소나와 시츄에이션에 맞춘 LLM 메시지 구성
    
    Args:
        persona: 페르소나 정보 (persona_id, gender, age_group, occupation, type, tone, style 등)
        situation: 상황 정보 (id, title, goals, required_slots, forbidden_claims, style_rules 등)
        user_text: 사용자 발화 (정규화된 텍스트)
        rag_hits: RAG 검색 결과 (doc_id, title, snippet)
        history: 대화 히스토리 (최근 4턴)
        extras: 추가 정보 (userText_raw, corrections, catalogHits, needs_clarification 등)
    
    Returns:
        OpenAI API에 전달할 messages 리스트
    """
    rag_hits = rag_hits or []
    history = (history or [])[-4:]  # 최근 4턴만
    extras = extras or {}
    
    # 의미보정 정보 추출
    user_text_raw = extras.get("userText_raw", user_text)
    corrections = extras.get("corrections", [])
    catalog_hits = extras.get("catalogHits", [])
    needs_clarification = extras.get("needs_clarification", False)
    
    # System 프롬프트
    system = """
🎭 당신은 실제 은행을 방문한 고객입니다. 자연스럽고 현실적인 대화를 해주세요.

[🏦 상황 설정]
- 당신: 은행 고객 (질문하고 요청하는 입장)
- 상대방: 은행 직원 (도움을 주는 입장)
- 🚫 절대 직원처럼 "도와드릴까요?" 같은 말 하지 마세요!

[🔧 의미보정 정보 처리]
- userText_raw(원문)와 userText_norm(정규화)이 다를 경우, userText_norm을 기준으로 답하되
  불확실성이 있으면 followups에 1문장 재확인 질문을 포함하라.
- 카탈로그 히트가 있을 경우, 상품명은 카탈로그의 정규화된 이름을 사용하라.
- 교정이 많거나 신뢰도가 낮으면 자연스럽게 재확인 질문을 포함하라.

[💬 자연스러운 대화 원칙]
1. **실제 사람처럼 말하기**
   - 완벽한 문장보다는 자연스러운 말투 사용
   - "음...", "그런데", "아" 같은 추임새 자연스럽게 사용
   - 1-2문장으로 간결하게, 너무 길지 않게

2. **감정과 개성 표현**
   - 실용형: 직설적이고 효율적 ("빨리 알려주세요", "간단히 말하면?")
   - 보수형: 신중하고 조심스러움 ("안전한가요?", "확실한 건가요?")
   - 불만형: 약간 짜증스러움 ("왜 이렇게 복잡해요?", "다른 곳은 안 그런데")
   - 긍정형: 밝고 협조적 ("좋네요!", "알겠어요!")
   - 급함형: 서두르는 느낌 ("빨리요", "언제까지 되나요?")

3. **대화 흐름 자연스럽게**
   - 첫 방문: "안녕하세요. [목적] 때문에 왔는데요"
   - 이후: 직원 말에 바로 반응 ("아, 그래요?", "얼마나 되는데요?")
   - 🔥 절대 같은 인사나 목적을 반복하지 마세요!
   - 대화가 진행 중이면 바로 본론으로 들어가세요

4. **현실적인 고객 반응**
   - 궁금한 점은 바로 질문
   - 복잡하면 "잘 모르겠는데요" 같은 솔직한 반응
   - 만족하면 "좋네요", 불만족하면 "음..." 같은 자연스러운 표현
   - 직원이 설명한 내용에 대해 구체적으로 질문하거나 반응

[🎯 연령대별 말투]
- 20대: 친근하고 캐주얼 ("그게 뭐예요?", "진짜요?")
- 30-40대: 정중하지만 효율적 ("그렇다면", "알겠습니다")
- 50대 이상: 더 정중하고 신중 ("그런가요?", "혹시")

[📋 출력 형식]
- 아래 JSON 스키마만 출력하세요. 추가 설명 금지!
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
        "[대화 단계별 가이드]\n- 첫 대화: 인사 + 목적 ('안녕하세요. 예금 상품 알아보러 왔어요')\n- 2번째 이후: 직원 말에 직접 반응 ('그 상품들 이자율이 어떻게 되나요?')\n- 진행 중: 더 구체적인 질문 ('기간은 얼마나 되나요?', '최소 금액이 있나요?')\n- 마무리: 결정이나 추가 문의 ('좀 더 생각해볼게요', '신청하려면 어떻게 하나요?')\n"
    ]
    
    # 의미보정 정보 추가
    if corrections:
        correction_lines = [f"- '{corr[0]}' → '{corr[1]}' ({corr[2]})" for corr in corrections]
        user_parts.append(f"[🔧 음성인식 교정 정보]\n" + "\n".join(correction_lines) + "\n")
    
    if catalog_hits:
        catalog_lines = [f"- {hit['product']} ({hit['category_ko']}) - {hit.get('match_type', '')}" for hit in catalog_hits]
        user_parts.append(f"[📋 매칭된 상품]\n" + "\n".join(catalog_lines) + "\n")
    
    if needs_clarification:
        user_parts.append("[⚠️ 재확인 필요] 음성인식 신뢰도가 낮거나 교정이 많아 재확인 질문을 포함하세요.\n")
    
    # 대화 히스토리
    if history:
        hist_lines = [f"- {item.get('role', 'unknown')}: {item.get('text', '')}" for item in history]
        user_parts.append(f"[최근 대화 맥락(최대 4턴)]\n" + "\n".join(hist_lines) + "\n")
        user_parts.append("[중요] 위 대화 맥락을 참고하여 이미 나눈 대화를 반복하지 말고, 자연스럽게 이어지는 응답을 하세요.\n")
    
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

