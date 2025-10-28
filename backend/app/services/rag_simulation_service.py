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
        self.scenarios_cache = None
        self.situations_cache = None
    
    def load_simulation_data(self):
        """시뮬레이션 데이터 로드"""
        try:
            print(f"📁 데이터 경로 확인: {self.data_path}")
            print(f"📁 디렉토리 존재 여부: {self.data_path.exists()}")
            
            if not self.data_path.exists():
                print(f"❌ 데이터 디렉토리가 존재하지 않습니다: {self.data_path}")
                return
            
            # 페르소나 데이터 로드
            personas_file = self.data_path / "personas_375.jsonl.txt"
            print(f"📄 페르소나 파일 경로: {personas_file}")
            print(f"📄 페르소나 파일 존재 여부: {personas_file.exists()}")
            
            if personas_file.exists():
                with open(personas_file, 'r', encoding='utf-8') as f:
                    self.personas_cache = [json.loads(line.strip()) for line in f if line.strip()]
            else:
                print("❌ 페르소나 파일을 찾을 수 없습니다")
            
            # 시나리오 데이터 로드
            scenarios_files = [
                "scenarios_easy_500.jsonl.txt",
                "scenarios_normal_500.jsonl.txt", 
                "scenarios_hard_500.jsonl.txt",
                "scenarios_100_expanded.jsonl.txt"
            ]
            
            self.scenarios_cache = []
            for filename in scenarios_files:
                scenarios_file = self.data_path / filename
                print(f"📄 시나리오 파일: {filename} - 존재: {scenarios_file.exists()}")
                if scenarios_file.exists():
                    with open(scenarios_file, 'r', encoding='utf-8') as f:
                        scenarios = [json.loads(line.strip()) for line in f if line.strip()]
                        self.scenarios_cache.extend(scenarios)
            
            # 상황 데이터 로드
            situations_file = self.data_path / "situations_200.jsonl.txt"
            print(f"📄 상황 파일 경로: {situations_file}")
            print(f"📄 상황 파일 존재 여부: {situations_file.exists()}")
            
            if situations_file.exists():
                with open(situations_file, 'r', encoding='utf-8') as f:
                    self.situations_cache = [json.loads(line.strip()) for line in f if line.strip()]
            else:
                print("❌ 상황 파일을 찾을 수 없습니다")
            
            print(f"✅ 데이터 로드 완료: 페르소나 {len(self.personas_cache) if self.personas_cache else 0}개, "
                  f"시나리오 {len(self.scenarios_cache) if self.scenarios_cache else 0}개, "
                  f"상황 {len(self.situations_cache) if self.situations_cache else 0}개")
            
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
    
    def get_scenarios(self, filters: Optional[Dict] = None) -> List[Dict]:
        """시나리오 목록 조회"""
        if not self.scenarios_cache:
            print("📊 시나리오 데이터 로딩 중...")
            self.load_simulation_data()
        
        if not self.scenarios_cache:
            print("❌ 시나리오 데이터가 없습니다.")
            return []
        
        scenarios = self.scenarios_cache
        
        if filters:
            # 카테고리 필터 - situation.category_ko에서 검색
            if filters.get("category"):
                category_filter = filters["category"]
                scenarios = [s for s in scenarios if (
                    s.get("situation", {}).get("category_ko", "") == category_filter or
                    category_filter in s.get("situation", {}).get("category_ko", "")
                )]
            
            # 난이도 필터
            if filters.get("difficulty"):
                scenarios = [s for s in scenarios if s.get("difficulty") == filters["difficulty"]]
            
            # 페르소나 필터
            if filters.get("persona"):
                scenarios = [s for s in scenarios if s.get("persona") == filters["persona"]]
        
        print(f"✅ 시나리오 {len(scenarios)}개 반환")
        return scenarios
    
    def get_situations(self, filters: Optional[Dict] = None) -> List[Dict]:
        """상황 목록 조회"""
        if not self.situations_cache:
            self.load_simulation_data()
        
        if not self.situations_cache:
            return []
        
        situations = self.situations_cache
        
        if filters:
            if filters.get("category"):
                situations = [s for s in situations if s.get("category") == filters["category"]]
        
        return situations
    
    def start_voice_simulation(self, user_id: int, persona_id: str, scenario_id: str, gender: str = 'male') -> Dict:
        """음성 시뮬레이션 시작"""
        # 데이터가 없으면 로드
        if not self.personas_cache or not self.scenarios_cache:
            self.load_simulation_data()
        
        # 페르소나와 시나리오 조회
        persona = None
        scenario = None
        
        if self.personas_cache:
            persona = next((p for p in self.personas_cache if p.get("persona_id") == persona_id), None)
            print(f"페르소나 조회: {persona_id} -> {persona is not None}")
        
        if self.scenarios_cache:
            scenario = next((s for s in self.scenarios_cache if s.get("scenario_id") == scenario_id), None)
            print(f"시나리오 조회: {scenario_id} -> {scenario is not None}")
        
        # 페르소나를 찾지 못했으면 첫 번째 페르소나 사용
        if not persona and self.personas_cache:
            persona = self.personas_cache[0]
            print(f"⚠️ 페르소나 {persona_id}를 찾지 못해 첫 번째 페르소나 사용: {persona.get('persona_id')}")
        
        # 시나리오를 찾지 못했으면 첫 번째 시나리오 사용
        if not scenario and self.scenarios_cache:
            scenario = self.scenarios_cache[0]
            print(f"⚠️ 시나리오 {scenario_id}를 찾지 못해 첫 번째 시나리오 사용: {scenario.get('scenario_id')}")
        
        if not persona:
            raise ValueError(f"페르소나를 찾을 수 없습니다: {persona_id}")
        
        if not scenario:
            raise ValueError(f"시나리오를 찾을 수 없습니다: {scenario_id}")
        
        # 성별 정보는 이미 페르소나 데이터에 포함되어 있으므로 추가하지 않음
        
        # 초기 고객 메시지 생성
        initial_message_data = self._generate_initial_customer_message(persona, scenario)
        
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
            "scenario": {
                "id": scenario["scenario_id"],
                "title": scenario.get("title", ""),
                "difficulty": scenario.get("difficulty", "easy"),
                "storyline": scenario.get("storyline", {}),
                "turn_blueprint": scenario.get("turn_blueprint", []),
                "evaluation_rubric": scenario.get("evaluation_rubric", [])
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
            scenario = session_data["scenario"]
            
            print(f"페르소나: {persona.get('persona_id', persona.get('id', 'Unknown'))}")
            print(f"시나리오: {scenario.get('scenario_id', scenario.get('id', 'Unknown'))}")
            
            # 페르소나와 시나리오 정보를 실제 데이터에서 조회
            persona_id = persona.get('persona_id', persona.get('id', ''))
            scenario_id = scenario.get('scenario_id', scenario.get('id', ''))
            
            # 실제 페르소나와 시나리오 데이터 조회
            actual_persona = None
            actual_scenario = None
            
            if self.personas_cache and persona_id:
                actual_persona = next((p for p in self.personas_cache if p.get("persona_id") == persona_id), None)
                if actual_persona:
                    print(f"실제 페르소나 데이터 조회 성공: {persona_id}")
                else:
                    print(f"실제 페르소나 데이터 조회 실패: {persona_id}")
            
            if self.scenarios_cache and scenario_id:
                actual_scenario = next((s for s in self.scenarios_cache if s.get("scenario_id") == scenario_id), None)
                if actual_scenario:
                    print(f"실제 시나리오 데이터 조회 성공: {scenario_id}")
                else:
                    print(f"실제 시나리오 데이터 조회 실패: {scenario_id}")
            
            # STT: 음성을 텍스트로 변환 (사용자가 제공한 텍스트가 있으면 우선 사용)
            if not user_message:
                print(f"STT 처리 시작: 오디오 크기 {len(audio_data) if audio_data else 0} bytes")
                transcribed_text = self._speech_to_text(audio_data)
            else:
                print(f"텍스트 입력: '{user_message}'")
                transcribed_text = user_message
            
            print(f"최종 텍스트: '{transcribed_text}'")
            
            # 고객 응답 생성 (프롬프트 오케스트레이터 사용)
            print("고객 응답 생성 시작")
            
            # 실제 페르소나와 시나리오 데이터 사용
            response_persona = actual_persona if actual_persona else persona
            response_scenario = actual_scenario if actual_scenario else scenario
            
            # 시츄에이션 정보 추출 (또는 기본값 사용)
            situation = response_scenario.get('situation', {})
            if not situation or not situation.get('id'):
                # situation_id를 scenario의 제목에서 추출하거나 기본값 사용
                situation_category = response_scenario.get('situation', {}).get('category_ko', 'deposit')
                situation = get_situation_defaults(situation_category)
            else:
                # 시츄에이션 기본 구조 확보
                situation = {
                    'id': situation.get('category_ko', 'deposit'),
                    'title': situation.get('category_ko', '상담'),
                    'goals': ['고객 요구사항 파악', '핵심 정보 안내'],
                    'required_slots': [],
                    'forbidden_claims': [],
                    'style_rules': ['숫자는 예시로만', '확정 불가 시 확인 안내'],
                    'disclaimer': '실제 조건은 심사 결과 및 정책에 따라 달라질 수 있습니다.'
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
                situation=situation,
                user_text=transcribed_text,
                rag_hits=[],  # TODO: RAG 검색 결과 추가
                history=conversation_history[-4:]  # 최근 4턴만 전달
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
            evaluation = self._evaluate_user_response(transcribed_text, persona, scenario)
            
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
        """페르소나에 따른 음성 특성 설정 (성별 포함)"""
        tone = persona.get("tone", "neutral")
        age_group = persona.get("age_group", "30s")
        
        # 성별 판단 - gender 필드에서 "남성"/"여성" 또는 "male"/"female" 처리
        gender = persona.get("gender", "남성")
        is_female = (gender == "여성" or gender == "female")
        
        print(f"🎤 성별: {gender}, 여성인가? {is_female}")
        
        # 성별별 음성 선택
        if is_female:
            voice_map = {
                "neutral": "nova",
                "calm": "nova", 
                "friendly": "nova",
                "angry": "shimmer",
                "impatient": "shimmer"
            }
        else:
            voice_map = {
                "neutral": "alloy",
                "calm": "echo", 
                "friendly": "echo",
                "angry": "fable",
                "impatient": "fable"
            }
        
        speed_map = {
            "neutral": 1.0,
            "calm": 0.9,
            "friendly": 1.1,
            "angry": 1.2,
            "impatient": 1.3
        }
        
        voice = voice_map.get(tone, "alloy")
        
        return {
            "voice": voice,
            "speed": speed_map.get(tone, 1.0)
        }
    
    def _generate_initial_customer_message(self, persona: Dict, scenario: Dict) -> Dict:
        """초기 고객 메시지 생성"""
        storyline = scenario.get("storyline", {})
        sample_utterances = persona.get("sample_utterances", [])
        situation = scenario.get('situation', {})
        
        # RAG 기반 초기 메시지 생성
        rag_context = self._get_rag_context(scenario)
        
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
        
        상황: {scenario.get('title', '')}
        
        RAG 컨텍스트:
        {rag_context}
        
        업무 카테고리: {situation.get('category', scenario.get('title', '')).replace('s_', '').split('_')[0]}
        세부 상황: {situation.get('details', '')}
        고객의 요구사항: {situation.get('customer_need', '')}
        
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
                                           scenario: Dict) -> Dict:
        """RAG 기반 고객 응답 생성"""
        # RAG 컨텍스트 생성
        rag_context = self._get_rag_context(scenario)
        
        # 페르소나 특성 추출
        persona_traits = self._extract_persona_traits(persona)
        
        prompt = f"""
        당신은 {persona.get('persona_id', 'Unknown')} 고객입니다.
        
        고객 특성:
        {persona_traits}
        
        상황: {scenario.get('title', '')}
        대화 플로우: {scenario.get('turn_blueprint', [])}
        
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
                "phase": self._determine_conversation_phase(scenario)
            }
            
        except Exception as e:
            print(f"고객 응답 생성 오류: {e}")
            return {
                "text": "네, 이해했습니다.",
                "phase": "ongoing"
            }
    
    def _get_rag_context(self, scenario: Dict) -> str:
        """시나리오 기반 RAG 컨텍스트 생성"""
        context_parts = []
        
        # 시나리오 정보
        context_parts.append(f"시나리오: {scenario.get('title', '')}")
        
        # Situation 정보 (업무 카테고리, 세부 상황 등)
        situation = scenario.get('situation', {})
        if situation:
            context_parts.append(f"\n업무 상황:")
            context_parts.append(f"- 카테고리: {situation.get('category', '')}")
            context_parts.append(f"- 세부 상황: {situation.get('details', '')}")
            context_parts.append(f"- 고객의 요구사항: {situation.get('customer_need', '')}")
            context_parts.append(f"- 주요 이슈: {situation.get('key_issues', '')}")
        
        # 스토리라인
        storyline = scenario.get('storyline', {})
        if storyline:
            context_parts.append(f"\n대화 맥락:")
            context_parts.append(f"- 초기 상태: {storyline.get('initial_state', '')}")
            context_parts.append(f"- 갈등: {storyline.get('conflict', '')}")
            context_parts.append(f"- 해결: {storyline.get('resolution', '')}")
        
        # 대화 플로우
        turn_blueprint = scenario.get('turn_blueprint', [])
        if turn_blueprint:
            context_parts.append(f"\n예상 대화 흐름:")
            for i, turn in enumerate(turn_blueprint[:3], 1):  # 처음 3턴만 표시
                context_parts.append(f"- {i}번째 턴: {turn.get('description', '')}")
        
        # 평가 기준
        evaluation_rubric = scenario.get('evaluation_rubric', [])
        if evaluation_rubric:
            context_parts.append(f"\n평가 기준:")
            for rubric in evaluation_rubric[:2]:  # 처음 2개만 표시
                context_parts.append(f"- {rubric.get('metric', '')}: {rubric.get('checklist', [])}")
        
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
    
    def _determine_conversation_phase(self, scenario: Dict) -> str:
        """대화 단계 결정"""
        turn_blueprint = scenario.get('turn_blueprint', [])
        
        if len(turn_blueprint) <= 2:
            return "initial"
        elif len(turn_blueprint) <= 4:
            return "developing"
        else:
            return "concluding"
    
    def _evaluate_user_response(self, user_message: str, persona: Dict, scenario: Dict) -> str:
        """사용자 응답 평가"""
        evaluation_rubric = scenario.get('evaluation_rubric', [])
        
        if not evaluation_rubric:
            return "평가 기준이 없습니다."
        
        # 평가 기준을 문자열로 변환
        rubric_text = "\n".join([
            f"- {rubric.get('metric', '')} ({rubric.get('weight', 0)}): {rubric.get('checklist', [])}"
            for rubric in evaluation_rubric
        ])
        
        prompt = f"""
        은행 직원의 응답: "{user_message}"
        
        고객 정보:
        - 고객 타입: {persona.get('type', '')}
        - 금융 이해도: {persona.get('financial_literacy', '')}
        - 톤: {persona.get('tone', 'neutral')}
        
        평가 기준:
        {rubric_text}
        
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
