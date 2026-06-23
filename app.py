import streamlit as st
import streamlit.components.v1 as components
import io, os, json, re
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="웰파인 AI 회의실", page_icon="🤖", layout="wide",
                   initial_sidebar_state="expanded")

CFG_FILE = "wellfine_config.json"
def load_cfg():
    try:
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}
def save_cfg(data):
    try:
        with open(CFG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#f5f1eb;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#ece8e0; min-width:260px;}
#MainMenu,footer{visibility:hidden;}
[data-testid="stFileUploader"]{
  opacity:0 !important;height:0 !important;overflow:hidden !important;
  margin:0 !important;padding:0 !important;position:absolute !important;
}
/* 결론 슬라이드 패널 */
[data-testid="stSidebarContent"] .result-panel{
  font-size:13px;line-height:1.7;
}
</style>
""", unsafe_allow_html=True)

PROVIDERS = {
    "🟠 Claude (Anthropic)": {"key": "anthropic", "models": {
        "Claude Sonnet (기본)": "claude-sonnet-4-6",
        "Claude Opus (고성능)": "claude-opus-4-8",
        "Claude Haiku (빠름)": "claude-haiku-4-5-20251001",
    }},
    "🟢 ChatGPT (OpenAI)": {"key": "openai", "models": {
        "GPT-4o (권장)": "gpt-4o",
        "GPT-4o mini (빠름)": "gpt-4o-mini",
    }},
    "🔵 Gemini (Google)": {"key": "gemini", "models": {
        "Gemini 2.5 Flash (무료/빠름)": "gemini-2.5-flash",
        "Gemini 2.5 Pro (고성능)": "gemini-2.5-pro",
        "Gemini 1.5 Flash": "gemini-1.5-flash",
    }},
}

BOTS = [
    {"name": "노무봇",  "system": "웰파인(강원도 횡성 건강기능식품 OEM/ODM) 인사총무팀 노무 전문 AI.\n성격: 보수적이고 까다로운 노무사 스타일.\n- 법 조문 근거 없이 괜찮다고 하지 마세요\n- 애매하면 반드시 전문가 확인 필요 명시\n- 근로기준법, 노동관련 법령 관점으로 검토\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "HRM봇",  "system": "웰파인 인사총무팀 HRM 전문 AI.\n성격: 원칙주의자.\n- 사내 규정, 취업규칙과의 일치 여부 체크\n- 규정과 실제 운영 간의 괴리를 찾아내세요\n- 형평성 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "채용봇",  "system": "웰파인 인사총무팀 채용 전문 AI.\n성격: 현실주의자.\n- 강원도 횡성 지역의 지원자 풀이 제한적임 감안\n- JD의 모호한/차별적 표현 찾아내세요\n- 채용 과정의 법적 문제 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "계약봇",  "system": "웰파인 인사총무팀 계약 전문 AI.\n성격: 의심 많은 변호사 스타일.\n- 계약서 조항 꼼꼼하게 분석\n- 불리한 조항/모호한 표현 찾아내세요\n- 해지/갱신 조항 리스크 집중 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "총무봇",  "system": "웰파인 인사총무팀 총무 전문 AI.\n성격: 꼼꼼한 살림꾼.\n- 비용 처리, 시설, 물품 관련 규정 준수 체크\n- 세무적으로 문제없는지 검토\n- 내부 결재/승인 프로세스 확인\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "급여봇",  "system": "웰파인 인사총무팀 급여/4대보험 전문 AI.\n성격: 숫자에 목숨 거는 스타일.\n- 급여 계산과 공제 항목 정확성 체크\n- 4대보험 요율과 신고 기한 확인\n- E-9 비자 외국인 근로자의 특수한 처리 체크\n- 핵심 포인트 번호 목록으로 제시"},
    {"name": "교육봇",  "system": "웰파인 인사총무팀 교육/OJT 전문 AI.\n성격: 실용주의 교육자.\n- 교육 내용이 실제 업무와 연결되는지 체크\n- OJT/수습평가 설계의 공정성 확인\n- 외국인 근로자 교육 시 언어/문화 차이 고려\n- 핵심 포인트 번호 목록으로 제시"},
]

FACTCHECK_SYS = (
    "웰파인 인사총무팀 팩트체크 AI. 감정 없는 검사 스타일.\n\n"
    "반드시 아래 실제 법령/규정 기준으로 검증하세요:\n"
    "- 근로기준법 (근로시간, 수습, 해고, 휴가, 임금 관련)\n"
    "- 최저임금법\n"
    "- 근로자퇴직급여보장법\n"
    "- 고용보험법 / 산재보험법 / 국민연금법 / 국민건강보험법\n"
    "- 남녀고용평등과 일·가정 양립 지원에 관한 법률\n"
    "- 외국인근로자의 고용 등에 관한 법률 (E-9 비자, 고용허가제)\n"
    "- 채용절차의 공정화에 관한 법률\n"
    "- 개인정보 보호법\n"
    "- 업로드된 문서가 있으면 해당 내용도 기준으로 포함\n\n"
    "각 봇 의견에 대해 [맞음/틀림/확인필요] 판정 후 근거 법령 조문 명시."
)

FIELD_SYS = (
    "웰파인 인사총무팀 실무 전문 AI. 성격: 현장 경험 많은 선배.\n"
    "- '이론은 맞는데 실제로 가능해?' 관점으로 접근\n"
    "- 직원 입장에서 이 결정을 받아들일 수 있는지 시뮬레이션\n"
    "- 강원도 횡성 제조업 현장 특성 감안\n"
    "- 현실적으로 실행 가능한 방향 제시"
)

FINAL_SYS = (
    "웰파인 인사총무팀 AI 회의 최종 정리 AI. 냉철한 회의 진행자.\n"
    "- 모든 봇 의견 종합해 결론 도출\n"
    "- 의견 충돌한 부분은 양쪽 모두 명시\n"
    "- 구체적 액션 아이템을 우선순위 순서로 제시\n"
    "- 전문가 확인 반드시 필요한 사항 명시\n\n"
    "다음 형식으로 작성:\n"
    "## 핵심 결론\n## 주요 리스크\n## 액션 아이템 (우선순위 순)\n## 전문가 확인 필요 사항"
)

SCREEN_SYS = (
    "웰파인 HR AI 회의 코디네이터. 이번 안건과 관련 있는 봇만 골라주세요.\n\n"
    "봇 전문 영역:\n"
    "- 노무봇: 근로기준법, 수습/해고/징계, 근로시간, 퇴직, 실업급여, 노동 법령\n"
    "- HRM봇: 인사관리, 사내규정, 취업규칙, 인사제도, 평가\n"
    "- 채용봇: 채용공고/JD, 면접, 지원자 선발, 채용 프로세스\n"
    "- 계약봇: 근로계약서, 용역계약, 협약서 등 계약 문서\n"
    "- 총무봇: 비용처리/법인카드, 시설관리, 물품/소모품, 세금계산서\n"
    "- 급여봇: 급여 계산, 임금, 4대보험, 원천징수, 퇴직금, 수당\n"
    "- 교육봇: OJT, 수습평가, 직원교육, 교육훈련\n\n"
    '{"노무봇":true,"HRM봇":false,"채용봇":false,"계약봇":false,'
    '"총무봇":false,"급여봇":false,"교육봇":false} 형태로만 응답하세요.'
)

BOT_COLORS = {
    "노무봇":     ["#3B6FD4","#2756B8"],
    "HRM봇":      ["#2E9E55","#1E7D3E"],
    "채용봇":     ["#E07B00","#B86000"],
    "계약봇":     ["#7048E8","#5030C8"],
    "총무봇":     ["#546E8A","#3D5570"],
    "급여봇":     ["#C79800","#A07800"],
    "교육봇":     ["#0A9E7A","#087D60"],
    "팩트체크봇": ["#C92A2A","#A01E1E"],
    "실무봇":     ["#7B5E3C","#5A4228"],
    "최종정리봇": ["#1565C0","#0D47A0"],
}

def call_bot(pkey, api_key, model, system, content, max_tokens=700):
    combined = system + "\n\n" + content
    try:
        if pkey == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(model=model, max_tokens=max_tokens,
                system=system, messages=[{"role": "user", "content": content}])
            return resp.content[0].text
        elif pkey == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(model=model, max_tokens=max_tokens,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": content}])
            return resp.choices[0].message.content
        elif pkey == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            resp = genai.GenerativeModel(model).generate_content(combined)
            return resp.text
    except Exception as e:
        return f"오류: {e}"
    return "지원하지 않는 제공자."

def extract_text(f):
    if not f:
        return ""
    ext = f.name.split(".")[-1].lower()
    try:
        if ext == "txt":
            return f.read().decode("utf-8", errors="ignore")
        elif ext == "pdf":
            import pypdf
            r = pypdf.PdfReader(io.BytesIO(f.read()))
            return "\n".join(p.extract_text() or "" for p in r.pages)
        elif ext in ("docx", "doc"):
            from docx import Document
            d = Document(io.BytesIO(f.read()))
            return "\n".join(p.text for p in d.paragraphs)
    except Exception as e:
        return f"[파일 오류: {e}]"
    return ""

def build_content(doc_text, question, case_notes):
    parts = []
    if case_notes.strip():
        parts.append("[웰파인 누적 케이스]\n" + case_notes.strip())
    if doc_text.strip():
        parts.append("[문서]\n" + doc_text[:3000])
    if question.strip():
        parts.append("[질문/검토 요청]\n" + question.strip())
    return "\n\n".join(parts)

def render_html(statuses, results, doc_name=""):
    data_json = json.dumps({"statuses": statuses, "results": results,
                            "colors": BOT_COLORS, "doc": doc_name}, ensure_ascii=False)
    return ("""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#f5f1eb;font-family:-apple-system,sans-serif;padding:8px;}
.room{background:linear-gradient(180deg,#e8e2d6,#dfd9cd);border-radius:16px;
  padding:18px 8px 12px;border:1px solid #cec8be;}
.row{display:flex;justify-content:center;align-items:flex-end;gap:6px;}
.mid{display:flex;justify-content:center;align-items:center;gap:8px;margin:2px 0;}
.conf-wrap{display:flex;align-items:center;gap:6px;}
.conf-main{flex:1;min-width:0;}
.chair-col{display:flex;flex-direction:column;align-items:center;justify-content:center;padding-left:4px;}
.table{flex:0 0 auto;width:290px;min-height:90px;
  background:linear-gradient(160deg,#6B4423,#8B5E3C 40%,#9B6B45 60%,#6B4423);
  border-radius:10px;border:3px solid #4A2E18;
  box-shadow:0 6px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.12);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;}
.table-lbl{color:rgba(255,255,255,.45);font-size:9px;letter-spacing:2px;text-transform:uppercase;}
.upload-zone{background:rgba(255,255,255,.12);border:1.5px dashed rgba(255,255,255,.5);
  border-radius:7px;padding:6px 20px;cursor:pointer;text-align:center;
  transition:all .2s;min-width:200px;}
.upload-zone:hover,.upload-zone.drag-over{background:rgba(255,255,255,.22);
  border-color:rgba(255,255,255,.85);}
.upload-plus{font-size:18px;color:rgba(255,255,255,.65);font-weight:300;line-height:1;}
.upload-txt{font-size:8.5px;color:rgba(255,255,255,.6);line-height:1.5;margin-top:2px;}
.doc-card{background:rgba(255,255,255,.88);border-radius:4px;padding:3px 10px;
  font-size:9px;color:#3a2800;max-width:230px;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;border:1px solid rgba(255,255,255,.5);cursor:pointer;}
.doc-card:hover{background:rgba(255,255,255,.98);}
.bot{display:flex;flex-direction:column;align-items:center;width:64px;position:relative;
  cursor:pointer;transition:transform .15s;}
.bot:hover{transform:scale(1.08);}
.bot-name{font-size:9.5px;font-weight:700;color:#3a3530;margin-top:2px;text-align:center;}
.dot{width:7px;height:7px;border-radius:50%;margin-top:2px;background:#bbb;}
.idle .dot{background:#bbb;}
.active .dot{background:#f5c842;box-shadow:0 0 8px #f5c842;animation:blink .9s infinite;}
.done .dot{background:#52c463;box-shadow:0 0 5px #52c463;}
.error .dot{background:#e05555;}
.skip{opacity:0.28;filter:grayscale(80%);cursor:default !important;}
.skip .dot{background:#ccc !important;box-shadow:none !important;}
.bubble{position:absolute;bottom:calc(100% + 4px);left:50%;transform:translateX(-50%);
  background:#fff9e6;border:1.5px solid #f5c842;border-radius:8px;padding:3px 7px;
  font-size:9px;font-weight:800;color:#6B4A00;white-space:nowrap;
  box-shadow:0 3px 8px rgba(0,0,0,.15);animation:float 1.5s ease-in-out infinite;z-index:5;}
.bubble::after{content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);
  border:5px solid transparent;border-top-color:#f5c842;}
.chair-area{display:flex;justify-content:center;margin-top:8px;
  padding-top:8px;border-top:1px dashed #c0b8ae;}
.chair-wrap{background:rgba(255,255,255,.65);border-radius:10px;padding:6px 16px;
  display:inline-flex;align-items:center;gap:8px;border:1px solid #d8d0c8;
  cursor:pointer;transition:transform .15s;}
.chair-wrap:hover{transform:scale(1.04);}
.chair-info{display:flex;flex-direction:column;}
.chair-title{font-size:11px;font-weight:700;color:#3a3530;}
.chair-sub{font-size:9px;color:#aaa;font-style:italic;}
.overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;
  background:rgba(0,0,0,.55);z-index:100;align-items:center;justify-content:center;}
.overlay.show{display:flex;}
.modal{background:#fff;border-radius:14px;padding:20px 22px;width:90%;max-width:540px;
  max-height:82vh;overflow-y:auto;position:relative;
  box-shadow:0 12px 40px rgba(0,0,0,.3);}
.modal-hdr{display:flex;align-items:center;gap:10px;margin-bottom:12px;
  padding-bottom:8px;border-bottom:2px solid #eee;}
.modal-hdr h2{font-size:14px;font-weight:700;color:#333;margin:0;}
.modal-body{font-size:13px;line-height:1.75;color:#444;}
.modal-body h2,.modal-body h3{font-size:13px;font-weight:700;margin:10px 0 4px;color:#222;}
.modal-body p{margin:4px 0;}
.modal-body ul,.modal-body ol{padding-left:18px;margin:4px 0;}
.modal-body li{margin:3px 0;}
.modal-body strong{color:#222;}
.close-btn{position:absolute;top:10px;right:14px;cursor:pointer;
  font-size:18px;color:#aaa;background:none;border:none;line-height:1;padding:2px 6px;
  border-radius:4px;}
.close-btn:hover{background:#f0f0f0;color:#333;}
.no-result{font-size:12px;color:#aaa;font-style:italic;padding:20px 0;text-align:center;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.3;}}
@keyframes float{0%,100%{transform:translateX(-50%) translateY(0);}
  50%{transform:translateX(-50%) translateY(-3px);}}
</style>
</head><body>
<div class="room" id="room"></div>
<div class="overlay" id="overlay" onclick="maybeClose(event)">
  <div class="modal" id="modal">
    <button class="close-btn" onclick="closeModal()">&#x2715;</button>
    <div class="modal-hdr">
      <div id="modal-icon"></div>
      <h2 id="modal-title"></h2>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>
<script>
const DATA=""" + data_json + """;
const COLORS=DATA.colors;

function svgRobot(name,sz){
  const s=sz||52;
  const c=(COLORS[name]||["#666","#444"]);
  const C=c[0],D=c[1];
  return `<svg width="${s}" height="${Math.round(s*1.18)}" viewBox="0 0 52 62" xmlns="http://www.w3.org/2000/svg">
    <rect x="22" y="1" width="8" height="10" rx="4" fill="${C}"/>
    <circle cx="26" cy="1" r="5.5" fill="${C}"/>
    <rect x="3" y="10" width="46" height="31" rx="10" fill="${C}"/>
    <circle cx="1" cy="26" r="5" fill="${D}"/>
    <circle cx="51" cy="26" r="5" fill="${D}"/>
    <rect x="8" y="16" width="14" height="13" rx="4.5" fill="white" opacity="0.95"/>
    <rect x="30" y="16" width="14" height="13" rx="4.5" fill="white" opacity="0.95"/>
    <circle cx="15" cy="22.5" r="4.5" fill="${C}"/>
    <circle cx="37" cy="22.5" r="4.5" fill="${C}"/>
    <circle cx="15" cy="22.5" r="2.5" fill="#111"/>
    <circle cx="37" cy="22.5" r="2.5" fill="#111"/>
    <circle cx="16.8" cy="20.8" r="1.1" fill="white"/>
    <circle cx="38.8" cy="20.8" r="1.1" fill="white"/>
    <rect x="15" y="33" width="22" height="4.5" rx="2.2" fill="rgba(255,255,255,0.38)"/>
    <rect x="20" y="41" width="12" height="6" fill="${C}"/>
    <rect x="1" y="47" width="50" height="15" rx="9 9 0 0" fill="${D}"/>
    <rect x="17" y="50" width="18" height="8" rx="4" fill="${C}" opacity="0.5"/>
    <circle cx="26" cy="54" r="2.5" fill="rgba(255,255,255,0.65)"/>
  </svg>`;
}

function botCard(name,status){
  const isSkip=status==='skip';
  const bubble=status==='active'?'<div class="bubble">&#x1F4AC; \\uBC1C\\uC5B8 \\uC911</div>':'';
  const onclick=isSkip?'':('onclick="showBot(\\'' + name + '\\')"');
  return '<div class="bot ' + status + '" ' + onclick + '>'
    + bubble + svgRobot(name)
    + '<div class="bot-name">' + name + '</div>'
    + '<div class="dot"></div></div>';
}

function triggerUpload(){
  try{
    const fi=window.parent.document.querySelector('input[data-testid="stFileUploaderDropzoneInput"]');
    if(fi) fi.click();
  }catch(e){console.log('upload trigger error',e);}
}
function attachUploadHandlers(){
  const z=document.getElementById('uploadZone');
  if(!z)return;
  z.addEventListener('click',function(e){e.stopPropagation();triggerUpload();});
  z.addEventListener('dragover',function(e){e.preventDefault();z.classList.add('drag-over');});
  z.addEventListener('dragleave',function(){z.classList.remove('drag-over');});
  z.addEventListener('drop',function(e){
    e.preventDefault();z.classList.remove('drag-over');
    const files=e.dataTransfer.files;
    if(!files.length)return;
    try{
      const dt=new DataTransfer();dt.items.add(files[0]);
      const fi=window.parent.document.querySelector('input[data-testid="stFileUploaderDropzoneInput"]');
      if(fi){fi.files=dt.files;fi.dispatchEvent(new Event('change',{bubbles:true}));}
    }catch(err){console.log('drop error',err);}
  });
}
function render(){
  const st=DATA.statuses;
  const g=n=>st[n]||'idle';
  const topRow=['\\ub178\\ubb34\\ubd07','HRM\\ubd07','\\ucc44\\uc6a9\\ubd07','\\uacc4\\uc57d\\ubd07'].map(n=>botCard(n,g(n))).join('');
  const btmRow=['\\ucd1d\\ubb34\\ubd07','\\uae09\\uc5ec\\ubd07','\\uad50\\uc721\\ubd07'].map(n=>botCard(n,g(n))).join('');
  const cs=g('\\ucd5c\\uc885\\uc815\\ub9ac\\ubd07');
  const cColor={idle:'#bbb',active:'#f5c842',done:'#52c463',error:'#e05555'}[cs]||'#bbb';
  const cGlow=cs!=='idle'?'box-shadow:0 0 7px '+cColor+';':'';
  const cBubble=cs==='active'?'<div class="bubble">&#x1F4AC; \\ubc1c\\uc5b8 \\uc911</div>':'';
  const tableInner=DATA.doc
    ?'<div class="doc-card" onclick="triggerUpload()">&#x1F4C4; '+DATA.doc+'</div>'
    :'<div class="upload-zone" id="uploadZone">'
      +'<div class="upload-plus">+</div>'
      +'<div class="upload-txt">\\ubb38\\uc11c \\ub4dc\\ub798\\uadf8 or<br>\\ud074\\ub9ad\\ud574\\uc11c \\uc5c5\\ub85c\\ub4dc</div>'
    +'</div>';
  const chairHtml=
    '<div class="chair-col">'
      +'<div class="chair-wrap" onclick="showBot(\\'\\ucd5c\\uc885\\uc815\\ub9ac\\ubd07\\')">'
        +cBubble+svgRobot('\\ucd5c\\uc885\\uc815\\ub9ac\\ubd07',44)
        +'<div class="chair-info">'
          +'<div class="chair-title">\\ucd5c\\uc885\\uc815\\ub9ac\\ubd07</div>'
          +'<div class="chair-sub">\\ud68c\\uc758 \\uc9c4\\ud589\\uc790</div>'
        +'</div>'
        +'<div class="dot" style="background:'+cColor+';'+cGlow+'"></div>'
      +'</div>'
    +'</div>';
  document.getElementById('room').innerHTML=
    '<div class="conf-wrap">'
      +'<div class="conf-main">'
        +'<div class="row">'+topRow+'</div>'
        +'<div class="mid">'
          +botCard('\\ud31d\\ud2b8\\uccb4\\ud06c\\ubd07',g('\\ud31d\\ud2b8\\uccb4\\ud06c\\ubd07'))
          +'<div class="table"><div class="table-lbl">WELLFINE HR AI</div>'+tableInner+'</div>'
          +botCard('\\uc2e4\\ubb34\\ubd07',g('\\uc2e4\\ubb34\\ubd07'))
        +'</div>'
        +'<div class="row">'+btmRow+'</div>'
      +'</div>'
      +chairHtml
    +'</div>';
  attachUploadHandlers();
}

function showBot(name){
  const result=DATA.results&&DATA.results[name];
  document.getElementById('modal-icon').innerHTML=svgRobot(name,32);
  document.getElementById('modal-title').textContent=name;
  if(result){
    document.getElementById('modal-body').innerHTML=marked.parse(result);
  } else {
    const st2=DATA.statuses[name]||'idle';
    const msg=st2==='active'?'\\uc9c0\\uae08 \\ubc1c\\uc5b8 \\uc911\\uc785\\ub2c8\\ub2e4...':'\\uc544\\uc9c1 \\uc758\\uacac\\uc774 \\uc5c6\\uc2b5\\ub2c8\\ub2e4.';
    document.getElementById('modal-body').innerHTML='<div class="no-result">'+msg+'</div>';
  }
  document.getElementById('overlay').classList.add('show');
}
function closeModal(){document.getElementById('overlay').classList.remove('show');}
function maybeClose(e){if(e.target===document.getElementById('overlay'))closeModal();}
render();
</script>
</body></html>""")

# ── 세션 초기화 ────────────────────────────────────────────
_cfg = load_cfg()
for k, v in [
    ("bot_statuses", {}), ("bot_results", {}), ("case_notes", ""),
    ("stop_requested", False), ("meeting_running", False),
    ("meeting_history", []), ("renaming_idx", None), ("current_doc", ""),
    ("show_result_panel", False), ("last_final", ""),
    ("saved_provider", _cfg.get("provider", list(PROVIDERS.keys())[0])),
    ("saved_model",    _cfg.get("model", "")),
    ("saved_api_key",  _cfg.get("api_key", "")),
]:
    if k not in st.session_state:
        st.session_state[k] = v
if "bot_prompts" not in st.session_state:
    bp0 = {b["name"]: b["system"] for b in BOTS}
    bp0.update({"팩트체크봇": FACTCHECK_SYS, "실무봇": FIELD_SYS, "최종정리봇": FINAL_SYS})
    st.session_state.bot_prompts = bp0

# ── 현재 설정값 도출 ───────────────────────────────────────
_p = st.session_state.saved_provider
if _p not in PROVIDERS:
    _p = list(PROVIDERS.keys())[0]
_prov    = PROVIDERS[_p]
_pkey    = _prov["key"]
_ml      = st.session_state.saved_model
if _ml not in _prov["models"]:
    _ml = list(_prov["models"].keys())[0]
_model   = _prov["models"][_ml]
_api_key = st.session_state.saved_api_key
if not _api_key:
    try:
        smap = {"anthropic": "ANTHROPIC_API_KEY",
                "openai":    "OPENAI_API_KEY",
                "gemini":    "GEMINI_API_KEY"}
        _api_key = st.secrets.get(smap[_pkey], "")
    except Exception:
        _api_key = ""

# ── 설정 다이얼로그 ────────────────────────────────────────
@st.dialog("⚙️ 설정", width="large")
def show_settings():
    tab1, tab2, tab3 = st.tabs(["🔌 AI 연결", "🤖 봇 프롬프트", "📂 케이스 메모"])
    with tab1:
        pl = st.selectbox("AI 제공자", list(PROVIDERS.keys()),
            index=(list(PROVIDERS.keys()).index(st.session_state.saved_provider)
                   if st.session_state.saved_provider in PROVIDERS else 0))
        pt = PROVIDERS[pl]; pkt = pt["key"]
        mll = list(pt["models"].keys())
        saved_m = st.session_state.saved_model
        ml = st.selectbox("모델", mll,
                          index=mll.index(saved_m) if saved_m in mll else 0)
        ph = {"anthropic": "sk-ant-...", "openai": "sk-...",
              "gemini": "AIza..."}.get(pkt, "")
        ak = st.text_input("API 키 (팀 공유)", type="password",
                           value=st.session_state.saved_api_key, placeholder=ph)
        st.caption("팀원 모두가 이 키로 사용합니다.")
        if st.button("💾 저장", type="primary", use_container_width=True):
            st.session_state.saved_provider = pl
            st.session_state.saved_model    = ml
            st.session_state.saved_api_key  = ak
            save_cfg({"provider": pl, "model": ml, "api_key": ak})
            st.rerun()
    with tab2:
        all_names = ([b["name"] for b in BOTS]
                     + ["팩트체크봇", "실무봇", "최종정리봇"])
        bs = st.selectbox("봇 선택", all_names)
        ed = st.text_area("프롬프트",
                          value=st.session_state.bot_prompts.get(bs, ""), height=220)
        if st.button("💾 프롬프트 저장", use_container_width=True):
            st.session_state.bot_prompts[bs] = ed
            st.rerun()
    with tab3:
        st.caption("모든 회의에 기본 콘텍스트로 포함됩니다.")
        nn = st.text_area("누적 케이스", value=st.session_state.case_notes,
                          height=200,
                          placeholder="수습 불합격 시 면담 2회 이상 기록 필요...")
        if st.button("💾 케이스 저장", use_container_width=True):
            st.session_state.case_notes = nn
            st.rerun()

# ── 왼쪽 사이드바: 히스토리 ───────────────────────────────
with st.sidebar:
    st.markdown("## 📜 회의 히스토리")
    if not st.session_state.meeting_history:
        st.info("회의를 진행하면\n여기에 기록이 쌓입니다.", icon="📋")
    else:
        for i, h in enumerate(reversed(st.session_state.meeting_history)):
            real_idx = len(st.session_state.meeting_history) - 1 - i
            title = h.get("title", "회의")
            label = (title[:20] + "…") if len(title) > 20 else title
            with st.expander(f"#{real_idx+1}  {label}", expanded=False):
                r_col, d_col = st.columns(2)
                with r_col:
                    if st.button("✏️ 이름", key=f"ren_{real_idx}",
                                 use_container_width=True):
                        st.session_state.renaming_idx = real_idx
                        st.rerun()
                with d_col:
                    if st.button("🗑️ 삭제", key=f"del_{real_idx}",
                                 use_container_width=True):
                        st.session_state.meeting_history.pop(real_idx)
                        if st.session_state.renaming_idx == real_idx:
                            st.session_state.renaming_idx = None
                        st.rerun()
                if st.session_state.renaming_idx == real_idx:
                    new_name = st.text_input(
                        "새 이름", value=h.get("title", ""),
                        key=f"ri_{real_idx}", label_visibility="collapsed")
                    s_col, c_col = st.columns(2)
                    with s_col:
                        if st.button("저장", key=f"rs_{real_idx}",
                                     use_container_width=True):
                            st.session_state.meeting_history[real_idx]["title"] = new_name
                            st.session_state.renaming_idx = None
                            st.rerun()
                    with c_col:
                        if st.button("취소", key=f"rc_{real_idx}",
                                     use_container_width=True):
                            st.session_state.renaming_idx = None
                            st.rerun()
                st.caption(h["time"])
                if h.get("doc"):
                    st.markdown(f"📄 `{h['doc']}`")
                st.markdown(f"**Q:** {h['question']}")
                if h.get("ops1"):
                    st.markdown("---")
                    for bn, op in h["ops1"].items():
                        with st.expander(f"🤖 {bn} 1차", expanded=False):
                            st.markdown(op)
                if h.get("fc1"):
                    with st.expander("🔍 팩트체크 1차", expanded=False):
                        st.markdown(h["fc1"])
                if h.get("ops2"):
                    for bn, op in h["ops2"].items():
                        with st.expander(f"🤖 {bn} 2차", expanded=False):
                            st.markdown(op)
                if h.get("fc2"):
                    with st.expander("🔍 팩트체크 최종", expanded=False):
                        st.markdown(h["fc2"])
                if h.get("final"):
                    st.markdown("---")
                    st.markdown("**🎯 최종 결론**")
                    st.markdown(h["final"])

# ── 메인 레이아웃 ──────────────────────────────────────────
# 최종 결론 패널이 열려 있으면 2컬럼 (테이블 | 결론), 아니면 풀 너비
if st.session_state.show_result_panel and st.session_state.last_final:
    main_col, result_col = st.columns([3, 2])
else:
    main_col = st.container()
    result_col = None

with main_col:
    col_title, col_cfg = st.columns([5, 1])
    with col_title:
        st.markdown("## 🏢 웰파인 인사총무 AI 회의실")
        api_status = " ✅" if _api_key else " ⚠️ API키 미입력"
        st.caption(f"설정: {_p.split()[-1]} · {_ml}" + api_status)
    with col_cfg:
        st.write("")
        if st.button("⚙️ 설정", use_container_width=True):
            show_settings()

    st.divider()

    table_slot = st.empty()
    with table_slot:
        components.html(
            render_html(st.session_state.bot_statuses,
                        st.session_state.bot_results,
                        st.session_state.current_doc),
            height=470)

    # 숨겨진 파일 업로더 (테이블 JS가 트리거)
    ufile = st.file_uploader(
        "문서", type=["pdf", "docx", "txt"],
        label_visibility="collapsed", key="doc_upload")
    if ufile:
        if st.session_state.current_doc != ufile.name:
            st.session_state.current_doc = ufile.name
            st.rerun()

    st.divider()
    st.markdown("##### 💬 질문 / 검토 요청")
    question = st.text_area(
        "질문", height=80, label_visibility="collapsed",
        placeholder="예: 이 근로계약서 수습기간 조항이 법적으로 문제없나요?")

    btn_c1, btn_c2 = st.columns([3, 1])
    with btn_c1:
        go = st.button("🚀 회의 시작", type="primary",
                       use_container_width=True,
                       disabled=st.session_state.meeting_running)
    with btn_c2:
        if st.button("⏹ 중단", use_container_width=True,
                     disabled=not st.session_state.meeting_running):
            st.session_state.stop_requested = True
            st.session_state.meeting_running = False
            st.rerun()

# 결론 슬라이드 패널 (오른쪽)
if result_col is not None:
    with result_col:
        st.markdown("### 🎯 최종 결론")
        if st.button("✕ 닫기", key="close_result"):
            st.session_state.show_result_panel = False
            st.rerun()
        st.markdown("---")
        st.markdown(st.session_state.last_final)

# ── 헬퍼 함수들 ───────────────────────────────────────────
def upd(statuses_update, results_update=None):
    st.session_state.bot_statuses.update(statuses_update)
    if results_update:
        st.session_state.bot_results.update(results_update)
    with table_slot:
        components.html(
            render_html(st.session_state.bot_statuses,
                        st.session_state.bot_results,
                        st.session_state.current_doc),
            height=490)

def check_stop():
    if st.session_state.stop_requested:
        st.warning("⏹ 회의가 중단되었습니다. "
                   "테이블의 봇을 클릭하면 완료된 결과를 확인할 수 있습니다.")
        st.stop()

# ── 회의 진행 ──────────────────────────────────────────────
if go:
    if not _api_key:
        st.error("⚙️ 설정에서 API 키를 입력하고 저장해주세요.")
        st.stop()
    if not ufile and not question.strip():
        st.error("문서를 업로드하거나 질문을 입력해주세요.")
        st.stop()

    st.session_state.bot_statuses   = {}
    st.session_state.bot_results    = {}
    st.session_state.stop_requested  = False
    st.session_state.meeting_running = True
    st.session_state.show_result_panel = False

    doc_text = extract_text(ufile) if ufile else ""
    content  = build_content(doc_text, question, st.session_state.case_notes)
    bp       = st.session_state.bot_prompts

    st.divider()
    st.markdown("### 📋 회의 진행")

    # 봇 선별 (관련 없는 봇 제외)
    active_bots = BOTS[:]
    skipped = []
    with st.spinner("🔍 안건 분석 — 관련 봇 선별 중..."):
        try:
            screen_res = call_bot(_pkey, _api_key, _model,
                                  SCREEN_SYS, content[:600], 150)
            m = re.search(r"\{[^{}]+\}", screen_res, re.DOTALL)
            relevant    = json.loads(m.group()) if m else {}
            active_bots = [b for b in BOTS if relevant.get(b["name"], True)]
            skipped     = [b["name"] for b in BOTS
                           if not relevant.get(b["name"], True)]
        except Exception:
            pass
    if skipped:
        st.info("💤 이번 안건과 직접 관련 없어 제외된 봇: **"
                + ", ".join(skipped) + "**")
        upd({n: "skip" for n in skipped})
    n_active = len(active_bots)

    # 1라운드
    st.markdown(f"**1라운드 — 전문 봇 {n_active}명 동시 발언**")
    upd({b["name"]: "active" for b in active_bots})
    ops1 = {}
    with st.spinner(f"🤖 {n_active}명 동시 분석 중..."):
        def _call1(b):
            return b["name"], call_bot(
                _pkey, _api_key, _model,
                bp.get(b["name"], b["system"]), content, 600)
        with ThreadPoolExecutor(max_workers=max(1, n_active)) as ex:
            for name, res in ex.map(_call1, active_bots):
                ops1[name] = res
    upd({b["name"]: "done" for b in active_bots}, ops1)
    for b in active_bots:
        with st.expander(f"🤖 {b['name']} 1차 의견", expanded=False):
            st.markdown(ops1[b["name"]])

    check_stop()

    # 팩트체크 1차
    st.markdown("**팩트체크 1차**")
    fc1_in = (content + "\n\n[1차 의견]\n"
              + "\n\n".join(f"{n}:\n{o}" for n, o in ops1.items()))
    upd({"팩트체크봇": "active"})
    with st.status("🤖 팩트체크봇 1차 검증 중...",
                   expanded=False) as stat:
        fc1 = call_bot(_pkey, _api_key, _model,
                       bp.get("팩트체크봇", FACTCHECK_SYS),
                       fc1_in, 900)
        st.markdown(fc1)
        stat.update(label="🤖 팩트체크봇 1차 ✅",
                    state="complete", expanded=False)
    upd({"팩트체크봇": "done"}, {"팩트체크봇_1차": fc1})

    check_stop()

    # 2라운드
    st.markdown(f"**2라운드 — 팩트체크 반영 재발언 ({n_active}명 병렬)**")
    upd({b["name"]: "active" for b in active_bots})
    ops2 = {}
    with st.spinner(f"🤖 {n_active}명 재검토 중..."):
        def _call2(b):
            r2_in = (content
                     + f"\n\n[팩트체크 결과]\n{fc1}"
                     + "\n\n[내 1차 의견]\n" + ops1.get(b["name"], "")
                     + "\n\n팩트체크 반영해 의견을 "
                       "보완하거나 수정해주세요.")
            return b["name"], call_bot(
                _pkey, _api_key, _model,
                bp.get(b["name"], b["system"]), r2_in, 600)
        with ThreadPoolExecutor(max_workers=max(1, n_active)) as ex:
            for name, res in ex.map(_call2, active_bots):
                ops2[name] = res
    upd({b["name"]: "done" for b in active_bots}, ops2)
    for b in active_bots:
        with st.expander(f"🤖 {b['name']} 2차 의견", expanded=False):
            st.markdown(ops2[b["name"]])

    check_stop()

    # 팩트체크 2차
    st.markdown("**팩트체크 2차 (최종 검증)**")
    fc2_in = (content + "\n\n[2차 의견]\n"
              + "\n\n".join(f"{n}:\n{o}" for n, o in ops2.items())
              + f"\n\n[1차 팩트체크]\n{fc1}")
    upd({"팩트체크봇": "active"})
    with st.status("🤖 팩트체크봇 최종 검증 중...",
                   expanded=False) as stat:
        fc2 = call_bot(_pkey, _api_key, _model,
                       bp.get("팩트체크봇", FACTCHECK_SYS),
                       fc2_in, 900)
        st.markdown(fc2)
        stat.update(label="🤖 팩트체크봇 최종 ✅",
                    state="complete", expanded=False)
    upd({"팩트체크봇": "done"}, {"팩트체크봇_2차": fc2})

    check_stop()

    # 실무봇
    upd({"실무봇": "active"})
    field_in = (content
                + "\n\n[전문 봇 최종 의견]\n"
                + "\n".join(f"{n}: {o[:200]}" for n, o in ops2.items())
                + f"\n\n[팩트체크 최종]\n{fc2}"
                + "\n\n현장 실무 관점에서 3줄 "
                  "이내로 핵심 코멘트만 작성해주세요.")
    with st.spinner("🤖 실무봇 코멘트 작성 중..."):
        field_brief = call_bot(_pkey, _api_key, _model,
                               bp.get("실무봇", FIELD_SYS),
                               field_in, 200)
    upd({"실무봇": "done"}, {"실무봇": field_brief})

    # 최종정리봇
    final_in = (content
                + "\n\n[전문 봇 2차 최종 의견]\n"
                + "\n\n".join(f"{n}:\n{o}" for n, o in ops2.items())
                + f"\n\n[팩트체크 최종 결과]\n{fc2}"
                + f"\n\n[실무 현장 코멘트]\n{field_brief}")
    upd({"최종정리봇": "active"})
    with st.spinner("🤖 최종정리봇 정리 중..."):
        final_res = call_bot(_pkey, _api_key, _model,
                             bp.get("최종정리봇", FINAL_SYS),
                             final_in, 1500)
    upd({"최종정리봇": "done"}, {"최종정리봇": final_res})

    st.session_state.meeting_running    = False
    st.session_state.last_final         = final_res
    st.session_state.show_result_panel  = True

    from datetime import datetime
    title = (ufile.name if ufile else question.strip()[:30])
    st.session_state.meeting_history.append({
        "time":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title":    title,
        "doc":      ufile.name if ufile else "",
        "question": question.strip()[:100],
        "ops1": ops1, "fc1": fc1,
        "ops2": ops2, "fc2": fc2,
        "final": final_res,
    })
    st.success("✅ 회의 완료! 오른쪽에 최종 결론이 표시됩니다.")
    st.rerun()
