# 🏋️ Assistente de Treino Físico com MCP

O avanço das tecnologias de inteligência artificial tem permitido o surgimento de soluções inovadoras em diversas áreas, incluindo saúde e atividade física. O uso de LLMs (Large Language Models) abre novas possibilidades para a criação de assistentes inteligentes capazes de compreender e adaptar-se ao contexto do usuário em tempo real.

Neste trabalho, propomos o desenvolvimento de uma assistente de treino físico que, utilizando dados como batimentos cardíacos e preferências pessoais, seja capaz de recomendar os melhores exercícios de forma dinâmica e personalizada. O diferencial da proposta está na integração com o Model Context Protocol, que permite o refinamento contínuo das respostas da LLM com base em dados contextuais atualizados. Essa abordagem visa tornar a prática de atividades físicas mais segura e eficiente, contribuindo para uma melhor adesão e resultados por parte dos usuários.

## 📋 Funcionalidades

### Core Features
- **Perfil Personalizado**: Criação de perfis com idade, peso, nível fitness e condições de saúde
- **Zonas de FC**: Cálculo automático das 5 zonas de frequência cardíaca
- **Recomendações Dinâmicas**: Exercícios adaptados à FC atual e perfil do usuário
- **Monitoramento**: Registro e análise de sessões de treino
- **Analytics**: Estatísticas de progresso e insights personalizados

### Integração MCP
- Compatível com Claude Desktop via Model Context Protocol
- Tools disponíveis como ferramentas nativas do assistente
- Contexto dinâmico baseado em dados biométricos em tempo real
- Refinamento contínuo das recomendações com base em dados contextuais

## 🚀 Instalação

### Pré-requisitos
- Python 3.9 ou superior
- PostgreSQL (opcional, usa banco em memória por padrão)

### Instalação Automática
```bash
# Clone o repositório
git clone https://github.com/matheus1103/fitness-assistant-mcp
cd fitness-assistant-mcp

# Execute o script de setup
python src/scripts/setup.py
```

### Instalação Manual
```bash
# Instale as dependências
pip install -r requirements.txt

# Configure o ambiente
cp .env.example .env
# Edite o arquivo .env conforme necessário

# Execute as migrações (se usando PostgreSQL)
alembic upgrade head
```

## 🔧 Configuração

### Integração com Claude Desktop

1. **Localize o arquivo de configuração**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. **Adicione a configuração MCP**:
```json
{
  "mcp_servers": {
    "fitness-assistant": {
      "command": "python",
      "args": ["/caminho/para/seu/projeto/src/fitness_assistant/main.py"],
      "env": {
        "PYTHONPATH": "/caminho/para/seu/projeto"
      }
    }
  }
}
```

3. **Reinicie o Claude Desktop**

### Configuração de Banco de Dados

#### SQLite (Padrão)
```env
DATABASE_TYPE=memory
# ou
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/fitness.db
```

#### PostgreSQL
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost/fitness_db
```

## 💡 Como Usar

### 1. Criação de Perfil
```
Crie um perfil para usuário joão123: 28 anos, 75kg, 1.75m, nível intermediário, sem condições de saúde, prefere cardio e musculação
```

### 2. Cálculo de Zonas de FC
```
Calcule as zonas de frequência cardíaca para idade 28 anos e FC repouso 65 bpm
```

### 3. Recomendações de Exercício
```
Minha FC atual é 140 bpm, recomende exercícios para uma sessão de 45 minutos
```

### 4. Registro de Treino
```
Registre minha sessão: corrida 25min + musculação 12min, duração total 45min, FC média 142, esforço percebido 6/10
```

### 5. Análise de Progresso
```
Mostre meu progresso nos últimos 30 dias e dê insights sobre minha evolução
```

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
src/
├── fitness_assistant/
│   ├── main.py              # Servidor MCP principal
│   ├── tools/               # Ferramentas MCP
│   ├── models/              # Modelos de dados
│   ├── database/            # Camada de persistência
│   └── core/                # Lógica de negócio
├── scripts/                 # Scripts de setup e manutenção
└── tests/                   # Testes automatizados
```

### Executando Testes
```bash
# Testes unitários
python -m pytest tests/

# Testes com cobertura
python -m pytest tests/ --cov=fitness_assistant --cov-report=html

# Testes de integração
python -m pytest tests/integration/
```

## Arquitetura

### Model Context Protocol (MCP)
O sistema utiliza o MCP para:
- **Contextualização Dinâmica**: Atualização contínua do contexto baseado em dados biométricos
- **Personalização Adaptativa**: Refinamento das recomendações com base no histórico do usuário
- **Integração Seamless**: Funcionamento nativo dentro do Claude Desktop

### Algoritmos de Recomendação
- **Análise de Zona FC**: Classificação automática da intensidade do exercício
- **Filtragem Colaborativa**: Recomendações baseadas em usuários similares
- **Adaptação Temporal**: Ajuste das recomendações com base no horário e frequência de treino
- **Prevenção de Lesões**: Monitoramento de carga de treino e sinais de fadiga

### Segurança e Privacidade
- Dados biométricos criptografados
- Processamento local quando possível
- Conformidade com LGPD/GDPR
- Consentimento informado para coleta de dados

## Métricas e Analytics

### Indicadores Principais
- **Aderência**: Percentual de sessões completadas vs. planejadas
- **Progresso**: Evolução de métricas como FC de repouso e capacidade aeróbica
- **Segurança**: Incidência de alertas de FC alta e feedbacks de dor/desconforto
- **Satisfação**: Avaliação do usuário sobre as recomendações

### Dashboards Disponíveis
- Progresso semanal/mensal
- Distribuição de tipos de exercício
- Análise de zonas de FC
- Tendências de performance

## Trabalhos futuros

- **Algoritmos de recomendação mais sofisticados**
- **Integração com mais dispositivos**
- **Interface de usuário**
- **Validação médica das recomendações**

## Disclaimer

Este assistente é para fins educacionais e informativos. Sempre consulte profissionais de saúde antes de iniciar novos programas de exercício, especialmente se tiver condições médicas pré-existentes.

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Autor

- **Matheus Francisco** - *Desenvolvimento inicial* - [matheus1103](https://github.com/matheus1103)

---

**Desenvolvido usando FastMCP e Claude**