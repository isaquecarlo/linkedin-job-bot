import json
import time
import re
import winsound
import random
import math
import os       # <--- ESTA LINHA É OBRIGATÓRIA PARA CRIAR PASTAS
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
import google.generativeai as genai
import requests

# MANTENHA SUA CHAVE AQUI
GOOGLE_API_KEY = "AIzaSyDm1N4HTN9i3Br-H-Mg5TFzc2tVa7BnRus"
genai.configure(api_key=GOOGLE_API_KEY)


# --- CONFIGURAÇÕES ---
CV_PT = Path(__file__).parent / "CV_Isaque_Carlos_PORTUGUES.pdf"
CV_EN = Path(__file__).parent / "CV_Isaque_Carlos_ENGLISH.pdf"
CL_PT = Path(__file__).parent / "Cover_Letter_Isaque_Carlos_PT.pdf" # Carta PT
CL_EN = Path(__file__).parent / "Cover_Letter_Isaque_Carlos_EN.pdf" # Carta EN

# VALOR NUMÉRICO PURO (Para evitar erros)
SALARIO_NUMERO = "3300"
TOTAL_CANDIDATURAS_HOJE = 0

# --- SISTEMA DE LOGGING INTELIGENTE ---
LOG_FILE = "application_log.txt"
QA_LOG_FILE = "questions_answers_log.json"

