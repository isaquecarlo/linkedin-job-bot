# LinkedIn Job Application Bot

Bot automatizado para realizar candidaturas em vagas do LinkedIn usando Playwright e IA (Google Gemini + Ollama).

## 🚀 Funcionalidades

- **Automação completa** de candidaturas no LinkedIn
- **IA Híbrida** para responder formulários (Google Gemini + Ollama)
- **Regras Configuráveis**: Defina sua pretensão salarial, experiência e respostas padrão em um arquivo simples (`config.json`)
- **Detecção de idioma** (PT, EN, ES)
- **Logs detalhados**: Mantém registro de todas as perguntas e respostas
- **Cotas de segurança**: Limite diário de candidaturas para evitar bloqueios

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Uma API Key do Google Gemini ([obter aqui - é grátis](https://aistudio.google.com/app/apikey))
- Conta no LinkedIn
- Seus currículos em PDF (Português e Inglês)

## 🛠️ Instalação Passo a Passo

### 1. Clonar o projeto
```bash
git clone https://github.com/seu-usuario/linkedin-job-bot.git
cd linkedin-job-bot
```

### 2. Criar ambiente virtual (Recomendado)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Instalar navegadores do Playwright (⚠️ Obrigatório)
```bash
playwright install chromium
```

## ⚙️ Configuração (Crucial)

O bot não funciona sem isso. Siga com atenção:

### 1. Configurar Variáveis de Ambiente
Renomeie o arquivo `.env.example` para `.env` e adicione sua chave:
```bash
cp .env.example .env
```
Abra o `.env` e coloque sua chave:
```intent
GOOGLE_API_KEY=AIzaSy...SuaChaveAqui
```

### 2. Configurar seus Dados (`config.json`)
Renomeie o arquivo `config.json.example` para `config.json`:
```bash
cp config.json.example config.json
```

**Abra o `config.json` e preencha TODOS os campos:**
- **`candidate`**: Seus dados pessoais.
- **`resume_text`**: Copie e cole o texto do seu currículo aqui (para a IA ler).
- **`ai_rules`**: AQUI você define como a IA deve responder:
    - `"salary_brl"`: Sua pretensão em Reais.
    - `"salary_usd"`: Sua pretensão em Dólar.
    - `"city_country"`: Onde você mora (ex: "São Paulo, Brazil").
    - `"experience_years..."`: Quantos anos de experiência declarar.
- **`credentials`**: Seu email e senha do LinkedIn.

### 3. Adicionar seus Currículos
Coloque seus arquivos PDF na pasta raiz do projeto e atualize os nomes no `config.json`:
```json
"pdf_paths": {
    "cv_pt": "SEU_CURRICULO_PT.pdf",
    "cv_en": "SEU_CURRICULO_EN.pdf",
    ...
}
```

## 🎯 Como Usar

Com tudo configurado, apenas rode:

```bash
python job_bot.py
```

O navegador abrirá e o bot começará a trabalhar.

### Dicas:
- **Primeira execução**: Pode ser necessário fazer login manualmente ou resolver um CAPTCHA.
- **Logs**: Verifique `application_log.txt` para ver o que o bot está fazendo.
- **Perguntas**: Verifique `questions_answers_log.json` para ver como a IA está respondendo.

## 🛡️ Segurança

- **NUNCA** envie seu arquivo `config.json` ou `.env` para o GitHub. Eles contêm suas senhas.
- O arquivo `.gitignore` já está configurado para preveni-lo de fazer isso, não o remova.

## 🤝 Contribuindo

Sinta-se livre para abrir Issues ou Pull Requests para melhorar o bot!

## ⚠️ Aviso Legal

Este projeto é para fins educacionais. O uso de bots pode violar os Termos de Serviço do LinkedIn. Use com moderação e responsabilidade.
