"""
RAG 기반 시뮬레이션 서비스
제공된 데이터를 활용한 STT/LLM/TTS 기반 음성 시뮬레이션
"""
import json
import os
import tempfile
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlmodel import Session, select
import openai
from pathlib import Path

from app.models.user import User
from app.services.promptOrchestrator import (
    compose_llm_messages,
    parse_llm_response,
    get_situation_defaults
)
from app.services.banking_normalizer import normalize_text, expand_search_query


class RAGSimulationService:
    """RAG 기반 시뮬레이션 서비스"""
    
    def __init__(self, session: Session):
        self.session = session
        # OpenAI 클라이언트 초기화 (API 키가 있을 때만)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                print(f"OpenAI 클라이언트 초기화 실패: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
        
        # 데이터 파일 경로 설정 (Docker 컨테이너 내부 경로)
        self.data_path = Path("/app/data")
        
        # 데이터 캐시
        self.personas_cache = None
        self.situations_cache = None
        self.product_catalog = None
    
    def load_simulation_data(self):
        """시뮬레이션 데이터 로드"""
        try:
            print(f"📁 데이터 경로 확인: {self.data_path}")
            print(f"📁 디렉토리 존재 여부: {self.data_path.exists()}")
            
            if not self.data_path.exists():
                print(f"❌ 데이터 디렉토리가 존재하지 않습니다: {self.data_path}")
                return
            
            # 페르소나 데이터 로드 (새로운 JSON 형식)
            personas_file = self.data_path / "personas_new.json"
            print(f"📄 페르소나 파일 경로: {personas_file}")
            print(f"📄 페르소나 파일 존재 여부: {personas_file.exists()}")
            
            if personas_file.exists():
                with open(personas_file, 'r', encoding='utf-8') as f:
                    personas_data = json.load(f)
                    if 'personas' in personas_data:
                        self.personas_cache = personas_data['personas']
                    else:
                        self.personas_cache = personas_data if isinstance(personas_data, list) else []
            else:
                print("❌ 페르소나 파일을 찾을 수 없습니다")
            
            # 상황 데이터 로드 (새로운 JSON 형식)
            situations_file = self.data_path / "situations_new.json"
            print(f"📄 상황 파일 경로: {situations_file}")
            print(f"📄 상황 파일 존재 여부: {situations_file.exists()}")
            
            if situations_file.exists():
                with open(situations_file, 'r', encoding='utf-8') as f:
                    situations_data = json.load(f)
                    if 'situations' in situations_data:
                        self.situations_cache = situations_data['situations']
                    else:
                        self.situations_cache = situations_data if isinstance(situations_data, list) else []
            else:
                print("❌ 상황 파일을 찾을 수 없습니다")
            
            # 상품 카탈로그 로드
            catalog_file = self.data_path / "product_catalog.json"
            print(f"📄 카탈로그 파일 경로: {catalog_file}")
            print(f"📄 카탈로그 파일 존재 여부: {catalog_file.exists()}")
            
            if catalog_file.exists():
                with open(catalog_file, 'r', encoding='utf-8') as f:
                    self.product_catalog = json.load(f)
                    print(f"✅ 상품 카탈로그 로드됨: {len(self.product_catalog.get('products', []))}개 상품")
            else:
                print("❌ 상품 카탈로그 파일을 찾을 수 없습니다")
                self.product_catalog = {"products": [], "categories": {}}
            
            print(f"✅ 데이터 로드 완료: 페르소나 {len(self.personas_cache) if self.personas_cache else 0}개, "
                  f"상황 {len(self.situations_cache) if self.situations_cache else 0}개, "
                  f"상품 {len(self.product_catalog.get('products', []))}개")
            
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def get_personas(self, filters: Optional[Dict] = None) -> List[Dict]:
        """페르소나 목록 조회"""
        if not self.personas_cache:
            print("📊 페르소나 데이터 로딩 중...")
            self.load_simulation_data()
        
        if not self.personas_cache:
            print("❌ 페르소나 데이터가 없습니다.")
            return []
        
        personas = self.personas_cache
        
        if filters:
            # age_group 필터
            if filters.get("age_group"):
                personas = [p for p in personas if p.get("age_group") == filters["age_group"]]
            
            # occupation 필터 - 영어 키워드 매핑
            if filters.get("occupation"):
                occupation_map = {
                    "student": "학생",
                    "employee": "직장인",
                    "self_employed": "자영업자",
                    "retired": "은퇴자",
                    "foreigner": "외국인"
                }
                occupation_keyword = occupation_map.get(filters["occupation"], filters["occupation"])
                personas = [p for p in personas if occupation_keyword in p.get("occupation", "")]
            
            # type 필터 - 영어 키워드 매핑
            if filters.get("type"):
                type_map = {
                    "practical": "실용형",
                    "conservative": "보수형",
                    "angry": "불만형",
                    "positive": "긍정형",
                    "impatient": "급함형"
                }
                type_keyword = type_map.get(filters["type"], filters["type"])
                personas = [p for p in personas if type_keyword in p.get("type", "")]
            
            # gender 필터 - 성별 매핑
            if filters.get("gender"):
                gender_map = {
                    "male": "남성",
                    "female": "여성"
                }
                gender_keyword = gender_map.get(filters["gender"], filters["gender"])
                personas = [p for p in personas if p.get("gender") == gender_keyword]
        
        print(f"✅ 페르소나 {len(personas)}개 반환")
        return personas
    
    def normalize_user_text(self, text: str, confidence: float = 1.0) -> Dict:
        """사용자 텍스트를 은행 도메인에 맞게 정규화합니다."""
        try:
            result = normalize_text(text, confidence)
            return {
                "original": result.original,
                "normalized": result.normalized,
                "corrections": result.corrections,
                "needs_clarification": result.needs_clarification,
                "extracted_entities": result.extracted_entities
            }
        except Exception as e:
            print(f"❌ 텍스트 정규화 실패: {e}")
            return {
                "original": text,
                "normalized": text,
                "corrections": [],
                "needs_clarification": False,
                "extracted_entities": {}
            }
    
    def match_product_catalog(self, normalized_text: str) -> List[Dict]:
        """정규화된 텍스트로 상품 카탈로그를 매칭합니다."""
        if not self.product_catalog or not self.product_catalog.get("products"):
            return []
        
        matched_products = []
        products = self.product_catalog["products"]
        
        for product in products:
            # 상품명 직접 매칭
            if product["name"] in normalized_text:
                matched_products.append({
                    "product": product["name"],
                    "code": product["code"],
                    "category": product["category"],
                    "category_ko": product["category_ko"],
                    "match_type": "exact_name"
                })
                continue
            
            # 키워드 매칭
            keywords = product.get("keywords", [])
            for keyword in keywords:
                if keyword in normalized_text:
                    matched_products.append({
                        "product": product["name"],
                        "code": product["code"],
                        "category": product["category"],
                        "category_ko": product["category_ko"],
                        "match_type": "keyword",
                        "matched_keyword": keyword
                    })
                    break
        
        return matched_products
    
    def expand_search_query(self, normalized_text: str, catalog_hits: List[Dict] = None) -> List[str]:
        """검색 쿼리를 확장합니다."""
        try:
            return expand_search_query(normalized_text, catalog_hits)
        except Exception as e:
            print(f"❌ 쿼리 확장 실패: {e}")
            return [normalized_text]
    
    def get_business_categories(self) -> List[Dict]:
        """비즈니스 카테고리 목록 조회"""
        if not self.situations_cache:
            self.load_simulation_data()
        
        if not self.situations_cache:
            return []
        
        # 카테고리 추출
        categories = []
        seen_categories = set()
        
        for situation in self.situations_cache:
            title = situation.get('title', '')
            category_id = situation.get('id', '')
            
            # 카테고리 이름 추출 (예: "수신 (예금, 적금, 자동이체)" -> "수신")
            if '(' in title:
                category_name = title.split('(')[0].strip()
            else:
                category_name = title
            
            if category_name not in seen_categories:
                categories.append({
                    "id": category_id,
                    "name": category_name,
                    "title": title
                })
                seen_categories.add(category_name)
        
        return categories
    
    def get_situations(self, filters: Optional[Dict] = None) -> List[Dict]:
        """상황 목록 조회"""
        if not self.situations_cache:
            self.load_simulation_data()
        
        if not self.situations_cache:
            return []
        
        situations = self.situations_cache
        
        if filters:
            if filters.get("category"):
                # 상황 데이터에서 category 필드가 없으므로 id 필드로 매칭
                category = filters["category"]
                situations = [s for s in situations if s.get("id") == category or s.get("category") == category]
        
        return situations
    
    def start_voice_simulation(self, user_id: int, persona_id: str, situation_id: str, gender: str = 'male') -> Dict:
        """음성 시뮬레이션 시작"""
        # 데이터가 없으면 로드
        if not self.personas_cache or not self.situations_cache:
            self.load_simulation_data()
        
        # 페르소나와 상황 조회
        persona = None
        situation = None
        
        if self.personas_cache:
            persona = next((p for p in self.personas_cache if p.get("persona_id") == persona_id), None)
            print(f"페르소나 조회: {persona_id} -> {persona is not None}")
        
        if self.situations_cache:
            situation = next((s for s in self.situations_cache if s.get("id") == situation_id), None)
            print(f"상황 조회: {situation_id} -> {situation is not None}")
        
        # 페르소나를 찾지 못했으면 첫 번째 페르소나 사용
        if not persona and self.personas_cache:
            persona = self.personas_cache[0]
            print(f"⚠️ 페르소나 {persona_id}를 찾지 못해 첫 번째 페르소나 사용: {persona.get('persona_id')}")
        
        # 상황을 찾지 못했으면 첫 번째 상황 사용
        if not situation and self.situations_cache:
            situation = self.situations_cache[0]
            print(f"⚠️ 상황 {situation_id}를 찾지 못해 첫 번째 상황 사용: {situation.get('id')}")
        
        if not persona:
            raise ValueError(f"페르소나를 찾을 수 없습니다: {persona_id}")
        
        if not situation:
            raise ValueError(f"상황을 찾을 수 없습니다: {situation_id}")
        
        # 성별 정보는 이미 페르소나 데이터에 포함되어 있으므로 추가하지 않음
        
        # 초기 고객 메시지 생성
        initial_message_data = self._generate_initial_customer_message(persona, situation)
        
        # TTS로 음성 생성
        initial_text = initial_message_data.get("text", "안녕하세요, 도움이 필요합니다.")
        initial_audio = self._text_to_speech(initial_text, persona)
        
        initial_message = {
            "type": "customer",
            "content": initial_text,
            "audio_url": initial_audio
        }
        
        return {
            "session_id": f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "persona": {
                "id": persona["persona_id"],
                "name": persona.get("persona_id", "Unknown"),
                "age_group": persona.get("age_group", ""),
                "occupation": persona.get("occupation", ""),
                "type": persona.get("type", ""),
                "tone": persona.get("tone", "neutral"),
                "style": persona.get("style", {}),
                "sample_utterances": persona.get("sample_utterances", [])
            },
            "situation": {
                "id": situation["id"],
                "title": situation.get("title", ""),
                "category": situation.get("category", "general"),
                "goals": situation.get("goals", []),
                "scenarios": situation.get("scenarios", [])
            },
            "initial_message": initial_message
        }
    
    def process_voice_interaction(self, session_data: Dict, audio_data: bytes, 
                                user_message: str = "") -> Dict:
        """음성 상호작용 처리"""
        try:
            print(f"음성 상호작용 처리 시작: session_data keys = {list(session_data.keys())}")
            
            if not session_data or "persona" not in session_data:
                raise ValueError("세션 데이터가 올바르지 않습니다.")
                
            persona = session_data["persona"]
            situation = session_data.get("situation", session_data.get("scenario", {}))
            
            print(f"페르소나: {persona.get('persona_id', persona.get('id', 'Unknown'))}")
            print(f"상황: {situation.get('id', situation.get('scenario_id', 'Unknown'))}")
            
            # 페르소나와 상황 정보를 실제 데이터에서 조회
            persona_id = persona.get('persona_id', persona.get('id', ''))
            situation_id = situation.get('id', situation.get('scenario_id', ''))
            
            # 실제 페르소나와 상황 데이터 조회
            actual_persona = None
            actual_situation = None
            
            if self.personas_cache and persona_id:
                actual_persona = next((p for p in self.personas_cache if p.get("persona_id") == persona_id), None)
                if actual_persona:
                    print(f"실제 페르소나 데이터 조회 성공: {persona_id}")
                else:
                    print(f"실제 페르소나 데이터 조회 실패: {persona_id}")
            
            if self.situations_cache and situation_id:
                actual_situation = next((s for s in self.situations_cache if s.get("id") == situation_id), None)
                if actual_situation:
                    print(f"실제 상황 데이터 조회 성공: {situation_id}")
                else:
                    print(f"실제 상황 데이터 조회 실패: {situation_id}")
            
            # STT: 음성을 텍스트로 변환 (사용자가 제공한 텍스트가 있으면 우선 사용)
            if not user_message:
                print(f"STT 처리 시작: 오디오 크기 {len(audio_data) if audio_data else 0} bytes")
                transcribed_text = self._speech_to_text(audio_data)
            else:
                print(f"텍스트 입력: '{user_message}'")
                transcribed_text = user_message
            
            print(f"최종 텍스트: '{transcribed_text}'")
            
            # 1. 의미 보정: STT 결과를 은행 도메인에 맞게 정규화
            print("🔧 의미 보정 시작")
            normalize_result = self.normalize_user_text(transcribed_text, confidence=0.9)
            normalized_text = normalize_result["normalized"]
            corrections = normalize_result["corrections"]
            needs_clarification = normalize_result["needs_clarification"]
            
            print(f"원본: '{normalize_result['original']}'")
            print(f"정규화: '{normalized_text}'")
            print(f"교정: {corrections}")
            print(f"재확인 필요: {needs_clarification}")
            
            # 2. 상품 카탈로그 매칭
            print("📋 상품 카탈로그 매칭 시작")
            catalog_hits = self.match_product_catalog(normalized_text)
            print(f"카탈로그 매칭 결과: {len(catalog_hits)}개")
            for hit in catalog_hits:
                print(f"  - {hit['product']} ({hit['category_ko']})")
            
            # 3. RAG 검색 쿼리 확장
            print("🔍 RAG 검색 쿼리 확장")
            expanded_queries = self.expand_search_query(normalized_text, catalog_hits)
            print(f"확장된 쿼리: {expanded_queries}")
            
            # 고객 응답 생성 (프롬프트 오케스트레이터 사용)
            print("고객 응답 생성 시작")
            
            # 실제 페르소나와 상황 데이터 사용
            response_persona = actual_persona if actual_persona else persona
            response_situation = actual_situation if actual_situation else situation
            
            # 상황 정보 추출 (또는 기본값 사용)
            final_situation = response_situation
            if not final_situation or not final_situation.get('id'):
                # 기본값 사용
                final_situation = get_situation_defaults('deposit')
            else:
                # 상황 기본 구조 확보
                final_situation = {
                    'id': final_situation.get('id', 'deposit'),
                    'title': final_situation.get('title', '상담'),
                    'goals': final_situation.get('goals', ['고객 요구사항 파악', '핵심 정보 안내']),
                    'required_slots': final_situation.get('required_slots', []),
                    'forbidden_claims': final_situation.get('forbidden_claims', []),
                    'style_rules': final_situation.get('style_rules', ['숫자는 예시로만', '확인 후 안내']),
                    'disclaimer': final_situation.get('disclaimer', '실제 조건은 정책에 따라 달라질 수 있습니다.')
                }
            
            # 대화 히스토리 구성 (세션 데이터에서 추출 및 누적)
            conversation_history = session_data.get("conversation_history", [])
            
            # 초기 메시지가 있고 히스토리가 비어있으면 추가
            if session_data.get("initial_message") and not conversation_history:
                initial_msg = session_data["initial_message"]
                conversation_history.append({
                    "role": "customer", 
                    "text": initial_msg.get("content", ""),
                    "timestamp": datetime.now().isoformat()
                })
            
            # 현재 직원 발화를 히스토리에 추가
            conversation_history.append({
                "role": "employee", 
                "text": transcribed_text,
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"대화 히스토리: {len(conversation_history)}턴")
            for i, msg in enumerate(conversation_history[-4:]):
                print(f"  {i+1}. {msg.get('role', 'unknown')}: {msg.get('text', '')[:50]}...")
            
            # 프롬프트 오케스트레이터로 메시지 구성
            messages = compose_llm_messages(
                persona=response_persona,
                situation=final_situation,
                user_text=normalized_text,  # 정규화된 텍스트 사용
                rag_hits=[],  # TODO: RAG 검색 결과 추가
                history=conversation_history[-4:],  # 최근 4턴만 전달
                extras={
                    "userText_raw": transcribed_text,  # 원본 텍스트
                    "corrections": corrections,  # 교정 정보
                    "catalogHits": catalog_hits,  # 카탈로그 매칭 결과
                    "needs_clarification": needs_clarification,  # 재확인 필요 여부
                    "expanded_queries": expanded_queries  # 확장된 검색 쿼리
                }
            )
            
            # OpenAI API 호출
            llm_response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
                max_tokens=500
            )
            
            # LLM 응답 파싱
            content = llm_response.choices[0].message.content
            parsed = parse_llm_response(content)
            
            print(f"고객 응답 (script): '{parsed.get('script', '')}'")
            
            # 고객 응답을 히스토리에 추가
            customer_response_text = parsed.get('script', '')
            conversation_history.append({
                "role": "customer",
                "text": customer_response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # TTS: 고객 응답을 음성으로 변환
            print(f"TTS 처리 시작")
            customer_audio = self._text_to_speech(customer_response_text, response_persona)
            print(f"TTS 완료: 오디오 길이 {len(customer_audio) if customer_audio else 0}")
            
            # 응답 평가
            evaluation = self._evaluate_user_response(transcribed_text, actual_persona or persona, actual_situation or situation)
            
            result = {
                "transcribed_text": transcribed_text,
                "customer_response": customer_response_text,
                "customer_audio": customer_audio,
                "feedback": evaluation,
                "followups": parsed.get('followups', []),
                "safety_notes": parsed.get('safety_notes', ''),
                "conversation_phase": "ongoing",
                "session_score": self._calculate_session_score(session_data),
                "conversation_history": conversation_history  # 업데이트된 히스토리 포함
            }
            
            print("음성 상호작용 처리 완료")
            return result
            
        except Exception as e:
            print(f"음성 상호작용 처리 오류: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _speech_to_text(self, audio_data: bytes) -> str:
        """음성을 텍스트로 변환 (STT) - whisper-1 사용"""
        if not self.openai_client:
            return "OpenAI API 키가 설정되지 않았습니다."
            
        if not audio_data:
            return "오디오 데이터가 없습니다."

        try:
            # OpenAI Whisper API 사용
            # 다양한 오디오 형식 지원
            audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
            audio_file.write(audio_data)
            audio_file.close()
            
            print(f"STT 처리: 오디오 파일 크기 {len(audio_data)} bytes")
            
            with open(audio_file.name, "rb") as f:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="ko"  # 한국어 설정
                )
            
            os.unlink(audio_file.name)
            print(f"STT 성공: '{transcript.text}'")
            return transcript.text
            
        except Exception as e:
            print(f"STT 오류: {e}")
            import traceback
            traceback.print_exc()
            return "음성 인식에 실패했습니다."
    
    def _text_to_speech(self, text: str, persona: Dict) -> str:
        """텍스트를 음성으로 변환 (TTS) - gpt-4o-mini-tts 사용"""
        if not self.openai_client:
            print("TTS 오류: OpenAI 클라이언트가 초기화되지 않았습니다.")
            return ""
            
        if not text:
            print("TTS 오류: 변환할 텍스트가 없습니다.")
            return ""
            
        try:
            print(f"TTS 시작: '{text[:50]}...'")
            
            # 페르소나에 따른 음성 특성 설정
            voice_characteristics = self._get_voice_characteristics(persona)
            print(f"TTS 음성 특성: {voice_characteristics}")
            
            # OpenAI TTS API 사용
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice_characteristics.get("voice", "alloy"),
                speed=voice_characteristics.get("speed", 1.0),
                input=text
            )
            
            # 음성 파일을 base64로 인코딩하여 반환
            audio_data = response.content
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            print(f"TTS 성공: 오디오 크기 {len(audio_data)} bytes, Base64 길이 {len(audio_base64)}")
            
            return f"data:audio/mpeg;base64,{audio_base64}"
            
        except Exception as e:
            print(f"TTS 오류: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _get_voice_characteristics(self, persona: Dict) -> Dict:
        """페르소나에 따른 음성 특성 설정 (성별, 나이대, 고객타입 기반)"""
        customer_type = persona.get("type", "실용형")
        age_group = persona.get("age_group", "30대")
        gender = persona.get("gender", "남성")
        
        # 성별 판단
        is_female = (gender == "여성" or gender == "female")
        
        print(f"🎤 페르소나 음성 설정: {gender} {age_group} {customer_type}")
        
        # 고객 타입별 음성 톤 매핑
        tone_map = {
            "실용형": "direct",
            "보수형": "calm",
            "불만형": "tense", 
            "긍정형": "cheerful",
            "급함형": "urgent"
        }
        
        tone = tone_map.get(customer_type, "neutral")
        
        # 성별 + 나이대 + 톤별 음성 선택
        if is_female:
            # 여성 음성: nova(차분), shimmer(밝음)
            if age_group in ["20대", "30대"]:
                voice_map = {
                    "direct": "shimmer",    # 젊고 직설적
                    "calm": "nova",         # 차분하고 신중
                    "tense": "shimmer",     # 약간 날카로운 톤
                    "cheerful": "shimmer",  # 밝고 긍정적
                    "urgent": "shimmer",    # 빠르고 급한
                    "neutral": "nova"
                }
            else:  # 40대 이상
                voice_map = {
                    "direct": "nova",       # 성숙하고 직설적
                    "calm": "nova",         # 차분하고 신중
                    "tense": "nova",        # 차분하지만 불만
                    "cheerful": "nova",     # 따뜻하고 긍정적
                    "urgent": "shimmer",    # 급한 상황
                    "neutral": "nova"
                }
        else:
            # 남성 음성: alloy(중성적), echo(깊음), fable(따뜻함)
            if age_group in ["20대", "30대"]:
                voice_map = {
                    "direct": "alloy",      # 젊고 직설적
                    "calm": "echo",         # 차분하고 깊은
                    "tense": "fable",       # 약간 거친 톤
                    "cheerful": "fable",    # 밝고 친근한
                    "urgent": "alloy",      # 빠르고 급한
                    "neutral": "alloy"
                }
            else:  # 40대 이상
                voice_map = {
                    "direct": "echo",       # 성숙하고 직설적
                    "calm": "echo",         # 차분하고 신중
                    "tense": "fable",       # 불만스러운 톤
                    "cheerful": "fable",    # 따뜻하고 긍정적
                    "urgent": "alloy",      # 급한 상황
                    "neutral": "echo"
                }
        
        # 고객 타입별 말하기 속도
        speed_map = {
            "direct": 1.1,      # 실용형: 빠르게
            "calm": 0.9,        # 보수형: 천천히
            "tense": 1.0,       # 불만형: 보통
            "cheerful": 1.1,    # 긍정형: 밝게 빠르게
            "urgent": 1.3,      # 급함형: 매우 빠르게
            "neutral": 1.0
        }
        
        voice = voice_map.get(tone, "alloy")
        
        return {
            "voice": voice,
            "speed": speed_map.get(tone, 1.0)
        }
    
    def _generate_initial_customer_message(self, persona: Dict, situation: Dict) -> Dict:
        """초기 고객 메시지 생성"""
        sample_utterances = persona.get("sample_utterances", [])
        
        # RAG 기반 초기 메시지 생성
        rag_context = self._get_rag_context(situation)
        
        prompt = f"""
        당신은 {persona.get('persona_id', 'Unknown')} 고객입니다.
        
        고객 정보:
        - 연령대: {persona.get('age_group', '')}
        - 직업: {persona.get('occupation', '')}
        - 금융 이해도: {persona.get('financial_literacy', '')}
        - 성격: {persona.get('type', '')}
        - 톤: {persona.get('tone', 'neutral')}
        - 말하기 스타일: {persona.get('style', {})}
        - 예시 발화: {sample_utterances}
        
        상황: {situation.get('title', '')}
        
        RAG 컨텍스트:
        {rag_context}
        
        업무 카테고리: {situation.get('category', situation.get('title', '')).split(' ')[0]}
        세부 상황: {situation.get('goals', [])}
        고객의 요구사항: {situation.get('title', '')}
        
        이 상황에서 고객이 은행 직원에게 처음으로 말할 내용을 생성해주세요.
        - 고객의 성격과 상황에 맞는 자연스러운 대화
        - 업무 카테고리와 세부 상황에 맞는 구체적인 질문이나 요청
        - 한 문장으로 간결하게
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            
            return {
                "text": response.choices[0].message.content,
                "phase": "initial"
            }
            
        except Exception as e:
            print(f"초기 메시지 생성 오류: {e}")
            return {
                "text": sample_utterances[0] if sample_utterances else "안녕하세요, 도움이 필요합니다.",
                "phase": "initial"
            }
    
    def _generate_customer_response_with_rag(self, user_message: str, persona: Dict, 
                                           situation: Dict) -> Dict:
        """RAG 기반 고객 응답 생성"""
        # RAG 컨텍스트 생성
        rag_context = self._get_rag_context(situation)
        
        # 페르소나 특성 추출
        persona_traits = self._extract_persona_traits(persona)
        
        prompt = f"""
        당신은 {persona.get('persona_id', 'Unknown')} 고객입니다.
        
        고객 특성:
        {persona_traits}
        
        상황: {situation.get('title', '')}
        대화 플로우: {situation.get('scenarios', [])}
        
        RAG 컨텍스트:
        {rag_context}
        
        은행 직원이 "{user_message}"라고 말했습니다.
        
        이 상황에서 고객이 자연스럽게 응답할 내용을 생성해주세요.
        고객의 성격과 상황에 맞는 반응을 보여주세요.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            
            return {
                "text": response.choices[0].message.content,
                "phase": self._determine_conversation_phase(situation)
            }
            
        except Exception as e:
            print(f"고객 응답 생성 오류: {e}")
            return {
                "text": "네, 이해했습니다.",
                "phase": "ongoing"
            }
    
    def _get_rag_context(self, situation: Dict) -> str:
        """상황 기반 RAG 컨텍스트 생성"""
        context_parts = []
        
        # 상황 정보
        context_parts.append(f"상황: {situation.get('title', '')}")
        
        # 상황 세부 정보
        context_parts.append(f"\n업무 상황:")
        context_parts.append(f"- 카테고리: {situation.get('category', '')}")
        context_parts.append(f"- 목표: {situation.get('goals', [])}")
        context_parts.append(f"- 시나리오: {situation.get('scenarios', [])}")
        
        # 추가 정보 (필요시)
        if situation.get('required_slots'):
            context_parts.append(f"\n필요 정보: {situation.get('required_slots', [])}")
        if situation.get('style_rules'):
            context_parts.append(f"\n스타일 규칙: {situation.get('style_rules', [])}")
        
        return "\n".join(context_parts)
    
    def _extract_persona_traits(self, persona: Dict) -> str:
        """페르소나 특성 추출"""
        traits = []
        
        traits.append(f"- 연령대: {persona.get('age_group', '')}")
        traits.append(f"- 직업: {persona.get('occupation', '')}")
        traits.append(f"- 금융 이해도: {persona.get('financial_literacy', '')}")
        traits.append(f"- 고객 타입: {persona.get('type', '')}")
        traits.append(f"- 톤: {persona.get('tone', 'neutral')}")
        
        style = persona.get('style', {})
        if style:
            traits.append(f"- 말하기 스타일: {style}")
        
        notes = persona.get('notes', '')
        if notes:
            traits.append(f"- 특이사항: {notes}")
        
        sample_utterances = persona.get('sample_utterances', [])
        if sample_utterances:
            traits.append(f"- 예시 발화: {sample_utterances}")
        
        return "\n".join(traits)
    
    def _determine_conversation_phase(self, situation: Dict) -> str:
        """대화 단계 결정"""
        scenarios = situation.get('scenarios', [])
        
        if len(scenarios) <= 2:
            return "initial"
        elif len(scenarios) <= 4:
            return "developing"
        else:
            return "concluding"
    
    def _evaluate_user_response(self, user_message: str, persona: Dict, situation: Dict) -> str:
        """사용자 응답 평가"""
        scenarios = situation.get('scenarios', [])
        
        if not scenarios:
            return "평가 기준이 없습니다."
        
        # 시나리오를 문자열로 변환
        scenarios_text = "\n".join([
            f"- {scenario}"
            for scenario in scenarios
        ])
        
        prompt = f"""
        은행 직원의 응답: "{user_message}"
        
        고객 정보:
        - 고객 타입: {persona.get('type', '')}
        - 금융 이해도: {persona.get('financial_literacy', '')}
        - 톤: {persona.get('tone', 'neutral')}
        
        시나리오:
        {scenarios_text}
        
        이 응답이 고객에게 적절했는지 평가하고, 개선점이 있다면 피드백을 제공해주세요.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"응답 평가 오류: {e}")
            return "응답 평가를 완료할 수 없습니다."
    
    def _calculate_session_score(self, session_data: Dict) -> float:
        """세션 점수 계산 (임시 구현)"""
        # 실제로는 대화 기록을 기반으로 점수를 계산해야 함
        return 75.0