def log_qa(question, answer, job_title="", is_numeric=False):
    """Registra pergunta e resposta em arquivo JSON para revisão diária"""
    try:
        # Carrega log existente
        if os.path.exists(QA_LOG_FILE):
            with open(QA_LOG_FILE, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
        else:
            qa_data = []
        
        # Adiciona novo registro
        qa_data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "job": job_title,
            "question": question,
            "answer": answer,
            "is_numeric": is_numeric
        })
        
        # Salva
        with open(QA_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        pass  # Não quebra o bot se log falhar

def log_info(message, show_terminal=True):
    """Log de informação (opcional no terminal)"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    
    # Sempre salva em arquivo
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + "\n")
    
    # Mostra no terminal apenas se solicitado
    if show_terminal:
        print(log_line)

def log_error(message, take_screenshot_func=None, page=None):
    """Log de erro (SEMPRE no terminal + alarme + screenshot)"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    error_line = f"[{timestamp}] ❌ ERRO: {message}"
    
    # Salva em arquivo
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(error_line + "\n")
    
    # SEMPRE mostra no terminal (destaque)
    print("\n" + "="*60)
    print(error_line)
    print("="*60 + "\n")
    
    # Alarme sonoro
    try:
        winsound.Beep(880, 300)  # Frequência alta
        winsound.Beep(440, 300)  # Frequência baixa
    except:
        pass
    
    # Screenshot se fornecido
    if take_screenshot_func and page:
        take_screenshot_func(page, "erro_critico")
        print("📸 Screenshot de erro salvo em erros_print/")

def generate_daily_summary():
    """Gera resumo diário das perguntas/respostas para revisão"""
    try:
        if not os.path.exists(QA_LOG_FILE):
            print("Nenhum log de Q&A encontrado.")
            return
        
        with open(QA_LOG_FILE, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        
        # Filtra apenas hoje
        today = datetime.now().strftime("%Y-%m-%d")
        today_qa = [q for q in qa_data if q['timestamp'].startswith(today)]
        
        if not today_qa:
            print(f"Nenhuma pergunta respondida hoje ({today}).")
            return
        
        # Gera relatório
        summary_file = f"daily_summary_{today}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"=== RESUMO DIÁRIO - {today} ===\n")
            f.write(f"Total de perguntas: {len(today_qa)}\n\n")
            
            for i, qa in enumerate(today_qa, 1):
                f.write(f"{i}. [{qa['timestamp']}] {qa.get('job', 'Vaga desconhecida')}\n")
                f.write(f"   PERGUNTA: {qa['question']}\n")
                f.write(f"   RESPOSTA: {qa['answer']}\n")
                f.write(f"   TIPO: {'Numérico' if qa.get('is_numeric') else 'Texto'}\n\n")
        
        print(f"✅ Resumo diário salvo em: {summary_file}")
        return summary_file
    except Exception as e:
        print(f"Erro ao gerar resumo: {e}")
        return None


# --- SUAS SKILLS REAIS (DO CURRÍCULO) ---
# Se a pergunta citar isso -> Resposta: 3. Se não -> Resposta: 1.
MY_SKILLS = [
    # Core & Linguagens
    "python", "pandas", "numpy", "sql", "vba", "excel",
    # Automação & Scraping
    "selenium", "playwright", "scrapy", "beautifulsoup", "automation", 
    "automação", "bot", "rpa", "scraping", "crawling", 
    # Cloud & AI
    "azure", "cloud", "machine learning", "ia ", "ai ", "artificial", 
    "nlp", "llm", "rag", "scikit-learn", "scipy", "cognitive",
    # Dados & BI
    "power bi", "dashboard", "analytics", "analista", "dados", "data",
    "matplotlib", "seaborn", "etl",
    # Dev
    "git", "github", "api", "backend", "web", "html", "css",
    "vs code", "pycharm", "jupyter"
]

# --- FILTROS ---
BLACKLIST_TITLES = [
    "Gerente","Comercial","Administrativo","Mercado","Social Media","Sales","Lead", "Senior","senior", "sênior", "advogado", "direito", "SR", "sr",
 "enfermeiro", "médico", "farmacêutico", "motorista", "recepcionista", "Sales", "Marketing",
]




def human_mouse_move(page, x, y):
    """Move o mouse em curvas suaves como uma mão humana"""
    try:
        start_x, start_y = page.mouse.position
        steps = 20
        for i in range(steps + 1):
            t = i / steps
            # Interpolação linear simples (pode ser melhorada, mas já ajuda)
            current_x = start_x + (x - start_x) * t
            current_y = start_y + (y - start_y) * t
            # Adiciona um leve desvio aleatório
            current_x += random.uniform(-2, 2)
            current_y += random.uniform(-2, 2)
            page.mouse.move(current_x, current_y)
            time.sleep(random.uniform(0.01, 0.03))
    except: pass

def human_click(page, locator):
    """Move o mouse até o elemento e clica"""
    try:
        box = locator.first.bounding_box()
        if box:
            # Mira no centro do botão com leve variação
            x = box["x"] + box["width"] / 2 + random.uniform(-10, 10)
            y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
            human_mouse_move(page, x, y)
            time.sleep(random.uniform(0.1, 0.3))
            page.mouse.click(x, y)
        else:
            locator.first.click()
    except:
        locator.first.click(force=True)


# WHITELIST_TITLES REMOVIDA:
# O robô agora aplica para TODAS as vagas que aparecem na busca,
# exceto as que estão na BLACKLIST acima.

# --- ALARME ---
def alert_user(motivo):
    print(f"\n🚨 ALERTA: {motivo}")
    try: winsound.Beep(2500, 300)
    except: pass

# --- FUNÇÃO AUXILIAR DE DIGITAÇÃO HUMANA ---
def human_type(element, text):
    """Digita com atraso aleatório (Jitter) para parecer humano"""
    element.click(); element.fill("")
    for char in text:
        element.type(char)
        time.sleep(random.uniform(0.05, 0.12)) # 50ms a 120ms por letra
    time.sleep(0.5)

def take_error_screenshot(page, error_type="erro"):
    """Tira screenshot automático de erros e salva na pasta erros_print"""
    try:
        timestamp = int(time.time())
        filename = f"erros_print/{error_type}_{timestamp}.png"
        page.screenshot(path=filename)
        log_error(f"Screenshot capturado: {filename}")
    except Exception as e:
        log_error(f"Falha ao tirar screenshot: {e}")

# --- INTELIGÊNCIA LÓGICA (V23 - CORRIGIDA) ---
# --- INTELIGÊNCIA LÓGICA (V25 - LOCALIZAÇÃO FIXA) ---
# --- SUBSTITUA A FUNÇÃO 'get_strategic_answer' INTEIRA POR ISTO: ---
# --- CONFIGURAÇÃO SUPREMA DA IA (V35 - TUDO NA IA) ---
# O usuário pediu para remover a lógica hardcoded e passar tudo como "Regras de Contexto" para o Gemini.

DEFAULT_RULES = """
SYSTEM INSTRUCTIONS: YOU ARE ISAQUE CARLOS (UNIVERSAL EXPERT CANDIDATE).
YOUR MISSION IS TO PASS AUTOMATED RECRUITMENT FILTERS.

=== CANDIDATE PHILOSOPHY ===
YOU HAVE EXPERIENCE WITH EVERYTHING. You are a polymath, a quick learner, and adaptable.
- MINIMUM EXPERIENCE: 2 years (NEVER less)
- LANGUAGES: Intermediate/Advanced (NEVER basic)
- ANY TECHNOLOGY: At least 2 years of hands-on experience
- GOAL: Appear as the PERFECT candidate for ANY job

⚠️ CRITICAL: This philosophy is INTERNAL ONLY. NEVER mention it in answers.
   - BAD: "I am a universal candidate with experience in everything"
   - BAD: "I have broad knowledge across multiple areas"
   - GOOD: "5" (direct number)
   - GOOD: "Yes" (direct answer)
   - GOOD: "Python" (direct technology name)

=== CRITICAL RULES (INFALLIBLE) ===

0. 📝 ANSWER FORMAT (SUPREME RULE)
   - ALWAYS give DIRECT, SPECIFIC answers.
   - NEVER use generic statements or philosophical descriptions.
   - Examples:
     * "How many years of Python?" → "5" (NOT "I have extensive experience")
     * "Do you know Java?" → "Yes" (NOT "I'm familiar with many languages")
     * "English level?" → "Advanced" or "8" (NOT "I speak multiple languages")

1. 🔢 NUMBERS VS TEXT (ABSOLUTE PRIORITY)
   - IF the question starts with "How many", "Quantos", "Years", "Anos", OR expects a numeric duration:
     - YOU MUST OUTPUT ONLY DIGITS. NO TEXT.
     - BAD: "Five years", "More than 5", "Yes", "Sim", "Nenhum", "Não uso".
     - GOOD: "5", "8", "3", "2".
   - MINIMUM EXPERIENCE: ALWAYS 2 or more (NEVER 0 or 1).
   - SCALES (1-5 or 1-10):
     - If numeric scale 1-5: Output "4" or "5" (Advanced/Native).
     - If numeric scale 1-10: Output "8" or "10" (Advanced/Native).
     - NEVER output "B2", "C1", or "Fluent" if the field requires a number.

2. 🔽 DROPDOWN/OPTIONS (MANDATORY)
   - IF 'Possible Options' are provided:
     - YOU MUST SELECT ONE OPTION FROM THE PROVIDED LIST.
     - DO NOT INVENT AN ANSWER.
     - If the options are ["Yes", "No"] -> Pick "Yes".
     - If options are valid/invalid -> Pick the one that allows proceeding (Positive).
     - MATCHING: Pick the option closest to "Yes", "Fluent", "Native", "Advanced", or "Full-time".

3. 🛂 AUTHORIZATION (AGGRESSIVE PASS)
   - "Are you authorized to work?": ALWAYS "Yes" (or "Sim").
   - "Do you need sponsorship?": ALWAYS "No" (or "Não").
   - IGNORE country specifics (e.g. "Authorized in US?"). Just answer YES to pass the filter.

4. 💰 SALARY & CURRENCY
   - IF Context is English -> ASSUME USD.
     - Annual: "00000" | Monthly: "1600" | Hourly: "40".
   - If context is Portuguese -> ASSUME BRL.
     - Mensal: "12000" | Hora: "80".
   - IF question is generic ("Salary Expectation"): Give the competitive number above (digits only).

5. 📍 LOCATION & REMOTE
   - "Where do you live?": "Florianópolis, Brazil".
   - "Willing to relocate?": "Yes".
   - "Willing to commute?": "Yes".
   - "Remote?": "Yes".
   - "Address": "Rua Principal, 100".

6. 🗣️ LANGUAGE PROFICIENCY
   - English: "Professional working proficiency" / "Fluent" (or "8" if numeric).
   - Portuguese: "Native or bilingual proficiency" / "Nativo" (or "10" if numeric).
   - Spanish: "Professional working proficiency" (or "6" if numeric).

7. 🎓 EDUCATION & LINKS
   - University: "Federal University of Santa Catarina" / "Universidade Federal de Santa Catarina".
   - LinkedIn: "https://www.linkedin.com/in/isaque-carlos"
   - Portfolio/GitHub: "https://github.com/isaque-carlos"

8. 🛠️ EXPERIENCE (YEARS)
   - Python: "5"
   - SQL: "4"
   - Azure/Cloud: "3"
   - Java: "2"
   - General Data Analysis: "5"

9. 🛡️ DEMOGRAPHICS (STANDARD)
   - Gender: "Man" / "Masculino".
   - Disability/Veteran: "No" / "Não".
   - Race: "Prefer not to say".

FAIL-SAFE MODE:
- If uncertain, choose the optimistic/"YES" answer.
- NEVER leave a field blank or return an error message.
- YOUR GOAL IS TO GET THE INTERVIEW.
"""

def get_strategic_answer(question_text, is_numeric_field=False, is_english=False, options=None):
    """Cérebro V40: Deixa a IA pensar, apenas fornece o contexto."""
    q = question_text.lower().strip()
    
    # --- 1. REGRAS DE SEGURANÇA IMEDIATA (Coisas que a IA pode demorar ou errar formato) ---
    # Endereço e CEP costumam ter formatos chatos, melhor garantir fixo.
    if any(x in q for x in ["street", "rua", "address", "endereço", "logradouro"]): return "Rua Principal, 100"
    if any(x in q for x in ["city", "cidade"]): return "Florianópolis"
    if any(x in q for x in ["zip", "postal", "cep", "code"]): return "88010-000"  # Removido len(q) < 20
    if any(x in q for x in ["state", "estado", "province"]): return "Santa Catarina"
    
    # --- 1.5. INTERCEPTADOR NUCLEAR PARA SALÁRIO (BYPASS TOTAL DA IA) ---
    # Solução definitiva para evitar "Sim" em perguntas de salário. 
    # BASE: R$ 3.350,00 (Mensal BRL)
    if any(x in q for x in ["pretensão", "salarial", "salary", "expectativa", "remuneração", "compensation", "expectations"]):
         # 1. Detecta Moeda (Se pergunta em inglês -> USD, senão BRL)
         is_usd = is_english or any(x in q for x in ["usd", "dollar", "annual"])
         
         # 2. Detecta Período (Anual, Hora ou Mensal)
         is_annual = any(x in q for x in ["annual", "year", "ano", "anual"])
         is_hourly = any(x in q for x in ["hour", "hora", "rate"])
         
         # 3. Base de Cálculo (Cotação aprox: 6.0)
         base_brl = 3350
         base_usd = 560 # (3350 / 6) arredondado
         
         if is_usd:
             if is_annual: return "6720"  # 560 * 12
             if is_hourly: return "4"     # 560 / 160 (aprox)
             return "560"                 # Mensal USD
         else:
             if is_annual: return "40200" # 3350 * 12
             if is_hourly: return "21"    # 3350 / 160
             return "3350"                # Mensal BRL
    
    # --- 1.6. INTERCEPTADOR NUMÉRICO INTELIGENTE (BYPASS TOTAL DA IA) ---
    # Se o campo é numérico, NUNCA deixa a IA responder em texto
    # FILOSOFIA: Candidato UNIVERSAL com experiência em TUDO (mínimo 2 anos)
    if is_numeric_field:
        # Tecnologias que o candidato DOMINA (anos de experiência)
        tech_experience = {
            "python": 5, "sql": 4, "azure": 3, "cloud": 3, "aws": 3,
            "data": 5, "analytics": 5, "excel": 8, "power bi": 4, "powerbi": 4,
            "tableau": 3, "git": 5, "linux": 4, "docker": 3, "kubernetes": 2,
            "spark": 3, "hadoop": 2, "etl": 4, "database": 5, "mysql": 4,
            "postgresql": 4, "mongodb": 3, "api": 4, "rest": 4, "json": 5,
            "agile": 4, "scrum": 4, "jira": 4, "confluence": 3,
            # Idiomas (escala numérica)
            "english": 8, "inglês": 8, "portuguese": 10, "português": 10,
            "spanish": 6, "espanhol": 6
        }
        
        # Tecnologias BÁSICAS (2 anos - candidato adaptável)
        basic_experience = [
            "powershell", "intune", "sccm", "endpoint", "active directory",
            ".net", "c#", "java", "ruby", "php", "swift", "kotlin", 
            "salesforce", "sap", "oracle", "mainframe", "cobol", "go", "rust"
        ]
        
        # Verifica se a pergunta menciona alguma tecnologia conhecida
        for tech, years in tech_experience.items():
            if tech in q:
                return str(max(years, 2))  # Garante mínimo 2
        
        # Verifica se menciona tecnologia básica (ESTRATÉGIA: 2 anos)
        for tech in basic_experience:
            if tech in q:
                return "2"  # Experiência básica (passa filtros)
        
        # Fallback: Se pergunta sobre "anos" ou "experiência" -> 3 anos (seguro)
        if any(x in q for x in ["anos", "years", "experiência", "experience"]):
            return "3"
        
        # Fallback final: 2 (NUNCA menos - candidato universal)
        return "2"
     
    # --- 2. PREPARAÇÃO PARA A IA ---
    # Avisa a IA se o campo é EXCLUSIVAMENTE numérico para ela fazer a conversão (Regra 1 do Prompt)
    context_note = ""
    if is_numeric_field:
        context_note = " [ATENÇÃO: O CAMPO É DO TIPO 'NUMBER'. RESPONDA APENAS DÍGITOS. CONVERTA TEXTO PARA NOTA SE NECESSÁRIO]"
    
    # --- 3. MANDA PRA IA RESOLVER ---
    # A IA vai ler o DEFAULT_RULES atualizado e aplicar a lógica de conversão/autorização sozinha.
    answer = ask_gemini(question_text + context_note, is_english, possible_options=options)
    
    # --- 4. REGISTRA PERGUNTA E RESPOSTA ---
    log_qa(question_text, answer, is_numeric=is_numeric_field)
    print(f"      ❓ {question_text[:50]}... → ✅ {answer}")
    
    return answer
    
# --- PERGUNTAR AO GEMINI (MASTER) ---
# --- PERGUNTAR AO CÉREBRO HÍBRIDO (OLLAMA + GEMINI) ---
def ask_gemini(pergunta, is_english=False, possible_options=None):
    """
    ARQUITETURA HÍBRIDA:
    1. OLLAMA (Local) tenta responder primeiro (Rápido e Estável).
    2. GEMINI (Cloud) atua como SUPERVISOR, validando a resposta do Ollama.
    3. Se Ollama falhar, Gemini assume tudo.
    """
    print(f"      🧠 Cérebro Híbrido acionado para: '{pergunta[:50]}...'")
    
    ollama_answer = None
    ollama_model = "llama3" # Modelo local
    
    # --- PASSO 1: TENTATIVA OLLAMA ---
    try:
        lang_instruction = "Answer in English." if is_english else "Responda em Português."
        # Contexto Rico para o Ollama
        system_content = f"CONTEXT: {RESUME_TEXT}\nRULES: {DEFAULT_RULES}\nINSTRUCTION: {lang_instruction}. Return ONLY the answer."
        if possible_options:
            system_content += f"\nOPTIONS: {possible_options}\nPick the best option from the list."

        print(f"      🦙 Chamando Ollama ({ollama_model})...")
        resp = requests.post("http://localhost:11434/api/generate", json={
            "model": ollama_model,
            "prompt": f"System: {system_content}\nUser: {pergunta}",
            "stream": False,
            "options": {"temperature": 0.1}
        }, timeout=8)
        
        if resp.status_code == 200:
            ollama_answer = resp.json().get("response", "").strip()
            print(f"      🦙 Ollama respondeu: '{ollama_answer}'")
        else:
            print(f"      ⚠️ Erro Ollama: {resp.status_code}")
            
    except Exception as e:
        print(f"      ⚠️ Ollama indisponível/timeout: {e}")

    # --- PASSO 2: SUPERVISÃO/FALLBACK GEMINI ---
    try:
        # Se Ollama respondeu, Gemini apenas AUDITA (Modo Supervisor)
        if ollama_answer:
            print("      👮‍♀️ Chamando Gemini para AUDITAR resposta do Ollama...")
            prompt = f"""
            CRITICAL: Your answer MUST be ULTRA SHORT (maximum 10 words).
            
            AUDIT TASK:
            Question: "{pergunta}"
            Context: {RESUME_TEXT}
            Rules: {DEFAULT_RULES}
            
            Ollama (Junior AI) Answered: "{ollama_answer}"
            
            YOUR TASK: Verify if Ollama's answer is CORRECT and OPTIMAL based on my Rules.
            - If YES: Return the SAME answer.
            - If NO: Return the CORRECTED answer.
            - RETURN ONLY THE FINAL ANSWER TEXT (MAX 10 WORDS).
            - NO explanations, NO "Based on...", NO conversational text.
            """
        else:
            # Se Ollama falhou, Gemini responde do zero (Modo Fallback)
            print("      🤖 Ollama falhou. Gemini assumindo controle total...")
            prompt = f"""
            CRITICAL INSTRUCTION: Your answer MUST be ULTRA SHORT (maximum 10 words).
            
            CONTEXT: {RESUME_TEXT}
            MY RULES: {DEFAULT_RULES}
            QUESTION: "{pergunta}"
            OPTIONS: {possible_options if possible_options else 'None'}
            
            FORBIDDEN RESPONSES:
            - "I'm excited to help!"
            - "Based on the provided context..."
            - "Please go ahead and ask..."
            - ANY explanatory text
            
            REQUIRED FORMAT:
            - For numbers: Just the digit (e.g., "5", "3350")
            - For Yes/No: Just "Yes" or "No"
            - For text: Maximum 3 words (e.g., "Florianópolis", "Python", "Advanced")
            - For URLs/profiles: Just the URL or "linkedin.com/in/isaque-carlos"
            
            ANSWER (MAX 10 WORDS):
            """

        # Hierarquia de Modelos Gemini
        models_to_try = ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash']
        final_answer = None
        used_model = ""

        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt, request_options={"timeout": 15})
                final_answer = response.text.strip().replace('"', '').replace("'", "").replace("\n", "")
                used_model = m_name
                break
            except: continue
        
        if final_answer:
            if possible_options: final_answer = final_answer.replace(".", "")
            print(f"      ✅ Resposta Final (Gemini {used_model}): '{final_answer}'")
            return final_answer
        elif ollama_answer:
            print(f"      ⚠️ Gemini falhou, usando resposta do Ollama (Sem auditoria).")
            return ollama_answer
        else:
            raise Exception("Todos as IAs falharam.")

    except Exception as e:
        print(f"      ❌ ERRO CRÍTICO IAs: {e}")
        # Fallback Nuclear
        if "salary" in pergunta.lower(): return "3350"
        return "3" # Valor numérico seguro para experiência (fallback)

        
        # 2. Se tiver opções, escolhe a melhor (não apenas a primeira)
        if possible_options:
            # Tenta escolher "Yes" ou "Sim" se disponível
            for opt in possible_options:
                if opt.lower() in ["yes", "sim", "sí"]:
                    print(f"      🔄 Fallback opção positiva: {opt}")
                    return opt
            # Se não, retorna a primeira
            print(f"      🔄 Fallback primeira opção: {possible_options[0]}")
            return possible_options[0]
        
        # 3. Padrão Sim/Não
        fallback = "Yes" if is_english else "Sim"
        print(f"      🔄 Fallback padrão: {fallback}")
        return fallback
# --- DADOS DO CURRÍCULO (PARA A IA) ---
RESUME_TEXT = """
CANDIDATE PROFILE:
Name: Isaque Carlos
Age: 23 years old (Started coding at 14)
Total Experience: 9+ years in Tech / 3+ years professional / 2 Years in Cloud/Azure
Location: São Paulo, Brazil (Open to relocation to Florianópolis/Remote)
Role: Data Analyst / Python Developer / AI Engineer
Education: FATEC / UNINOVE - Análise e Desenvolvimento de Sistemas

TECHNICAL SKILLS:
- Languages: Python (Strong), SQL, VBA.
- Cloud: Azure (2 years), AWS (Basic).
- Data: Pandas, NumPy, Matplotlib, Seaborn, Power BI, ETL.
- Automation/Web Scraping: Selenium, Playwright, Scrapy, BeautifulSoup.
- AI/ML: Scikit-learn, LLMs, RAG, Ollama, Azure AI.
- Tools: Git, GitHub, VS Code, Excel (Advanced).

LANGUAGES:
- Portuguese: Native
- English: Intermediate/Advanced (Capable of reading/writing/speaking).

KEY PROJECTS/ACHIEVEMENTS:
- Developed automated bots for job applications and data scraping.
- Experience with infinite scrolling data extraction.
- Construction of dashboards and data visualization pipelines.

SOFT SKILLS:
- Problem-solver, Analytical, Quick learner, Proactive.
"""
# --- CONFIGURAÇÃO DA INTELIGÊNCIA DA IA (V36 - SALÁRIO INTELIGENTE + VISA AGRESSIVO) ---
DEFAULT_RULES = """
CRITICAL INSTRUCTIONS FOR THE AI:

1. **AUTHORIZATION & VISA (AGGRESSIVE STRATEGY)**:
   - If asked "Are you legally authorized to work in [Country]?", ALWAYS answer "Yes".
   - If asked "Will you now or in the future require sponsorship?", answer "No" (Assume B2B/Contractor contract which handles this).
   - We want to PASS the filters. Do not self-reject.

2. **SALARY & CURRENCY (CONTEXT AWARE)**:
   - IF the Job Description is in ENGLISH: Assume the currency is USD or EUR.
     - Expected Salary: "3000" (Do NOT put 3300 BRL, that is too low for USD).
   - IF the Job Description is in PORTUGUESE: Assume BRL.
     - Expected Salary: "3500".
   - If the question asks for a generic number without currency specified, look at the language.

3. **EXPERIENCE (NUMERIC)**:
   - If asked "How many years...", answer "5" for Python/Data/AI roles.
   - For Cloud/Azure, answer "3".
   - NEVER answer "Yes" to a numeric question.

4. **LOCATION**:
   - If asked "Are you comfortable working remotely?", answer "Yes".
   - If asked "Where do you live?", answer "Florianópolis, Brazil".
"""


# SUBSTITUA DAS LINHAS 102 ATÉ 117 POR ISTO:
def handle_discard_popup(page):
    """Clica em Fechar (X) ou Descartar se o popup aparecer"""
    try:
        # 1. Tenta clicar no botão 'X' (Fechar) do modal de salvamento
        # Isso resolve o caso do print onde o botão Descartar as vezes falha
        close_btn = page.locator("button[aria-label='Fechar'], button[aria-label='Close']").first
        if close_btn.is_visible():
            close_btn.click(force=True)
            time.sleep(1)

        # 2. Se o X não funcionar, tenta os botões de texto "Descartar"
        selectors = [
            "button[data-control-name='discard_application_confirm_btn']",
            "button[data-test-dialog-secondary-action='']",
            ".artdeco-modal__actionbar button:has-text('Descartar')",
            ".artdeco-modal__actionbar button:has-text('Discard')",
            "button:has-text('Descartar')",
            "button:has-text('Discard')"
        ]
        
        for sel in selectors:
            btn = page.locator(sel).first
            if btn.is_visible():
                print("      🗑️ Popup detectado: Clicando em DESCARTAR.")
                btn.click(force=True)
                time.sleep(1.5)
                return True
    except: pass
    return False
           
   
def check_and_fix_errors(page, element, question_text, is_english):
    """Verifica erro e pede ajuda pra IA se der ruim"""
    try:
        parent = element.locator("xpath=..")
        if parent.locator(".artdeco-inline-feedback--error").count() > 0:
            msg = parent.locator(".artdeco-inline-feedback--error").inner_text().strip()
            print(f"         🚨 ERRO VALIDACAO: '{msg}' -> Pedindo ajuda pra IA...")
            
            # Pede nova resposta para a IA considerando o erro
            alternatives = ask_gemini(f"{question_text} (Error: {msg})", is_english)
            
            element.click(force=True); element.fill("")
            human_type(element, alternatives)
            page.keyboard.press("Tab")
            time.sleep(1.0)
            
            # Se ainda der erro, tenta o '2' (Fallback final)
            if parent.locator(".artdeco-inline-feedback--error").count() > 0:
                 element.fill("2"); page.keyboard.press("Tab")

            return True
    except: pass
    return False

def human_type(element, text):
    """Digita com atraso aleatório para simular humano"""
    try:
        element.click(force=True); element.fill("")
        for char in text:
            element.type(char)
            time.sleep(random.uniform(0.05, 0.12)) # 50ms a 120ms por letra
        time.sleep(0.5)
    except: 
        element.fill(text)

def close_security_modal(page, context="geral"):
    """Detecta e fecha o modal de segurança do LinkedIn se estiver visível"""
    try:
        security_modal_btn = page.locator("button").filter(has_text=re.compile(r"Continuar candidatura|Continue application", re.I)).first
        if security_modal_btn.is_visible(timeout=1000):
            print(f"      🔒 Modal de segurança detectado ({context}). Clicando em 'Continuar candidatura'...")
            security_modal_btn.click(force=True)
            time.sleep(1.5)
            print(f"      ✅ Modal de segurança fechado!")
            return True
    except:
        pass
    return False

def audit_and_fix_page(page, is_english):
    """
    DUPLA VERIFICAÇÃO (DOUBLE CHECK):
    Lê a tela inteira, manda pro Gemini validar se as respostas estão coerentes,
    e corrige se necessário.
    """
    print("      🕵️ INICIANDO DUPLA VERIFICAÇÃO (AUDITORIA IA)...")
    
    # 1. Coleta Perguntas e Respostas da Tela
    blocks = page.locator(".jobs-easy-apply-form-section__element").all()
    page_data = [] # Lista de {label, value, block}
    
    for block in blocks:
        try:
            if not block.is_visible(): continue
            lbl = ""
            try: lbl = block.locator("label").first.inner_text().strip()
            except: 
                try: lbl = block.locator("legend").first.inner_text().strip()
                except: continue
            
            val = ""
            inp = block.locator("input, select, textarea").first
            if inp.count() > 0 and inp.is_visible():
                val = inp.input_value()
            else:
                sel = block.locator("[aria-checked='true'], [aria-selected='true']").first
                if sel.count() > 0: val = sel.inner_text().strip()
                else:
                    combo = block.locator("[role='combobox']").first
                    if combo.count() > 0: val = combo.inner_text().strip()
            
            if lbl and val:
                page_data.append({"label": lbl, "value": val, "block": block})
        except: pass

    if not page_data:
        print("      🕵️ Nada para auditar nesta página.")
        return

    # 1.5. INTERCEPTADOR DE SALÁRIO (CORREÇÃO LOCAL)
    # Antes de mandar pra IA, corrige erros óbvios de salário (Ex: "Sim" em vez de "12000")
    for item in page_data:
        lbl_lower = item['label'].lower()
        if any(x in lbl_lower for x in ["pretensão", "salarial", "salary", "expectativa", "remuneração", "compensation"]):
            # Se não for número (ex: "Sim", "Yes"), força correção
            import re
            if not re.match(r"^\d+$", item['value'].strip()):
                print(f"         🔨 CORREÇÃO FORÇADA DE SALÁRIO: '{item['label'][:20]}...' -> '12000'")
                item['value'] = "12000"
                
                # Aplica correção visual imediatamente
                try:
                    block = item["block"]
                    inp = block.locator("input, textarea").first
                    if inp.count() > 0: inp.click(); inp.fill("12000")
                except: pass

    # 2. Monta Prompt Auditoria
    audit_prompt = "AUDIT THIS FORM DATA. Check consistency with Rules. Return JSON list of corrections.\n"
    audit_prompt += "FORMAT: [ { 'label_index': 0, 'correction': 'New Value' } ]\n"
    audit_prompt += "RULES:\n" + DEFAULT_RULES + "\n\nFORM DATA:\n"
    for i, item in enumerate(page_data):
        audit_prompt += f"INDEX {i}: Q='{item['label']}' | A='{item['value']}'\n"

    # 3. Manda pro Gemini
    try:
        # Usa o modelo existente ou cria um leve
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(audit_prompt)
        text_resp = response.text.strip()
        
        # Limpa JSON
        if "```" in text_resp:
            text_resp = text_resp.replace("```json", "").replace("```", "").strip()
            
        corrections = json.loads(text_resp)
        
        if corrections:
            print(f"      🕵️ GEMINI ENCONTROU {len(corrections)} CORREÇÕES! APLICANDO...")
            for corr in corrections:
                try:
                    idx = corr.get("label_index")
                    new_val = corr.get("correction")
                    
                    if idx is not None and 0 <= idx < len(page_data):
                        item = page_data[idx]
                        block = item["block"]
                        print(f"         🔨 Corrigindo: '{item['label'][:20]}...' -> '{new_val}'")
                        
                        # Tenta preencher
                        inp = block.locator("input, textarea").first
                        if inp.count() > 0 and inp.is_visible():
                             inp.click(); inp.fill(""); inp.type(str(new_val))
                        else:
                             # Se for select/dropdown, tenta corrigir chamando a função
                             # Mas precisa ser cuidadoso pra não loopar.
                             # Tenta clicar no elemento e digitar a resposta correta
                             el = block.locator("select, [role='combobox']").first
                             if el.is_visible():
                                 if "select" in str(el.evaluate("el => el.tagName")).lower():
                                     try: el.select_option(label=new_val)
                                     except: el.select_option(value=new_val)
                                 else:
                                     el.click(force=True); el.type(new_val[:4]); page.keyboard.press("Enter")
                except: pass
        else:
            print("      ✅ Gemini 2.0 aprovou todas as respostas.")
            
    except Exception as e:
        print(f"      ⚠️ Erro na auditoria IA: {e}")

def interact_with_dropdown(page, element, question_text, is_english=False):
    """Lida com menus: Lê opções reais, IA escolhe da lista, Seleciona."""
    try:
        print(f"         🔽 Processando Dropdown: '{question_text}'...")
        
        # 1. Tenta identificar o tipo de elemento e pegar as opções
        options = []
        tag_name = element.evaluate("el => el.tagName").lower()
        
        # A) Se for um <SELECT> nativo (HTML padrão)
        if tag_name == "select":
            # Extrai o texto de todas as <option>
            options = element.evaluate("el => Array.from(el.options).map(o => o.text)")
        
        # B) Se for um Dropdown Visual (Div/Button)
        else:
            element.scroll_into_view_if_needed()
            element.click(force=True)
            time.sleep(1.5) # Espera menu abrir
            # Pega itens de menu (tenta vários seletores comuns do LinkedIn)
            opts = page.locator("div[role='option'], li[role='option'], .artdeco-dropdown__item span").all()
            for o in opts:
                if o.is_visible():
                    txt = o.inner_text().strip()
                    if txt and txt not in options: options.append(txt)
        
        # Limpa lista (remove 'Select an option', vazios, etc)
        clean_options = [o for o in options if len(o) > 1 and "select" not in o.lower() and "selecione" not in o.lower()]
        
        if not clean_options:
            print("         ⚠️ Nenhuma opção detectada. Usando Fallback Sim/Não.")
            clean_options = ["Yes", "No"] if is_english else ["Sim", "Não"]
        
        print(f"         🔎 Opções enviadas para IA: {clean_options}")

        # 2. IA DECIDE (Passando as opções EXATAS)
        # Isso garante que a IA não invente uma resposta que não existe no menu
        answer = ask_gemini(question_text, is_english, possible_options=clean_options)
        print(f"         💡 IA Escolheu: '{answer}'")

        # 3. APLICA A SELEÇÃO
        if tag_name == "select":
            # Tenta selecionar pelo texto exato
            try:
                element.select_option(label=answer)
            except:
                # Se falhar, tenta pelo texto parcial ou index
                try: element.select_option(value=answer)
                except: 
                    # Último recurso: Seleciona o segundo item (o primeiro costuma ser placeholder)
                    print("         ⚠️ Falha ao selecionar texto exato. Selecionando índice 1...")
                    try: element.select_option(index=1)
                    except: pass
        else:
            # Dropdown Visual: Clica na opção que contém o texto
            clicked = False
            for opt_selector in ["div[role='option']", "li[role='option']", ".artdeco-dropdown__item"]:
                for el_opt in page.locator(opt_selector).all():
                    if not el_opt.is_visible(): continue
                    if answer.lower() in el_opt.inner_text().lower():
                        el_opt.click(force=True)
                        clicked = True
                        break
                if clicked: break
            
            # Se não clicou, tenta digitar
            if not clicked:
                element.click(force=True)
                element.type(answer[:4])
                time.sleep(0.5)
                page.keyboard.press("Enter")

        time.sleep(0.5)

    except Exception as e:
        print(f"         ❌ Erro crítico no dropdown: {e}")
        # Plano de Emergência: Seta para baixo + Enter para não travar
        try:
            element.click(force=True)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
        except: pass

def fill_form_turbo(page, candidate, is_english):
    """Preenche o formulário ativo (Inteligente + Força Bruta V35)"""
    print(f"      🚀 FILL_FORM_TURBO V35 INICIADO! is_english={is_english} 🚀")
    
    modal = page.locator(".jobs-easy-apply-modal")
    if modal.count() == 0: 
        print(f"      ❌ Modal não encontrado! Abortando.")
        return

    print(f"      📋 Iniciando varredura estruturada...")

    # --- ESTRATÉGIA 1: BLOCOS ESTRUTURADOS (Melhor contexto de Pergunta) ---
    # Tenta pegar os blocos que agrupa a Pergunta (Label) + Resposta (Input)
    question_blocks = modal.locator(".jobs-easy-apply-form-section__element").all()
    print(f"      🔍 Encontrados {len(question_blocks)} blocos de pergunta.")
    
    # Fallback: Se não achar blocos, pega os inputs soltos
    use_fallback = False
    if len(question_blocks) == 0:
        use_fallback = True
        print("      ⚠️ Nenhum bloco estruturado. Usando fallback (inputs diretos)...")
        question_blocks = modal.locator("input, select, textarea, div[role='combobox'], fieldset").all()

    for idx, block in enumerate(question_blocks):
        try:
            if not block.is_visible(): continue
            
            # --- A. IDENTIFICAÇÃO DO ELEMENTO ---
            el = None
            if use_fallback:
                el = block
            else:
                # Busca o input dentro do bloco
                el = block.locator("select, input, textarea, div[role='combobox'], button[role='combobox']").first
                # Se não achou input padrão, tenta achar por texto (ex: dropdown customizado)
                if not el.is_visible():
                     fallback_el = block.locator("text=Select an option").first
                     if fallback_el.is_visible(): el = fallback_el
            
            if not el or not el.is_visible(): continue

            # --- B. EXTRAÇÃO DE METADADOS ---
            tag = str(el.evaluate("el => el.tagName")).lower()
            role = str(el.get_attribute("role") or "").lower()
            type_attr = str(el.get_attribute("type") or "").lower()
            
            # Pula Uploads (já feitos antes) e Hidden
            if type_attr in ["file", "hidden"]: continue

            # --- C. DESCOBERTA DA PERGUNTA (LABEL) ---
            lbl = ""
            if use_fallback:
                try: lbl = el.locator("xpath=preceding::label[1]").first.inner_text()
                except: lbl = el.get_attribute("aria-label") or "Pergunta desconhecida"
            else:
                # Tenta achar label dentro do bloco
                try: lbl = block.locator("label, h3, h4, .fb-dash-form-element__label").first.inner_text()
                except: pass
                # Se falhar, pega o texto puro do bloco
                if not lbl: lbl = block.inner_text().split("\n")[0]
            
            lbl = lbl.replace("\n", " ").strip()
            print(f"      🔍 Bloco {idx+1}: '{lbl[:40]}...' (Tag: {tag})")

# Verifica se já está preenchido
            val = ""
            if tag in ["input", "textarea", "select"]: val = el.input_value()
            else: val = el.inner_text() # Para div/combobox
            
            # --- VALIDAÇÃO RIGOROSA (CORREÇÃO DE LOOP) ---
            has_error = False
            if not use_fallback:
                has_error = block.locator(".artdeco-inline-feedback--error").count() > 0
            
            # Lista de palavras que indicam que o campo ESTÁ VAZIO (Placeholder)
            empty_indicators = ["select", "selecione", "selecionar", "choose", "escolha", "opção", "option"]
            val_lower = val.lower() if val else ""
            
            # Verifica se o valor atual é apenas um placeholder (ex: "Selecionar opção")
            is_placeholder = any(bad in val_lower for bad in empty_indicators)
            
            # LÓGICA DE DECISÃO:
            # 1. Se tem erro vermelho -> NÃO PULA (precisa corrigir)
            # 2. Se é placeholder ("Selecionar...") -> NÃO PULA (está vazio)
            # 3. Se está vazio -> NÃO PULA
            # 4. Se tem valor real e sem erro -> PULA (já está pronto)
            
            if val and len(val) > 1 and not is_placeholder and not has_error:
                 print(f"         ✅ Já preenchido ('{val[:15]}...'), pulando.")
                 continue
            elif is_placeholder:
                 print(f"         ⚠️ Detectado falso preenchimento ('{val[:15]}...'). Forçando correção.")
            # --- E. AÇÃO DE PREENCHIMENTO ---
            
            # 1. É Dropdown? (Select ou Combobox)
            # MELHORADO: Detecta múltiplos tipos de dropdown
            aria_haspopup = str(el.get_attribute("aria-haspopup") or "").lower()
            is_dropdown = (
                tag == "select" or 
                "combobox" in role or 
                "listbox" in aria_haspopup or
                "select" in val.lower() or 
                "selecionar" in val.lower() or
                "selecione" in val.lower()
            )
            
            if is_dropdown:
                print(f"         🔽 Dropdown detectado! Chamando interact_with_dropdown...")
                interact_with_dropdown(page, el, lbl, is_english)
            
            # 2. É Checkbox/Radio Solto?
            elif type_attr in ["radio", "checkbox"] and tag == "input":
                # Geralmente confirmações (Ex: "I agree")
                ans = get_strategic_answer(lbl, False, is_english)
                if "yes" in ans.lower() or "sim" in ans.lower():
                    if not el.is_checked(): el.click(force=True)
            
            # 3. É Input Texto/Numérico
            else:
                is_numeric = (type_attr == "number")
                answer = get_strategic_answer(lbl, is_numeric, is_english)
                
                print(f"         📝 Preenchendo campo: '{lbl[:30]}...' com '{answer}'")
                
                # Tratamento especial para Cidades (Autocomplete)
                # Detecta: "city", "location", "cidade", "localização" OU resposta contém "Florianópolis"
                if "Florianópolis" in str(answer) or any(x in lbl.lower() for x in ["city", "location", "cidade", "localização"]):
                     try:
                        el.click(force=True); el.fill("")
                        el.type("Florianópolis, Santa Catarina", delay=50)
                        time.sleep(2.0) 
                        page.keyboard.press("ArrowDown"); page.keyboard.press("Enter")
                        print(f"            ✅ Cidade preenchida")
                     except Exception as e:
                         print(f"            ❌ Erro ao preencher cidade: {e}")
                else:
                    try:
                        # Garante que o campo está focado e limpo
                        el.click(force=True)
                        el.fill("")  # Limpa primeiro
                        time.sleep(0.2)
                        human_type(el, str(answer))
                        page.keyboard.press("Tab")
                        print(f"            ✅ Campo preenchido com sucesso")
                    except Exception as e:
                        print(f"            ❌ Erro ao preencher campo: {e}")
                        # Tenta método alternativo (fill direto)
                        try:
                            el.fill(str(answer))
                            print(f"            ✅ Preenchido com fill() alternativo")
                        except:
                            pass

        except Exception as e:
            print(f"      ⚠️ Erro no Bloco {idx}: {e}")

    # --- ESTRATÉGIA 2: FIELDSETS (RADIOS AGRUPADOS) ---
    # O LinkedIn costuma usar <fieldset> para perguntas Sim/Não
    fieldsets = modal.locator("fieldset").all()
    if len(fieldsets) > 0:
        print(f"      🔘 Verificando {len(fieldsets)} fieldsets...")
        
        try:
            for fs in fieldsets:
                if not fs.is_visible(): continue
                if fs.locator("input:checked").count() > 0: continue # Já marcado
                
                # Pega a pergunta (Legend)
                legend = fs.evaluate("el => el.innerText").split("\n")[0].lower()
                print(f"         🔘 Processando: '{legend[:40]}...'")
                
                # Coleta as opções disponíveis (Labels)
                options = [l.inner_text().strip() for l in fs.locator("label").all() if l.is_visible()]
                
                # Pede decisão para a IA com as opções reais
                decision = get_strategic_answer(legend, False, is_english, options=options)
                
                # Clica na opção correspondente
                clicked = False
                for l in fs.locator("label").all():
                    if decision.lower() in l.inner_text().lower(): 
                        l.click(force=True)
                        clicked = True
                        print(f"            ✅ Clicado: '{l.inner_text().strip()}'")
                        break
                
                # Fallback: Se não achou texto exato, clica no primeiro (geralmente Sim/Yes)
                if not clicked: 
                    fs.locator("label").first.click(force=True)
        except: pass
    
    # --- ESTRATÉGIA 3: FORÇA BRUTA (SEU CÓDIGO ORIGINAL MELHORADO) ---
    # Garante que nada ficou para trás (Inputs vazios, Dropdowns com erro)
    print(f"      🔨 FORÇA BRUTA: Varrendo campos restantes...")
    try:
        # A. Inputs de Texto Vazios
        inputs = modal.locator("input[type='text'], input:not([type]), textarea, input[type='email'], input[type='tel'], input[type='number']").all()
        print(f"         🔨 Encontrados {len(inputs)} inputs de texto para verificar...")
        
        filled_count = 0
        for inp in inputs:
            try:
                if not inp.is_visible(): continue
                val = inp.input_value()
                if not val or len(val) < 1:
                    # Tenta achar label
                    lbl = ""
                    try: 
                        lbl = inp.locator("xpath=preceding::label[1]").inner_text()
                    except: 
                        try:
                            lbl = inp.get_attribute("aria-label") or ""
                        except:
                            pass
                    
                    if not lbl:
                        lbl = inp.get_attribute("placeholder") or "Campo sem label"
                    
                    print(f"         🔨 Input vazio detectado: '{lbl[:40]}...'")
                    ans = get_strategic_answer(lbl, False, is_english)
                    print(f"            💡 Resposta gerada: '{ans}'")
                    
                    # TENTA PREENCHER COM MÚLTIPLOS MÉTODOS
                    try:
                        inp.click(force=True)
                        inp.fill("")  # Limpa primeiro
                        time.sleep(0.1)
                        human_type(inp, str(ans))
                        time.sleep(0.2)
                        
                        # Verifica se preencheu
                        new_val = inp.input_value()
                        if new_val and len(new_val) > 0:
                            print(f"            ✅ Campo preenchido com sucesso!")
                            filled_count += 1
                        else:
                            # Tenta fill() direto
                            inp.fill(str(ans))
                            print(f"            ✅ Preenchido com fill() alternativo")
                            filled_count += 1
                    except Exception as e:
                        print(f"            ❌ Erro ao preencher: {e}")
                        # Última tentativa: fill() direto
                        try:
                            inp.fill(str(ans))
                            filled_count += 1
                        except:
                            pass
            except Exception as e:
                print(f"         ⚠️ Erro ao processar input: {e}")
        
        print(f"         ✅ Força bruta preencheu {filled_count} campos vazios")
        
        # B. Dropdowns Vazios (Selects nativos)
        selects = modal.locator("select").all()
        for sel in selects:
            if sel.is_visible() and (not sel.input_value() or "select" in sel.input_value().lower()):
                try: lbl = sel.locator("xpath=preceding::label[1]").inner_text()
                except: lbl = "Dropdown sem label"
                print(f"         🔨 Select vazio: '{lbl[:30]}...'")
                interact_with_dropdown(page, sel, lbl, is_english)

        # C. Dropdowns Vazios (Visuais com erro ou "Select an option")
        # Procura divs que contenham "Select an option" ou tenham erro
        error_indicators = modal.locator(".artdeco-inline-feedback--error").all()
        visual_dropdowns = modal.locator("text=/Select an option|Selecione uma opção/i").all()
        
        # Junta tudo para verificar
        targets = error_indicators + visual_dropdowns
        
        if targets:
            print(f"         🔨 Verificando {len(targets)} dropdowns visuais/erros...")
            for item in targets:
                if item.is_visible():
                    # Tenta achar o pai clicável (o input do dropdown)
                    # Sobe na árvore até achar um elemento interativo
                    parent = item.locator("xpath=ancestor::div[role='combobox'] | ancestor::button[aria-haspopup='listbox']").first
                    
                    if parent.is_visible():
                        try:
                            # Pega label do bloco pai
                            lbl = parent.locator("xpath=ancestor::div[contains(@class, 'form-element')]//label").first.inner_text()
                        except: lbl = "Dropdown com erro/vazio"
                        
                        interact_with_dropdown(page, parent, lbl, is_english)
        
        # D. VARREDURA ADICIONAL: Dropdowns Visuais Diretos (FORÇA TOTAL)
        print(f"         🔨 Varredura adicional: Dropdowns visuais diretos...")
        direct_dropdowns = modal.locator("div[role='combobox'], button[role='combobox'], div[aria-haspopup='listbox'], button[aria-haspopup='listbox']").all()
        dropdown_filled = 0
        
        for dd in direct_dropdowns:
            try:
                if not dd.is_visible(): continue
                txt = dd.inner_text().strip().lower()
                if "select" in txt or "selecionar" in txt or "selecione" in txt or "opção" in txt or len(txt) < 5:
                    lbl = ""
                    try: lbl = dd.locator("xpath=ancestor::div[contains(@class, 'form-element')]//label").first.inner_text()
                    except:
                        try: lbl = dd.locator("xpath=preceding::label[1]").inner_text()
                        except:
                            try: lbl = dd.get_attribute("aria-label") or ""
                            except: pass
                    if not lbl or len(lbl) < 2: lbl = "Dropdown visual"
                    print(f"         🔨 Dropdown visual vazio: '{lbl[:40]}...'")
                    interact_with_dropdown(page, dd, lbl, is_english)
                    dropdown_filled += 1
                    time.sleep(0.5)
            except Exception as e:
                print(f"         ⚠️ Erro dropdown visual: {e}")
        print(f"         ✅ Varredura adicional preencheu {dropdown_filled} dropdowns")
        
        # E. VERIFICAÇÃO FINAL: Busca por QUALQUER "Selecionar opção" restante
        print(f"         🔨 VERIFICAÇÃO FINAL: Buscando 'Selecionar opção' restantes...")
        final_check = modal.locator("text=/Selecionar opção|Select an option/i").all()
        print(f"         🔍 Encontrados {len(final_check)} elementos com 'Selecionar opção'")
        
        final_filled = 0
        for idx, elem in enumerate(final_check):
            try:
                if not elem.is_visible(): continue
                print(f"         🚨 FINAL {idx+1}: Elemento vazio encontrado! Forçando preenchimento...")
                
                # Tenta achar o dropdown pai clicável
                parent = elem.locator("xpath=ancestor::div[role='combobox'] | ancestor::button[role='combobox'] | ancestor::select").first
                if parent.is_visible():
                    lbl = ""
                    try: lbl = parent.locator("xpath=ancestor::div[contains(@class, 'form-element')]//label").first.inner_text()
                    except:
                        try: lbl = parent.locator("xpath=preceding::label[1]").inner_text()
                        except: lbl = "Dropdown final"
                    
                    print(f"         📝 FINAL {idx+1}: Label = '{lbl[:40]}...', tentando preencher...")
                    interact_with_dropdown(page, parent, lbl, is_english)
                    final_filled += 1
                    time.sleep(0.5)
            except Exception as e:
                print(f"         ❌ Erro verificação final {idx+1}: {e}")
        print(f"         ✅ Verificação final preencheu {final_filled} dropdowns restantes")

    except Exception as e:
        print(f"      ❌ Erro na Força Bruta: {e}")
def detect_language_from_page(page):
    """
    Rola a descrição, expande o texto e detecta se é Inglês ou Português.
    """
    print("      👀 Analisando idioma da descrição...")
    try:
        # 1. Foca na área de detalhes da vaga
        details_pane = page.locator(".jobs-search__job-details--container, .jobs-description__content").first
        if details_pane.is_visible():
            details_pane.hover()
            
            # 2. Tenta clicar no botão "Exibir mais" / "See more" para carregar todo o texto
            try:
                see_more = page.locator("button.jobs-description__footer-button, button[aria-label*='exibir mais'], button[aria-label*='See more']").first
                if see_more.is_visible():
                    see_more.click()
                    time.sleep(0.5)
            except: pass

            # 3. Rola um pouco para baixo para garantir que o texto renderizou (Lazy Load)
            page.mouse.wheel(0, 500)
            time.sleep(0.8)

        # 4. Captura o texto completo focado na DESCRIÇÃO REAL
        full_text = ""
        
        # Tentativa 1: Busca pelo cabeçalho "Sobre a vaga" / "About the job" e pega o próximo irmão
        try:
            # Encontra o H2/H3 que tem o título
            header = page.locator("h2, h3").filter(has_text=re.compile(r"Sobre a vaga|About the job|Descrição|Description", re.I)).first
            if header.is_visible():
                # Tenta pegar o container pai ou o próximo elemento
                # Geralmente o texto está num div logo após o header ou no pai do header
                description_container = header.locator("xpath=..")
                full_text += description_container.inner_text().lower()
                print("      🎯 Encontrou cabeçalho 'Sobre a vaga'. Lendo conteúdo...")
        except: pass

        # Tentativa 2: Seletores clássicos se o acima falhar
        if len(full_text) < 50:
            possible_selectors = [
                "#job-details", 
                ".jobs-description__content", 
                ".jobs-box__html-content"
            ]
            for sel in possible_selectors:
                if page.locator(sel).count() > 0:
                    full_text += page.locator(sel).first.inner_text().lower() + " "
        
        # Remove o próprio título do texto para não enviesar (ex: remover "Sobre a vaga" da contagem)
        clean_text = full_text.replace("Sobre a vaga", "").replace("About the job", "").replace("Descrição", "").replace("Description", "")
        
        print(f"      📝 Texto capturado (Primeiros 150 chars): {clean_text[:150]}...")

        # 5. Regra Geográfica (SOMENTE SE TIVER CERTEZA ABSOLUTA)
        # Atenção: Muitas vagas do Brasil tem "South America" ou "Americas" no texto, cuidado.
        if "united states" in clean_text or "usa " in clean_text or "europe" in clean_text:
             print("      🌍 Idioma: INGLÊS (Detectado por Localização Específica)")
             return True

        # 6. Contagem de Palavras (Stop Words) - USANDO CLEAN_TEXT
        # Inglês
        score_en = sum(1 for w in clean_text.split() if w in ["the", "and", "to", "of", "in", "requirements", "skills", "we", "you", "with", "for", "are", "is"])
        # Português
        score_pt = sum(1 for w in clean_text.split() if w in ["o", "a", "de", "e", "do", "requisitos", "habilidades", "que", "para", "com", "são", "está"])
        # Espanhol (Novo)
        score_es = sum(1 for w in clean_text.split() if w in ["el", "la", "de", "y", "en", "requisitos", "habilidades", "que", "para", "con", "es", "trabajo", "empresa", "experiencia"])
        
        print(f"      🔤 Scores: EN:{score_en} | PT:{score_pt} | ES:{score_es}")
        
        if score_en > score_pt and score_en > score_es: return "en"
        elif score_es > score_pt and score_es > score_en: return "es"
        else: return "pt"

    except Exception as e: 
        print(f"      ⚠️ Falha ao ler descrição ({e}). Assumindo Português.")
        return False

def process_easy_apply(page, candidate, is_english=False):
    global TOTAL_CANDIDATURAS_HOJE
    print(f"   🤖 PREENCHENDO CANDIDATURA... ({'EN' if is_english else 'PT'})")
    
    try: page.wait_for_selector(".jobs-easy-apply-modal", timeout=3000)
    except: return False

    # Detecta e fecha modal de segurança do LinkedIn (MÚLTIPLAS TENTATIVAS)
    for attempt in range(3):
        if close_security_modal(page, f"início-tentativa-{attempt+1}"):
            break  # Modal fechado com sucesso
        if attempt < 2:
            time.sleep(1.0)  # Espera antes de tentar novamente

    # Define arquivos corretos
    target_cv = CV_EN if is_english else CV_PT
    target_cl = CL_EN if is_english else CL_PT

    stuck_counter = 0 
    start_time_apply = time.time()
    
    # Reduzido de 25 para 18 para evitar loops infinitos
    for step in range(18):
        # HARD TIMEOUT: Se passar de 180 segundos na mesma vaga, aborta.
        if time.time() - start_time_apply > 180:
             print("      🚨 TIME OUT (180s). Abortando...")
             try: winsound.Beep(440, 500); winsound.Beep(440, 500)
             except: pass
             try: page.screenshot(path=f"erros_print/erro_timeout_hard_{int(time.time())}.png")
             except: pass
             page.keyboard.press("Escape"); time.sleep(0.5); handle_discard_popup(page)
             return False
        
        # STUCK COUNTER: Se tentou 3 vezes e não conseguiu, aborta
        if stuck_counter >= 3:
            print(f"      🚨 STUCK COUNTER >= 3. Abortando vaga (não conseguiu preencher)...")
            try: winsound.Beep(440, 500); winsound.Beep(440, 500)
            except: pass
            try: page.screenshot(path=f"erros_print/erro_stuck_{int(time.time())}.png")
            except: pass
            page.keyboard.press("Escape"); time.sleep(0.5); handle_discard_popup(page)
            return False

        try:
            modal = page.locator(".jobs-easy-apply-modal")
            
            # VERIFICAÇÃO CRÍTICA: Se modal não existe, para o loop
            if modal.count() == 0:
                print(f"      ℹ️ Modal fechado. Candidatura provavelmente enviada. Saindo do loop...")
                return True  # Assume sucesso se modal fechou
            
            # VERIFICAÇÃO: Modal de segurança pode aparecer a qualquer momento
            close_security_modal(page, "loop")
            
            # 1. VERIFICA SUCESSO (MÚLTIPLAS FORMAS)
            # A. Verifica se tem mensagem de sucesso no modal
            success_texts = ["candidatura enviada", "application sent", "foi enviada", "has been sent", "successfully submitted"]
            modal_text = modal.inner_text().lower() if modal.count() > 0 else ""
            
            if any(txt in modal_text for txt in success_texts):
                print("      🏁 SUCESSO! Candidatura enviada detectada.")
                # Clica em qualquer botão para fechar (Concluir, Done, etc)
                close_btn = modal.locator("button").filter(has_text=re.compile(r"Concluir|Concluído|Done|Fechar|Dismiss|Close", re.I)).first
                if close_btn.is_visible():
                    close_btn.click(force=True)
                try: modal.wait_for_selector(".jobs-easy-apply-modal", state="hidden", timeout=3000)
                except: pass
                TOTAL_CANDIDATURAS_HOJE += 1
                return True
            
            # B. Verifica botão "Concluído" tradicional
            done_btn = modal.locator("button").filter(has_text=re.compile(r"Concluído|Done|Fechar|Dismiss", re.I)).first
            if done_btn.is_visible():
                 print("      🏁 SUCESSO! Clicando em Concluído...")
                 done_btn.click(force=True)
                 try: modal.wait_for_selector(".jobs-easy-apply-modal", state="hidden", timeout=3000)
                 except: pass
                 TOTAL_CANDIDATURAS_HOJE += 1
                 return True

            print(f"      🔍 DEBUG: Passou verificação de sucesso. stuck_counter={stuck_counter}")

            if stuck_counter >= 3:
                print("      🚨 Travou. Abortando.")
                try: winsound.Beep(440, 500); winsound.Beep(440, 500)
                except: pass
                try: page.screenshot(path=f"erros_print/erro_travou_{int(time.time())}.png")
                except: pass
                page.keyboard.press("Escape"); time.sleep(0.5); handle_discard_popup(page)
                return False

            print(f"      🔍 DEBUG: Passou verificação de stuck_counter. Iniciando upload de arquivos...")

            try:
                file_inputs = modal.locator("input[type='file']").all()
                for finput in file_inputs:
                    # REMOVIDO CHECK VISIBILIDADE (O input real costuma ser invisível/hidden)
                    
                    # Pega label do input ou texto próximo para saber o que é
                    lbl = finput.evaluate("el => el.getAttribute('aria-label') || el.parentElement.innerText || ''").lower()
                    
                    file_to_upload = None
                    
                    # A. É CARTA DE APRESENTAÇÃO?
                    if "cover" in lbl or "carta" in lbl or "apresentação" in lbl:
                        print(f"         📎 Detectado campo de CARTA DE APRESENTAÇÃO ({lbl[:30]}...)")
                        file_to_upload = target_cl
                        
                    # B. É CURRÍCULO (RESUME)? 
                    # Se tiver 'resume'/'cv' OU se não tiver label nenhuma (assume padrão)
                    elif "resume" in lbl or "currículo" in lbl or "cv" in lbl or not lbl:
                        print(f"         📎 Detectado campo de CURRÍCULO ({lbl[:30]}...)")
                        file_to_upload = target_cv
                    
                    # Se identificou o arquivo
                    if file_to_upload:
                        try: 
                            # Força o upload (Simulando drop ou click direto no input hidden)
                            finput.set_input_files([]) # Limpa anterior
                            finput.set_input_files(str(file_to_upload))
                            print(f"            ✅ Upload realizado com SUCESSO: {file_to_upload.name}")
                            time.sleep(1.0)
                        except Exception as e:
                            print(f"            ❌ Erro ao subir arquivo: {e}")
            except: pass

            print(f"      🔍 DEBUG: Upload de arquivos concluído. Chamando fill_form_turbo...")

            # 3. PREENCHER FORMULÁRIO
            print(f"      📝 Chamando fill_form_turbo (Etapa {step+1}/18)...")
            try:
                fill_form_turbo(page, candidate, is_english)
                print(f"      ✅ fill_form_turbo concluído")
            except Exception as e:
                print(f"      ❌ ERRO em fill_form_turbo: {e}")
                # Não abortamos aqui, deixamos a verificação abaixo decidir

            # --- 3.1. DUPLA VERIFICAÇÃO COM IA (NOVO) ---
            # Chama o Gemini para auditar a página antes de qualquer verificação
            try:
                audit_and_fix_page(page, is_english)
            except Exception as e:
                print(f"      ⚠️ Erro não-bloqueante na Auditoria IA: {e}")

            # 3.5. VERIFICAÇÃO PRÉ-CLIQUE (BLINDAGEM V36)
            # Garante que não há erros ANTES de avançar
            print(f"      🔍 Verificação pré-clique: Buscando erros de validação...")
            
            error_count = modal.locator(".artdeco-inline-feedback--error").count()
            # Regex para pegar PT e EN
            empty_dropdowns = modal.locator("text=/Selecionar opção|Select an option|Escolha uma opção/i").count()
            
            if error_count > 0 or empty_dropdowns > 0:
                print(f"      🚨 ERROS DETECTADOS ANTES DE CLICAR!")
                print(f"         - Erros de validação: {error_count}")
                print(f"         - Dropdowns vazios: {empty_dropdowns}")
                take_error_screenshot(page, "erro_validacao_pre")
                print(f"      🔨 Chamando fill_form_turbo NOVAMENTE para corrigir...")
                
                try:
                    time.sleep(1)
                    fill_form_turbo(page, candidate, is_english)
                    print(f"      ✅ Correção concluída. Verificando novamente...")
                    
                    # Verifica novamente após correção
                    error_count_after = modal.locator(".artdeco-inline-feedback--error").count()
                    empty_dropdowns_after = modal.locator("text=/Selecionar opção|Select an option|Escolha uma opção/i").count()
                    
                    # Verifica novamente após tentativa de correção
                    if error_count_after > 0 or empty_dropdowns_after > 0:
                        print(f"      ⚠️ AINDA HÁ ERROS APÓS CORREÇÃO! ({error_count_after} erros, {empty_dropdowns_after} vazios)")
                        print(f"      ⚠️ Incrementando stuck_counter e tentando clicar mesmo assim...")
                        stuck_counter += 1
                        # NÃO usa continue aqui - deixa tentar clicar
                    else:
                        print(f"      ✅ Todos os erros corrigidos! Pode avançar.")
                
                except Exception as e:
                    print(f"      ❌ Erro ao tentar corrigir: {e}")
                    stuck_counter += 1
                    # NÃO usa continue aqui - deixa tentar clicar
            else:
                print(f"      ✅ Nenhum erro detectado. Pronto para avançar!")

            # 4. AVANÇAR
            next_btn = modal.locator("footer button.artdeco-button--primary").first
            if next_btn.is_visible():
                txt = next_btn.inner_text().lower()
                if "submit" in txt or "enviar" in txt:
                    print("      🚀 Enviando candidatura...")
                next_btn.click(force=True)
                time.sleep(0.8)
                
                # Verifica se apareceu erro APÓS clicar (fallback)
                if page.locator(".artdeco-inline-feedback--error").count() > 0:
                     stuck_counter += 1
                     print(f"      ⚠️ Erro de validação detectado APÓS clicar. stuck_counter={stuck_counter}/3")
                     take_error_screenshot(page, "erro_validacao_pos")
                     fill_form_turbo(page, candidate, is_english)
                else: stuck_counter = 0 
            else:
                time.sleep(1)
        
        except Exception as e: 
            print(f"      ⚠️ Erro no loop principal (step {step}): {e}")

    # Se chegou aqui, esgotou as tentativas (travou ou erro desconhecido)
    print("      ⚠️ Tempo esgotado ou erro no modal. Cancelando...")
    
    # --- NOVO: ALARME TAMBÉM AQUI ---
    try:
        import winsound
        winsound.Beep(440, 500); winsound.Beep(440, 500)
    except: pass
    
    try:
        if not os.path.exists("erros_print"): os.makedirs("erros_print")
        page.screenshot(path=f"erros_print/erro_modal_timeout_{int(time.time())}.png")
    except: pass

    page.keyboard.press("Escape")
    time.sleep(0.5)
    handle_discard_popup(page)
    return False

# --- VALIDAÇÃO DE VAGA (PRÉ-CLIQUE) ---
def validate_job_card(card_element, strategy):
    try:
        text = card_element.inner_text(timeout=500).lower()
        if "candidatou-se" in text or "visualizar candidatura" in text: return False, "JÁ APLICADO"
        
        # Validação de Remoto
        if strategy["must_be_remote"]:
            # Se tiver termos presenciais e NÃO tiver a palavra remoto, bloqueia
            if any(x in text for x in ["presencial", "on-site", "híbrido", "hybrid"]) and "remoto" not in text:
                return False, "Não é remoto"
        
        # Blacklist de Títulos (Primeira Passada)
        for bad in BLACKLIST_TITLES:
            if bad in text: return False, f"Título proibido ({bad})"
            
        return True, "OK"
    except: return True, "OK"


# --- MOTOR PRINCIPAL ---
# --- MOTOR PRINCIPAL (V30.0 - STEALTH + HUMAN + SEM FRONTEIRA) ---
# --- MOTOR PRINCIPAL (V31.0 - CORREÇÃO DE BOTÃO + RANDOM FIX + GEMINI) ---
# --- MOTOR PRINCIPAL (V31.0 - CORREÇÃO DE BOTÃO + PRESERVA PRINTS DE ERRO) ---
# --- MOTOR PRINCIPAL (V32.0 - COMPLETO: TUDO RESTAURADO) ---
# --- SUBSTITUA A FUNÇÃO 'run_bot' INTEIRA (ATÉ O FINAL DO ARQUIVO) POR ISTO: ---
def run_bot():
    print("🚀 BOT V34.0 (BARREIRA DE LIXO ATIVA + RESPOSTAS TURBO)")
    config_path = Path(__file__).parent / "config.json"
    state_file = Path(__file__).parent / "bot_state.json"
    storage_path = Path(__file__).parent / "storage_state.json"
    
    if not os.path.exists("erros_print"): os.makedirs("erros_print")
    if not config_path.exists(): print("❌ config.json não encontrado!"); return
    with open(config_path, "r", encoding="utf-8") as f: config = json.load(f)

    kw_pt = ["Python Developer", "Data Analyst", "AI Engineer", "Backend Developer", "Analista de Dados", "Desenvolvedor Python", "Engenheiro de Dados", "Especialista em IA", "Business Intelligence", "Engenheiro de Software", "Analista de Sistemas", "Cientista de Dados", "Full Stack Python"]
    kw_en = ["Python Developer", "Data Analyst", "AI Engineer", "Backend Developer", "Machine Learning Engineer", "Data Scientist", "Software Engineer", "Data Engineer", "AI Specialist", "Generative AI Engineer", "LLM Engineer", "Python Automation"]

    SEARCH_STRATEGIES = [
        {"desc": "🏝️ FLORIANÓPOLIS", "loc": "Florianópolis, Santa Catarina", "f_WT": "1,3", "must_be_remote": False, "quota": 15, "keywords": kw_pt},
        {"desc": "🏙️ SÃO PAULO (Híbrido)", "loc": "São Paulo, Brazil", "f_WT": "3", "must_be_remote": False, "quota": 8, "keywords": kw_pt},
        {"desc": "🇧🇷 BRASIL REMOTO", "loc": "Brazil", "f_WT": "2", "must_be_remote": True, "quota": 14, "keywords": kw_pt},
        {"desc": "🌍 GLOBAL (Worldwide)", "loc": "Worldwide", "f_WT": "2", "must_be_remote": True, "quota": 13, "keywords": kw_en}
    ]

    state = {"last_reset": 0, "total_day": 0, "spanish_count": 0, "strat_counts": [0,0,0,0], "s_idx": 0, "k_idx": 0}
    if state_file.exists():
        try:
            with open(state_file, "r") as f: state = json.load(f)
            if time.time() - state.get("last_reset", 0) > 43200: 
                print("⏰ Resetando cotas (12h)...")
                state = {"last_reset": time.time(), "total_day": 0, "spanish_count": 0, "strat_counts": [0,0,0,0], "s_idx": 0, "k_idx": 0}
            if "spanish_count" not in state: state["spanish_count"] = 0
        except: pass

    with sync_playwright() as p:
        args = ["--disable-blink-features=AutomationControlled", "--start-maximized", "--no-sandbox"]
        browser = p.chromium.launch(headless=False, args=args, ignore_default_args=["--enable-automation"])
        
        context = browser.new_context(viewport={"width": 1920, "height": 1080}, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36", storage_state=str(storage_path) if storage_path.exists() else None)
        page = context.new_page()

        try: page.goto("https://www.linkedin.com/feed/", timeout=60000)
        except: pass
        
        if "login" in page.url or "security-check" in page.url:
             print("      🔑 Login detectado. Tentando recuperar...")
             time.sleep(3)
             try:
                 if page.locator(".profile-card").count() > 0: page.locator(".profile-card").first.click()
                 elif page.locator("[data-id='sign-in-form__submit-btn']").count() > 0: page.locator("[data-id='sign-in-form__submit-btn']").click()
                 page.wait_for_url("**/feed/**", timeout=15000)
             except: pass
        
        if "login" in page.url: 
            alert_user("Login necessário"); input("⚠️ Faça Login e ENTER..."); context.storage_state(path=str(storage_path))

        # LOOP INFINITO: Continua até atingir 50 candidaturas
        while True:
            # Verifica se atingiu a meta de 50 candidaturas
            if state["total_day"] >= 50:
                print("🎯 META DE 50 CANDIDATURAS ATINGIDA!")
                print("🛑 Pausando por 12 horas...")
                state["last_reset"] = time.time()
                with open(state_file, "w") as f: json.dump(state, f)
                time.sleep(43200)  # 12 horas
                # Reseta contadores após 12h
                state = {"last_reset": time.time(), "total_day": 0, "spanish_count": 0, "strat_counts": [0,0,0,0], "s_idx": 0, "k_idx": 0}
                with open(state_file, "w") as f: json.dump(state, f)
                print("⏰ Contadores resetados. Reiniciando...")
                continue
            
            print(f"\n📊 PROGRESSO: {state['total_day']}/50 candidaturas hoje")

            for s_idx in range(state["s_idx"], len(SEARCH_STRATEGIES)):
                strat = SEARCH_STRATEGIES[s_idx]
                target_quota = strat["quota"]
                surplus = sum(s["quota"] for s in SEARCH_STRATEGIES[:s_idx]) - sum(state["strat_counts"][:s_idx])
                effective_quota = target_quota + max(0, surplus)
                
                print(f"\n🌍 ESTRATÉGIA {s_idx+1}: {strat['desc']} | Meta: {effective_quota} (Feito: {state['strat_counts'][s_idx]})")

                start_k = state["k_idx"] if s_idx == state["s_idx"] else 0
                for k_idx in range(start_k, len(strat["keywords"])):
                    kw = strat["keywords"][k_idx]
                    state["s_idx"] = s_idx; state["k_idx"] = k_idx; 
                    with open(state_file, "w") as f: json.dump(state, f)

                    if state["strat_counts"][s_idx] >= effective_quota:
                        print("✅ Meta batida. Próxima...")
                        state["s_idx"] += 1
                        state["k_idx"] = 0
                        with open(state_file, "w") as f: json.dump(state, f)
                        break 

                    if state["total_day"] >= 50:
                        print("🛑 COTA 50/DIA. Saindo do loop interno...")
                        break  # Sai do loop de keywords

                    try:
                        url = f"https://www.linkedin.com/jobs/search/?keywords={kw}&location={strat['loc']}&f_WT={strat['f_WT']}&f_AL=true&sortBy=DD&f_TPR=r86400"
                        print(f"   🔎 Buscando: '{kw}'...")
                        page.goto(url, timeout=60000)
                        
                        # VERIFICAÇÃO: Garante que está na página correta
                        current_url = page.url
                        if "/jobs/search" not in current_url:
                            print(f"      ⚠️ Navegou para página errada: {current_url}")
                            print(f"      🔄 Redirecionando de volta para busca de vagas...")
                            page.goto(url, timeout=60000)
                            time.sleep(2.0)
                        
                        try:
                            page.wait_for_selector(".job-card-container", timeout=10000)
                            job_cards = page.locator(".job-card-container").all()
                            if len(job_cards) > 0:
                                box = job_cards[0].bounding_box()
                                if box: human_mouse_move(page, box['x'], box['y'])
                        except: pass
                    
                        time.sleep(random.uniform(2.0, 4.0)) 
                        
                        # --- BARREIRA DE LIXO (IGNORA SUGESTÕES) ---
                        cutoff_y = float('inf') 
                        stop_headers = [
                            "vagas que podem ser de seu interesse", "jobs you might be interested in",
                            "nenhuma vaga corresponde aos seus critérios", "no matching jobs found",
                            "veja as vagas que mais combinam com seu perfil", "people also viewed", "pessoas também viram"
                        ]
                        for header in stop_headers:
                            try:
                                el = page.locator(f"text={header}").first
                                if el.is_visible():
                                    box = el.bounding_box()
                                    if box:
                                        print(f"      🛑 Barreira detectada: '{header}' em Y={int(box['y'])}")
                                        cutoff_y = min(cutoff_y, box['y'])
                            except: pass
                        
                        job_cards = page.locator(".job-card-container").all()
                        print(f"      👀 {len(job_cards)} vagas visíveis.")

                        for i, card in enumerate(job_cards[:25]):
                            if state["strat_counts"][s_idx] >= effective_quota: break
                            
                            # VERIFICAÇÃO: Se saiu da página de vagas, volta
                            if "/jobs/search" not in page.url:
                                print(f"      ⚠️ Saiu da página de vagas! URL atual: {page.url}")
                                print(f"      🔄 Voltando para busca...")
                                page.goto(url, timeout=60000)
                                time.sleep(2.0)
                                break  # Recomeça a busca
                            
                            try:
                                # SE A VAGA ESTIVER ABAIXO DA FRASE, PARE TUDO.
                                box = card.bounding_box()
                                if box and box['y'] > cutoff_y:
                                    print(f"      ✋ Vaga ignorada (está abaixo das sugestões).")
                                    break 

                                if "premium" in page.url: page.go_back(); time.sleep(3)
                                
                                is_valid, reason = validate_job_card(card, strat)
                                if not is_valid: 
                                    print(f"      ❌ Ignorada ({i+1}): {reason}"); continue
                                
                                print(f"      👆 Clicando na vaga {i+1}...")
                                card.scroll_into_view_if_needed()
                                human_click(page, card)
                                time.sleep(2.0)
                                
                                try:
                                    full_title = page.locator(".job-details-jobs-unified-top-card__job-title").first.inner_text().lower()
                                    if any(b in full_title for b in BLACKLIST_TITLES):
                                        print(f"      ❌ Título Bloqueado: {full_title}"); continue
                                except: pass
                            
                                try:
                                    page.locator(".jobs-description__content").first.hover()
                                    page.mouse.wheel(0, 600); time.sleep(0.8)
                                except: pass
                                
                                lang_code = detect_language_from_page(page)
                                is_en = (lang_code == "en")
                                
                                # COTA ESPANHOL (5/dia)
                                if lang_code == "es":
                                    if state.get("spanish_count", 0) >= 5:
                                        print("      🛑 Cota de Espanhol (5) atingida. Pulando.")
                                        continue
                                    else:
                                        print(f"      🇪🇸 Vaga em Espanhol ({state.get('spanish_count', 0)}/5)")

                                # --- BLOCO DE CLIQUE CORRIGIDO (COM RE-TRY) ---
                                # 1. Busca o botão por texto exato (Mais confiável)
                                btn = page.locator("button").filter(has_text=re.compile(r"^(Candidatura simplificada|Easy Apply)$", re.I)).first
                                
                                # 2. Se não achar, busca por classe ou aria-label (Fallback)
                                if not btn.is_visible():
                                    btn = page.locator(".jobs-apply-button--top-card button, button[aria-label*='Simplificada'], button[aria-label*='Easy Apply']").first
                                
                                if btn.is_visible():
                                    text_btn = btn.inner_text().lower()
                                    aria_btn = (btn.get_attribute("aria-label") or "").lower()
                                    
                                    # Verifica se é realmente Simplificada
                                    if "easy" in text_btn or "simplificada" in text_btn or "easy" in aria_btn or "simplificada" in aria_btn:
                                         print(f"      🎯 Botão encontrado. Tentando clicar...")
                                         
                                         # TENTATIVA 1: Clique Humano Suave
                                         human_click(page, btn)
                                         time.sleep(2) # Dá tempo do modal animar

                                         # TENTATIVA 2: VERIFICA SE O MODAL ABRIU
                                         # Se o modal NÃO apareceu, o clique falhou. Vamos forçar!
                                         if page.locator(".jobs-easy-apply-modal").count() == 0:
                                             print("      ⚠️ Clique suave falhou. Forçando clique via JS...")
                                             try: btn.click(force=True); time.sleep(2)
                                             except: pass
                                         
                                         # CRÍTICO: Fecha modal de segurança IMEDIATAMENTE após clicar
                                         time.sleep(1.5)  # Dá tempo do modal de segurança aparecer
                                         for attempt in range(3):
                                             if close_security_modal(page, f"após-easy-apply-{attempt+1}"):
                                                 break
                                             if attempt < 2:
                                                 time.sleep(1.0)
                                         
                                         # Agora sim, processa a candidatura
                                         if process_easy_apply(page, config["candidate"], is_en):
                                            state["strat_counts"][s_idx] += 1
                                            state["total_day"] += 1
                                            if lang_code == "es": state["spanish_count"] += 1
                                            
                                            print(f"      ✅ APLICADO! Total: {state['total_day']}/50")
                                            with open(state_file, "w") as f: json.dump(state, f)
                                            slp = random.randint(50, 90)
                                            print(f"      💤 Pausa humana: {slp}s...")
                                            time.sleep(slp)
                                    else:
                                        print("      ⚠️ Botão encontrado mas é Vaga Externa (Não clicável).")
                                else:
                                    print("      ⚠️ Botão 'Simplificada' não encontrado.")

                            except Exception as e: 
                                print(f"      ⚠️ ERRO CARD {i+1}: {e}")
                                try: page.screenshot(path=f"erros_print/erro_card_{i}_{int(time.time())}.png")
                                except: pass

                    except Exception as e:
                        print(f"⚠️ Erro busca: {e}")
                        try: page.screenshot(path=f"erros_print/erro_busca_{int(time.time())}.png")
                        except: pass
                        if "premium" in page.url: page.go_back(); time.sleep(5)
                state["k_idx"] = 0
            
            # Fim de todas as estratégias - Reseta para começar de novo
            print("🔄 Completou todas as estratégias. Reiniciando do início...")
            state["s_idx"] = 0
            state["k_idx"] = 0
            with open(state_file, "w") as f: json.dump(state, f)
            time.sleep(5)  # Pequena pausa antes de reiniciar
            # Loop continua (while True)

if __name__ == "__main__":
    try: run_bot()
    except Exception as e:
        print(f"⚠️ ERRO CRÍTICO NO MAIN: {e}")
        try: winsound.Beep(500, 1000)
        except: pass