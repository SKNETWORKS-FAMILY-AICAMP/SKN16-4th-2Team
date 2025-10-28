"""
최종 RAG 서비스 - SQL 오류 없이 확실하게 작동
"""
import os
import requests
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

class FinalRAGService:
    def __init__(self, session: Session):
        self.session = session
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        
        # 문서 제목 리스트 (실제 데이터베이스의 모든 제목)
        self.document_titles = [
            "위임장", "신용보증서", "이의신청서", "대위변제증서", "대출만기안내", "민원접수양식", "제증명의뢰서",
            "거치식예금약관", "고객권리안내문", "수신거래상황표", "신용보증약정서", "여신거래상황표",
            "이의제기신청서", "이자계산내역서", "자료열람요구서", "잔존채무확인서", "적립식예금약관",
            "피해구제신청서", "대출만기경과안내", "예금거래기본약관", "전세지킴보증약관",
            "채권자계좌신고서", "가계대출상품설명서", "기업대출상품설명서", "보증채무이행청구서",
            "비과세종합저축특약", "신용보증부실통지서", "전자금융거래기본약관",
            "은행여신거래기본약관(함께대출용)", "은행여신거래기본약관(가계용)", "은행여신거래기본약관(기업용)",
            "전자금융거래기본약관(기업용)", "입출금이자유로운예금_약관", "가계대출상품설명서(함께대출용)",
            "증권계좌개설서비스+설명서", "계좌통합관리서비스+이용약관", "증권계좌개설서비스_이용약관",
            "전월세보증금대출+상품설명서", "위임장(개인여신)", "위임장(금결원+대출이동시스템)", 
            "위임장+(전월세대출+심사용)", "위임장+(상속)",
            # 추가된 모든 제목들
            "전기통신금융사기+피해구제신청서+종합+서류", "전기통신금융사기+전화번호+등+신고",
            "대출이동시스템을_통한_대환대출서비스_이용약관", "대출이동시스템을_통한__전세대출_대환대출서비스_이용약관",
            "정보변경신청서(전기통신금융사기관련)", "자금반환동의서(전기통신금융사기+관련)(지급청구서+겸용)",
            "신용보증신청서(서민금융진흥원)", "피해구제신청서(작성예시본)",
            "신용보증약정서(개별거래용-비대면)_[신용보증기금]", "사장님대환대출(갱신보증)+상품안내",
            "신용보증약정서(개별거래-개별보증용)_[신용보증재단]", "대출거래약정서(가계용)", "대출거래약정서(기업용)",
            "고객거래확인서(개인)", "은행거래신청서(법인)", "대출거래약정서(원금_자동상환용)",
            "고객거래확인서(법인_단체)", "계좌이동서비스+이용약관", "거래외국환은행+지정(변경)+신청서+",
            "카드이동서비스_이용약관", "신용보증신청서_(한국주택금융공사)",
            "수출신용보증(선적전)_수출용원자재_수입신용보증_약정서_[한국무역보험공사]",
            "고객확인제도+안내문", "기회보증대출+상품안내", "대출계좌원장+거래내역", "우대보증대출+상품안내",
            "국내원천소득+제한세율+적용신청서(비거주자용)", "다이렉트보증+상품+설명서+[한국무역보험공사]+",
            "금융거래정보+제공+동의서+[토스뱅크+아이+서비스]", "금융거래정보+제공+동의서+[연체금+자동충전+서비스]",
            "금융거래정보+제공+동의서+[채우기+송금+서비스]", "외화예금거래_기본약관",
            "후불교통카드_이용약관_(하나카드)", "전세지킴보증_신청서(한국주택금융공사)",
            "전세지킴보증_확약서(한국주택금융공사)", "등기변동알림_서비스_이용약관",
            "햇살론뱅크에_따른_추가약정서", "지급청구서(개인)", "지급청구서(법인)", "채권계산서(경매)",
            "보이스피싱+피해예방+문진표", "모바일뱅킹+서비스+설명서", "법정대리인+인증+자동화+서비스+이용+동의+신청서",
            "공동명의인+확인+및+동의서", "위촉증명서+(전월세대출+심사용)", "해촉증명서+(전월세대출+심사용)",
            "햇살론뱅크_신용보증약관", "자동환전시_부족한돈_자동충전_서비스_이용약관", "모바일뱅킹_서비스_이용약관",
            "자동이체(납부)_약관", "자동이체(송금)_약관", "피해구제+취소신청서",
            "대출거래+추가약정서(사장님새날대출용)", "대출거래+추가약정서(이차보전대출용)",
            "대출거래+추가약정서(당행대환용)", "대출거래+추가약정서(대환대출용)",
            "대출거래+추가약정서(함께대출+조건변경용)", "대출거래+추가약정서(함께대출+고액+신용대출의+사후+용도관리용)",
            "대출거래+추가약정서(고액+신용대출+사후+용도관리용)", "토스뱅크+나눠모으기+통장+상품설명서",
            "대출거래+추가약정서+(전월세보증금대출용)", "대출거래+추가약정서+(함께대출용)",
            "대출거래+추가약정서+(가계용)", "대출거래+추가약정서+(기업용)",
            "대출거래+추가약정서+(주택+취득+제한+등에+대한+전세자금대출+추가약정용)",
            "토스뱅크+도전통장+상품설명서", "토스뱅크+모임금고+상품설명서", "토스뱅크+외화통장+상품설명서",
            "토스뱅크+모임통장+상품설명서+", "토스뱅크+모임카드+프로모션+혜택+안내장",
            "토스뱅크+모임통장+서비스+설명서+", "개인정보+노출사실+해제+신청서",
            "전자금융+이체한도+증액+신청서", "토스뱅크+키워봐요+적금+상품설명서+",
            "금융거래+정보제공+요구·동의서", "대출정보+열람청구+및+상환+위임장(신용보증기금)",
            "대출거래+약정서(함께대출용)", "정기적인+증명서+발급+신청서+",
            "대출거래+약정서+(가계대출+금리우대용)", "미성년자+업무+요청서", "토스뱅크+통장+상품설명서",
            "토스뱅크+법인+정기예금+상품설명서", "토스뱅크+아이+서비스+설명서", "토스뱅크+게임+저금통+상품설명서",
            "금융거래+목적+확인서+(법인)", "토스뱅크+법인+통장(제휴)+상품설명서", "토스뱅크+굴비+적금+상품설명서",
            "토스뱅크+법인+통장+상품설명서", "토스뱅크+서브+통장+상품설명서", "토스뱅크+아이+적금+상품설명서",
            "토스뱅크+아이+통장+상품설명서", "토스뱅크+자유+적금+상품설명서", "토스뱅크+이자+받는+저금통+상품설명서",
            "토스뱅크+먼저+이자+받는+정기예금+상품설명서", "기초정보+정정·삭제+및+자동화평가+재산출+요청서",
            "개인정보+수집·이용+및+제공+동의서+[오픈뱅킹]+", "개인정보+수집・이용+동의서+[토스뱅크+도전서비스]",
            "개인정보+수집・이용+동의서+[토스뱅크+함께+응원하기+서비스]", "개인정보+수집·이용·제공+동의서+[사진+올리기+기능+이용]",
            "현금카드_약관", "이체한도_추가약정서", "토스뱅크_도전서비스_이용약관",
            "토스뱅크_금융콘텐츠_구독서비스_이용약관", "토스뱅크_나눠모으기_통장_특약",
            "체크카드_개인회원_약관", "토스뱅크_도전통장_특약", "토스뱅크_모임금고_특약",
            "토스뱅크_모임통장_특약", "토스뱅크_외화통장_특약", "토스뱅크_모임카드_상품약관",
            "토스뱅크_모임카드_이용약관", "토스뱅크_체크카드_상품약관", "토스뱅크_모임통장_서비스이용약관",
            "오픈뱅킹_공동업무_금융정보조회_약관", "오픈뱅킹_공동업무_자동계좌이체_약관",
            "토스뱅크_외화통장_부가서비스_특약", "오픈뱅킹_자동이체_연체방지_서비스_이용약관",
            "토스뱅크_기업뱅킹_서비스_이용약관", "토스뱅크_투자소식_구독_서비스_이용약관",
            "토스뱅크_키워봐요_적금_특약_", "오픈뱅킹_서비스_이용약관", "위치기반_서비스_이용약관",
            "커뮤니티_서비스_이용약관", "소상공인_저금리_대환대출_신용보증약정_설명서(신용보증기금)",
            "토스뱅크_통장_특약", "채무상환_조정_약정서", "토스뱅크_함께_응원하기_서비스_이용약관",
            "토스뱅크_법인_정기예금__특약", "토스뱅크_게임_저금통_특약", "토스뱅크_아이_서비스_이용_약관",
            "토스뱅크_아이_서비스_이용_약관(부모용)", "토스뱅크_법인_통장(제휴)_특약",
            "토스뱅크_굴비_적금_특약", "토스뱅크_법인_통장_특약", "토스뱅크_서브_통장_특약",
            "토스뱅크_아이_적금_특약", "토스뱅크_아이_통장_특약", "토스뱅크_자유_적금_특약",
            "토스뱅크_이자_받는_저금통_특약", "토스뱅크_모임_정산_서비스_이용약관",
            "토스뱅크_먼저_이자_받는_정기예금_특약", "위임장(개인여신)", "위임장(금결원+대출이동시스템)",
            "관리비+자동이체(납부)+약관", "비대면+금융사고+문진표", "대출금+상환신청+명세서_확인",
            "비대면+금융사고+조사+신청서+(수기용)", "제신고+및+변경+의뢰서", "위임장+(전월세대출+심사용)",
            "위임장+(상속)", "법인용_인터넷뱅킹_서비스_이용약관", "연체금_자동충전_서비스_이용약관",
            "개인(신용)정보+선택적+제공+동의+(부정+사용+방지)+(선택)", "개인(신용)정보+동의서+및+나의+행정정보+토스뱅크+제공+요청서+[공공마이데이터]+(수신)",
            "개인(신용)정보+조회+동의서++[공공+마이데이터]", "개인(신용)정보+수집+이용+동의서(금융결제원+대출이동시스템)",
            "개인(신용)정보+수집·이용+동의서(토스뱅크+금융콘텐츠+구독+서비스)", "개인(신용)정보+수집·이용+동의서+[계좌통합관리서비스]",
            "개인(신용)정보+수집·이용+동의서+[연체금+자동충전+서비스]", "개인(신용)정보+수집·이용+동의서+[비여신+금융거래]",
            "개인(신용)정보+수집·이용+동의서[대환대출+스크래핑]", "개인(신용)정보+수집·이용+동의서[채우기+송금]",
            "개인(신용)정보+수집·이용+동의서[대리인](필수)", "개인(신용)정보+수집·이용·제공+동의서(함께대출)",
            "개인(신용)정보+수집·이용·제공+동의서+(체크카드_비교통)+", "개인(신용)정보+수집·이용·제공+동의서+[전월세보증금대출+배우자]",
            "개인(신용)정보+수집·이용·제공+동의서+[전월세보증금대출]", "개인(신용)정보+수집·이용·제공+동의서+[여신금융거래]",
            "개인(신용)정보+수집·이용·제공+동의서+[주택보유수+확인+등]", "개인(신용)정보+수집·이용·제공+동의서+[권리보험용]",
            "개인(신용)정보+수집·이용·제공+동의서+[토스뱅크+서비스+출금이체]", "개인(신용)정보+수집·이용·제공+동의서+[토스뱅크+송금+서비스]",
            "개인(신용)정보+수집·이용·제공+동의서[제휴대환대출]", "개인(신용)정보+수집·이용·제공+동의서[상품서비스+안내+등]",
            "개인(신용)정보+수집·이용·제공·조회+동의서", "개인(신용)정보+수집·이용·제공·조회+동의서(대안정보+활용)",
            "개인(신용)정보+수집·이용·제공·조회+동의서+[후불+교통카드]", "개인(신용)정보+수집·이용·제공·+동의+(체크카드_교통)+",
            "개인(신용)정보+수집・이용+동의서+[토스뱅크+같이+덕질하기+서비스]", "나의+행정정보+토스뱅크+제공+요청서[공공마이데이터]_여신_정기적전송미포함",
            "계약+해지+요구서", "계약+체결·이행+등을+위한+필수+동의서+[보이스피싱신용보험용]",
            "카드_결제_부족금액_자동_채우기_서비스_이용약관", "티몬‧위메프+정산지연+피해기업+확약서",
            "티몬‧위메프+판매자+정산확인+자료+예시", "내+한도+관리+서비스_이용약관",
            "(기업뱅킹)개인정보+처리방침", "[기업뱅킹용]+토스뱅크+인증서+서비스+이용약관",
            "[필수]개인(신용)정보+수집·이용·제공+동의서[전자금융거래+사고+피해조사]", "[필수]+민감정보+수집·이용+동의서+[비과세종합저축]+",
            "[선택]+개인정보+수집·이용+동의서+[토스뱅크+이벤트+알림받기]", "[선택]+개인정보+수집·이용+동의서+[토스뱅크+이벤트+참여]",
            "[선택]+개인정보+수집·이용+동의서+[토스뱅크+대출+갈아타기+알림받기]", "[필수]+개인정보+수집·이용·제공+동의서+[민원접수]",
            "[필수]+개인(신용)정보+조회동의서+[공공+마이데이터]+(제휴회원용)", "[필수]+개인(신용)정보+수집이용+동의서+(구독+서비스+이용)",
            "[선택]+개인(신용)정보+수집이용+동의서[카드+캐시백+프로모션+알림]+", "[필수]+개인(신용)정보+수집,+이용+동의서(신고접수)+(안심보상제)+(수기용)",
            "[필수]+개인(신용)정보+수집,+이용,+제공+동의서[전자금융거래+사고+피해조사]+(안심보상제)+(서면용)",
            "[필수]+개인(신용)정보+수집·이용+동의서+(오픈뱅킹+안심차단+서비스)", "[선택]+개인(신용)정보+수집·이용+동의서+[수출똑똑보증대출+출시+알림+받기]",
            "[선택]+개인(신용)정보+수집·이용+동의서+[제휴대환대출+오픈안내]", "[필수]+개인(신용)정보+수집·이용+동의서+[기업뱅킹+회원가입용]",
            "[필수]+개인(신용)정보+수집·이용·제공+동의서(사업장+위치정보)", "[필수]+개인(신용)정보+수집·이용·제공·조회+동의서+(제휴회원용)",
            "[필수]+개인(신용)정보+수집・이용+동의서+[모임통장서비스이용]+", "「오픈뱅킹공동업무」+금융정보+조회+약관+(기업고객용)",
            "토스뱅크_하루_1분_뇌_운동_서비스_이용약관", "개인(신용)정보+수집・이용+동의서+[하루+1분+뇌+운동+서비스]",
            "중소기업은행법 타법개정 2020.03.24 [법률 제17112호, 시행 2021.3.25.] 금융위원회",
            "한국은행법 타법개정 2023.05.16 [법률 제19409호, 시행 2024.5.17.] 기획재정부",
            "가계대출상품설명서(제휴대환대출용)+(판매종료+-+2023.05.19.)", "대출거래+추가약정서(제휴대환대출용)+(판매종료+-+2023.05.19.)",
            "은행법 타법개정 2023.09.14 [법률 제19700호, 시행 2023.9.14.] 금융위원회",
            "토스뱅크++모으기+상품설명서(판매종료+-+2024.02.14.)", "토스뱅크_모으기_특약_(판매종료_-_2024.02.14.)",
            "한국수출입은행법 일부개정 2024.03.19 [법률 제20373호, 시행 2024.3.19.] 기획재정부",
            "상호저축은행법 타법개정 2024.09.20 [법률 제20434호, 시행 2025.1.31.] 금융위원회",
            "한국산업은행법 일부개정 2025.01.21 [법률 제20719호, 시행 2025.1.21.] 금융위원회",
            "한국수출입은행법 시행령 타법개정 2025.01.21 [대통령령 제35228호, 시행 2025.1.31.] 기획재정부",
            "중소기업은행법 시행령 타법개정 2025.01.21 [대통령령 제35228호, 시행 2025.1.31.] 금융위원회",
            "한국은행법 시행령 타법개정 2025.01.21 [대통령령 제35228호, 시행 2025.1.31.] 기획재정부",
            "은행법 시행령 타법개정 2025.03.12 [대통령령 제35382호, 시행 2025.3.12.] 금융위원회",
            "한국산업은행법 시행령 일부개정 2025.06.25 [대통령령 제35607호, 시행 2025.6.25.] 금융위원회",
            "개인정보+제3자+제공+동의서+[토스뱅크+함께+응원하기+서비스]", "개인(신용)정보+및+금융거래정보+제3자+제공+동의서+[모임통장서비스이용]",
            "개인(신용)정보+제3자+제공+동의서+[이상금융거래행위+탐지+등]", "개인(신용)정보+제3자+제공+동의서+[비바리퍼블리카]",
            "개인(신용)정보+제3자+제공+동의서[정보+자동입력]", "[필수]+토스계정통합서비스+개인(신용)정보+제3자+제공+동의서[비바리퍼블리카]",
            "[필수]+개인정보+제3자+제공+동의+(안심보상+신고접수)", "[필수]+개인(신용)정보+및+금융거래정보+제3자+제공+동의서+[모임카드서비스이용]",
            "[필수]+개인(신용)정보+및+금융거래정보+제3자+제공+동의서+[함께+키우기]+", "[선택]+개인(신용)정보+제3자+제공+동의서+(자녀+계좌+관리+서비스)",
            "[선택]+개인(신용)정보+제3자+제공+동의서+[토스뱅크+이벤트+참여]_추가정보", "[필수]+개인(신용)정보+제3자+제공+동의서+[자동차+시세+정보+조회]",
            "개인정보+제3자+제공+동의서+[토스뱅크+하루+1분+뇌+운동+서비스]", "토스뱅크+체크카드+스위치+캐시백+시즌5+_+어디서나+캐시백",
            "토스뱅크+체크카드+스위치+캐시백+시즌5+_+오프라인+캐시백", "토스뱅크+체크카드+스위치+캐시백+시즌5+_+온라인+캐시백",
            "토스뱅크+체크카드+스위치+캐시백+시즌5+_+기부+캐시백 (1)", "CD수익률+설명서",
            "개인(신용)정보+수집·이용+동의서+[ChatGPT+$1에+구독하기+이벤트]", "개인(신용)정보+조회+동의서++[공공+마이데이터_나의+DSR]",
            "개인(신용)정보+수집・이용·제공·조회+동의서+[나의+DSR]", "나의+행정정보+토스뱅크+제공+요청서[공공마이데이터_나의DSR]",
            "본인확인서+(FATCA+·+CRS+부모_대리인용)", "본인+확인서+(FATCA+·+CRS+개인용)",
            "본인+확인서+(FATCA+·+CRS+법인용)", "KCB+올크레딧+서비스+이용약관+(신상정보서비스)",
            "KCB+모바일+안심+플러스+이용약관", "개인신용보험+추가약정서(SGI)", "기회UP보증대출+상품안내"
        ]
    
    async def process_query(self, question: str) -> Dict:
        """메인 쿼리 처리"""
        try:
            print(f"RAG 검색 시작: '{question}'")
            
            # 1. 인사말 체크
            if self.is_greeting(question):
                return {
                    "answer": "안녕하세요! AI 하리보입니다 🐻 신입사원 온보딩 관련 질문이 있으시면 언제든지 말씀해주세요!",
                    "sources": [],
                    "response_time": 0.0,
                    "answer_type": "greeting",
                    "mode": "GREETING",
                    "doc_type": "general",
                    "citations": [],
                    "next_actions": [],
                    "confidence": 1.0,
                    "notes": "인사말 응답"
                }
            
            # 2. 제목 매칭 확인
            matched_titles = self.find_exact_title_match(question)
            print(f"매칭된 제목들: {matched_titles}")
            
            # 3. RAG 문서 검색
            rag_docs = await self.search_rag_documents(question)
            print(f"RAG 문서 검색 결과: {len(rag_docs)}개")
            
            # 4. 답변 생성
            if rag_docs or matched_titles:
                # RAG 답변 생성
                answer = await self.generate_rag_answer(question, rag_docs, matched_titles)
                
                # sources를 딕셔너리 형태로 변환 (RAG 문서와 매칭된 제목 모두 포함)
                sources = []
                
                # 1. RAG 문서에서 찾은 제목들 추가
                if rag_docs:
                    for doc in rag_docs[:3]:
                        sources.append({"title": doc.get("title", ""), "type": "document"})
                
                # 2. 매칭된 제목들 추가 (중복 제거)
                if matched_titles:
                    existing_titles = {source["title"] for source in sources}
                    for title in matched_titles[:3]:
                        if title not in existing_titles:
                            sources.append({"title": title, "type": "document"})
                
                print(f"최종 sources: {sources}")
                
                return {
                    "answer": answer,
                    "sources": sources,  # 관련 자료실 문서 표시 복원
                    "response_time": 0.0,
                    "answer_type": "rag",
                    "mode": "RAG",
                    "doc_type": "form",
                    "citations": [],
                    "next_actions": [],
                    "confidence": 0.9,
                    "notes": "RAG 답변"
                }
            else:
                # 은행 업무 관련 질문인지 확인 (키워드 확장)
                bank_keywords = ["고객", "대출", "예금", "적금", "상품", "금리", "한도", "신청", "서류", "절차", "추천", "문의", "상담", 
                               "보이스피싱", "피싱", "사기", "피해", "대처", "신고", "예방", "금융사고", "보안", "안전",
                               "입출금", "이자", "수수료", "면제", "계산", "중도해지", "약관", "기본약관", "특약", "상품설명서",
                               "모임통장", "통장", "계좌", "개인정보", "제3자", "제공", "범위", "서비스", "이용약관", "거래약관",
                               "상품추천", "추천상품", "상품안내", "상품소개", "상품비교", "상품선택", "상품가입", "상품가입절차"]
                if any(keyword in question for keyword in bank_keywords):
                    # 은행 업무 관련 질문은 RAG + GPT 협업 사용
                    answer = await self.generate_rag_gpt_collaboration(question, rag_docs, matched_titles)
                    
                    # sources 구성
                    sources = []
                    if rag_docs:
                        for doc in rag_docs[:3]:
                            sources.append({"title": doc.get("title", ""), "type": "document"})
                    if matched_titles:
                        existing_titles = {source["title"] for source in sources}
                        for title in matched_titles[:3]:
                            if title not in existing_titles:
                                sources.append({"title": title, "type": "document"})
                    
                    return {
                        "answer": answer,
                        "sources": sources,
                        "response_time": 0.0,
                        "answer_type": "rag_gpt_collaboration",
                        "mode": "BANK_ADVICE",
                        "doc_type": "general",
                        "citations": [],
                        "next_actions": [],
                        "confidence": 0.8,
                        "notes": "RAG + GPT 협업 답변"
                    }
                else:
                    # 완전히 관련 없는 질문에 대한 안내
                    answer = await self.generate_off_topic_answer(question)
                    return {
                        "answer": answer,
                        "sources": [],
                        "response_time": 0.0,
                        "answer_type": "off_topic",
                        "mode": "OFF_TOPIC",
                        "doc_type": "general",
                        "citations": [],
                        "next_actions": [],
                        "confidence": 0.8,
                        "notes": "관련 없는 질문 안내"
                    }
                
        except Exception as e:
            print(f"Process query error: {e}")
            return {
                "answer": "죄송합니다. 일시적인 오류가 발생했습니다.",
                "sources": [],
                "response_time": 0.0,
                "answer_type": "error",
                "mode": "ERROR",
                "doc_type": "general",
                "citations": [],
                "next_actions": [],
                "confidence": 0.0,
                "notes": f"오류: {str(e)}"
            }
    
    def find_matching_titles(self, query: str) -> List[str]:
        """제목 매칭 (특수문자 처리 포함)"""
        query_clean = self.clean_text(query)
        matched = []
        
        for title in self.document_titles:
            title_clean = self.clean_text(title)
            
            # 정확한 매칭
            if query_clean in title_clean or title_clean in query_clean:
                matched.append(title)
                continue
            
            # 부분 매칭 (단어 단위)
            query_words = query_clean.split()
            title_words = title_clean.split()
            
            for q_word in query_words:
                for t_word in title_words:
                    if q_word in t_word or t_word in q_word:
                        if title not in matched:
                            matched.append(title)
                        break
        
        return matched[:5]  # 최대 5개
    
    def clean_text(self, text: str) -> str:
        """텍스트 정리 (특수문자 제거)"""
        import re
        # 특수문자를 공백으로 변환
        text = re.sub(r'[+()\[\]{}&=\-_·]', ' ', text)
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        return text.lower().strip()
    
    def find_exact_title_match(self, query: str) -> List[str]:
        """정확한 제목 매칭 (특수문자 처리 개선)"""
        query_clean = self.clean_text(query)
        matched = []
        
        for title in self.document_titles:
            title_clean = self.clean_text(title)
            
            # 정확한 매칭
            if query_clean == title_clean:
                matched.append(title)
                continue
            
            # 부분 매칭 (단어 단위)
            query_words = query_clean.split()
            title_words = title_clean.split()
            
            # 모든 쿼리 단어가 제목에 포함되는지 확인
            if all(any(q_word in t_word or t_word in q_word for t_word in title_words) for q_word in query_words):
                matched.append(title)
        
        return matched[:5]
    
    async def search_rag_documents(self, query: str) -> List[Dict]:
        """RAG 문서 검색 (쿼리 확장 포함)"""
        try:
            # 원본 쿼리와 정리된 쿼리 모두 사용
            query_original = query.strip()
            query_clean = self.clean_text(query)
            
            # 쿼리 확장 (키워드 기반)
            expanded_queries = self.expand_query(query_original)
            
            print(f"검색 쿼리: '{query_original}' -> 정리된 쿼리: '{query_clean}'")
            print(f"확장된 쿼리들: {expanded_queries}")
            
            # SQL에서 직접 텍스트 매칭 사용 (확장된 쿼리 포함)
            all_queries = [query_original, query_clean] + expanded_queries
            
            # 동적 SQL 생성
            query_conditions = []
            params = {}
            for i, q in enumerate(all_queries):
                if q.strip():  # 빈 쿼리 제외
                    query_conditions.append(f"(dc.content ILIKE :query{i} OR d.title ILIKE :query{i})")
                    params[f"query{i}"] = f"%{q}%"
            
            if not query_conditions:
                return []
            
            sql = text(f"""
                SELECT 
                    dc.content,
                    d.title,
                    d.category,
                    d.id as document_id
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.is_indexed = true 
                AND d.category = 'RAG'
                AND ({' OR '.join(query_conditions)})
                LIMIT 20
            """)
            
            result = self.session.execute(sql, params)
            
            docs = []
            for row in result:
                docs.append({
                    "content": row.content,
                    "title": row.title,
                    "category": row.category,
                    "document_id": row.document_id
                })
                print(f"SQL 매칭: '{row.title}'")
            
            print(f"SQL 텍스트 매칭으로 {len(docs)}개 문서 발견")
            return docs
            
        except Exception as e:
            print(f"RAG 문서 검색 오류: {e}")
            return []
    
    def expand_query(self, query: str) -> List[str]:
        """쿼리 확장 (키워드 기반)"""
        expanded = []
        
        # 예금 관련 확장
        if "입출금" in query or "예금" in query:
            expanded.extend(["입출금이자유로운예금", "입출금이자유로운예금_약관", "예금거래기본약관"])
        
        if "이자" in query:
            expanded.extend(["이자계산", "이자계산내역서", "이자"])
        
        if "수수료" in query:
            expanded.extend(["수수료", "면제", "수수료면제"])
        
        if "적금" in query:
            expanded.extend(["적립식예금약관", "적금", "적립식"])
        
        if "중도해지" in query:
            expanded.extend(["중도해지", "해지", "만기전해지"])
        
        if "약관" in query:
            expanded.extend(["약관", "기본약관", "거래약관"])
        
        # 신용보증 관련 확장
        if "신용보증" in query:
            expanded.extend(["신용보증서", "신용보증약정서", "신용보증신청서", "신용보증부실통지서"])
        
        if "보증료" in query or "보증료율" in query:
            expanded.extend(["보증료", "보증료율", "신용보증약정서"])
        
        if "채무이행" in query:
            expanded.extend(["채무이행", "보증채무이행청구서", "채무이행절차"])
        
        if "대출" in query:
            expanded.extend(["대출", "대출거래약정서", "대출상품설명서", "대출만기안내"])
        
        # 모임통장/계좌 관련 확장
        if "모임통장" in query or "통장" in query:
            expanded.extend(["모임통장", "통장", "계좌", "계좌통합관리서비스", "계좌이동서비스"])
        
        if "개인정보" in query:
            expanded.extend(["개인정보", "개인정보처리방침", "개인정보+처리방침"])
        
        if "제3자" in query or "제공" in query:
            expanded.extend(["제3자", "제공", "동의서", "금융거래정보+제공+동의서"])
        
        # 상품 관련 확장
        if "상품" in query or "추천" in query:
            expanded.extend(["상품설명서", "상품안내", "가계대출상품설명서", "기업대출상품설명서", "상품소개"])
        
        if "대출상품" in query or "대출" in query:
            expanded.extend(["대출상품설명서", "가계대출상품설명서", "기업대출상품설명서", "대출상품안내", "대출거래약정서"])
        
        if "예금상품" in query or "예금" in query:
            expanded.extend(["예금상품설명서", "예금상품안내", "입출금이자유로운예금", "적립식예금약관"])
        
        # 연령대별 대출 상품 확장
        if "70대" in query or "고령" in query or "연령" in query:
            expanded.extend(["가계대출상품설명서", "대출상품설명서", "대출거래약정서", "상품설명서", "대출상품안내"])
        
        # 대출 상담 관련 확장
        if "대출상담" in query or "대출 추천" in query or "대출 상품" in query:
            expanded.extend(["가계대출상품설명서", "대출상품설명서", "대출거래약정서", "대출상품안내", "상품설명서", "주택담보대출", "가계대출", "전월세보증금대출"])
        
        # 구체적인 대출 상품명 확장
        if "대출" in query:
            expanded.extend(["가계대출상품설명서", "대출상품설명서", "주택담보대출", "가계대출", "전월세보증금대출", "대출거래약정서"])
        
        # 중복 제거 및 빈 문자열 제거
        expanded = list(set([q for q in expanded if q.strip()]))
        
        return expanded
    
    async def generate_rag_answer(self, question: str, rag_docs: List[Dict], matched_titles: List[str]) -> str:
        """RAG 답변 생성"""
        # RAG 내용 구성
        rag_content = ""
        if rag_docs:
            rag_content = "\n\n".join([doc["content"][:300] for doc in rag_docs[:3]])
        
        # 참고자료 구성
        references = ""
        if matched_titles:
            references = f"\n\n📚 관련 자료실 문서:\n"
            for i, title in enumerate(matched_titles[:3], 1):
                references += f"{i}. {title}\n"
        
        prompt = f"""
다음 문서 내용을 바탕으로 질문에 답변해주세요.

문서 내용:
{rag_content}

질문: {question}

답변 요구사항:
1. 신입사원이 이해하기 쉽게 간결하고 친절하게 답변하세요
2. 긴 문단 대신 짧은 문장과 불릿 포인트를 사용하세요
3. 핵심 정보를 먼저 제시하고, 세부사항은 나중에 설명하세요
4. 단계별로 나누어 설명하세요 (1단계, 2단계 등)
5. 한국어로 친근하게 답변하세요 (🐻 이모티콘만 사용)
6. AI 하리보로서 신입사원을 도와주는 마음으로 답변하세요

답변:
"""
        
        answer = await self.call_gpt(prompt)
        
        # 참고자료 추가
        if references:
            answer += references
        
        return answer
    
    def is_greeting(self, query: str) -> bool:
        """인사말 감지"""
        greetings = ["안녕", "안녕하세요", "hi", "hello", "ㅎㅇ", "하이", "헬로", "좋은 아침", "좋은 오후", "좋은 저녁", "안ㄴ녕"]
        return any(greeting in query.lower() for greeting in greetings)
    
    async def generate_off_topic_answer(self, question: str) -> str:
        """관련 없는 질문에 대한 안내"""
        # 은행 업무 관련 질문인지 확인
        bank_keywords = ["고객", "대출", "예금", "적금", "상품", "금리", "한도", "신청", "서류", "절차", "추천", "문의", "상담"]
        if any(keyword in question for keyword in bank_keywords):
            return "은행 업무 관련 질문이시군요! 🐻 신입사원 온보딩 자료실의 상품설명서나 약관 문서를 참고해서 답변드릴 수 있어요. 구체적인 상품명이나 서류명을 말씀해주시면 더 정확한 안내를 드릴 수 있습니다!"
        
        return "죄송해요 🐻 AI 하리보는 신입사원 온보딩 관련 질문을 주로 도와드려요. 위임장, 이의신청서, 약관, 상품설명서 등에 대해 궁금한 점이 있으시면 언제든지 말씀해주세요!"
    
    async def generate_rag_gpt_collaboration(self, question: str, rag_docs: List[Dict], matched_titles: List[str]) -> str:
        """RAG + GPT 협업 답변"""
        # RAG 내용 구성
        rag_content = ""
        if rag_docs:
            for i, doc in enumerate(rag_docs[:3], 1):
                rag_content += f"\n[문서 {i}] {doc.get('title', '')}\n{doc.get('content', '')}\n"
        
        # 참고자료 추가
        references = ""
        if matched_titles:
            references = f"\n\n📚 관련 자료실 문서:\n"
            for i, title in enumerate(matched_titles[:3], 1):
                references += f"{i}. {title}\n"
        
        prompt = f"""
다음 문서 내용을 바탕으로 질문에 답변해주세요. 문서 내용이 있으면 반드시 문서 내용을 우선적으로 활용하세요.

문서 내용:
{rag_content}

질문: {question}

답변 요구사항:
- 신입사원이 이해하기 쉽게 친절하고 상세하게 답변하세요
- 자연스러운 문단으로 구성하여 길게 설명하세요 (불릿 포인트나 단계별 나열 금지)
- 핵심 정보를 먼저 제시하고, 세부사항을 포함한 완전한 설명을 제공하세요
- 문단과 문단 사이는 자연스럽게 연결하여 흐름 있게 작성하세요
- 한국어로 친근하게 답변하세요 (🐻 이모티콘은 답변 시작과 끝에만 사용)
- AI 하리보로서 신입사원을 도와주는 마음으로 답변하세요
- 문서 내용이 있으면 반드시 문서 내용을 우선 활용하고, 문서 내용에 없는 부분만 일반적인 은행 업무 지식으로 보완하세요
- 질문과 관련 없는 내용은 답변에 포함하지 마세요
- 질문의 핵심 키워드와 직접 관련된 내용만 답변하세요
- 문장을 충분히 길게 작성하여 상세한 설명을 제공하세요
- 각 문단은 5-7문장으로 구성하여 충분한 정보를 제공하세요
- 상품 추천 관련 질문에는 구체적인 상품명과 특징을 포함하여 답변하세요
- 연령대별 고객 특성을 고려한 맞춤형 상품 추천을 제공하세요
- 대출 상품의 경우 금리, 한도, 상환조건 등 구체적인 정보를 포함하세요
- 대출 상담 질문에는 실제 대출 상품을 추천하고, 알림 서비스나 기타 서비스는 추천하지 마세요
- 답변을 자연스러운 문단으로 구성하여 길고 상세하게 작성하세요
- 대출 상품 추천 시에는 구체적인 상품명(가계대출, 주택담보대출, 전월세보증금대출 등)을 명시하세요
- 70대 고객에게는 연령대에 맞는 대출 상품을 구체적으로 추천하세요
- 대출 상담 질문에는 반드시 구체적인 대출 상품명을 추천하고, 단계별 설명이나 일반적인 조언은 피하세요
- 고객에게 직접적인 대출 상품 추천을 제공하세요

답변:
"""
        
        answer = await self.call_gpt(prompt)
        
        # 참고자료 추가
        if references:
            answer += references
        
        return answer

    async def generate_gpt_answer(self, question: str) -> str:
        """GPT 백업 답변"""
        prompt = f"""
신입사원이 고객 상담 시 도움이 될 수 있도록 답변해주세요.

질문: {question}

답변 요구사항:
- 신입사원이 이해하기 쉽게 친절하고 상세하게 답변하세요
- 자연스러운 문단으로 구성하여 길게 설명하세요 (불릿 포인트나 단계별 나열 금지)
- 핵심 정보를 먼저 제시하고, 세부사항을 포함한 완전한 설명을 제공하세요
- 문단과 문단 사이는 자연스럽게 연결하여 흐름 있게 작성하세요
- 한국어로 친근하게 답변하세요 (🐻 이모티콘은 답변 시작과 끝에만 사용)
- AI 하리보로서 신입사원을 도와주는 마음으로 답변하세요
- 은행 업무에 관련된 실용적인 조언을 포함하세요
- 문장을 충분히 길게 작성하여 상세한 설명을 제공하세요
- 각 문단은 5-7문장으로 구성하여 충분한 정보를 제공하세요
- 상품 추천 관련 질문에는 구체적인 상품명과 특징을 포함하여 답변하세요
- 연령대별 고객 특성을 고려한 맞춤형 상품 추천을 제공하세요
- 대출 상품의 경우 금리, 한도, 상환조건 등 구체적인 정보를 포함하세요
- 대출 상담 질문에는 실제 대출 상품을 추천하고, 알림 서비스나 기타 서비스는 추천하지 마세요
- 답변을 자연스러운 문단으로 구성하여 길고 상세하게 작성하세요
- 대출 상품 추천 시에는 구체적인 상품명(가계대출, 주택담보대출, 전월세보증금대출 등)을 명시하세요
- 70대 고객에게는 연령대에 맞는 대출 상품을 구체적으로 추천하세요
- 대출 상담 질문에는 반드시 구체적인 대출 상품명을 추천하고, 단계별 설명이나 일반적인 조언은 피하세요
- 고객에게 직접적인 대출 상품 추천을 제공하세요

답변:
"""
        return await self.call_gpt(prompt)
    
    async def call_gpt(self, prompt: str) -> str:
        """GPT API 호출"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return "죄송합니다. 답변 생성 중 오류가 발생했습니다."
                
        except Exception as e:
            print(f"GPT API error: {e}")
            return "죄송합니다. 답변 생성 중 오류가 발생했습니다."
