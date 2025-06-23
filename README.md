# 🏋️ Assistente de Treino Físico com MCP

Um assistente inteligente para recomendações personalizadas de exercícios usando Large Language Models e Model Context Protocol.

## 📋 Funcionalidades

### Core Features
- **Perfil Personalizado**: Criação de perfis com idade, peso, nível fitness e condições de saúde
- **Zonas de FC**: Cálculo automático das 5 zonas de frequência cardíaca
- **Recomendações Dinâmicas**: Exercícios adaptados à FC atual e perfil do usuário
- **Monitoramento**: Registro e análise de sessões de treino
- **Analytics**: Estatísticas de progresso e insights personalizados

### Integração MCP
- Compatible com Claude Desktop via Model Context Protocol
- Tools disponíveis como ferramentas nativas do assistente
- Contexto dinâmico baseado em dados biométricos em tempo real

## 🚀 Instalação

### Pré-requisitos
```bash
pip install fastmcp pydantic numpy
```

### Configuração Básica
1. Salve o código principal como `fitness_assistant.py`
2. Execute localmente para testes:
```bash
python fitness_assistant.py
```

### Integração com Claude Desktop

1. **Localize o arquivo de configuração**:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Adicione a configuração MCP**:
```json
{
  "mcp_servers": {
    "fitness-assistant": {
      "command": "python",
      "args": ["/caminho/para/seu/fitness_assistant.py"],
      "env": {}
    }
  }
}
```

3. **Reinicie o Claude Desktop**

## 💡 Como Usar

### 1. Criação de Perfil
```python
# Via MCP no Claude
"Crie um perfil para usuário joão123: 28 anos, 75kg, 1.75m, nível intermediário, sem condições de saúde, prefere cardio e musculação"
```

### 2. Cálculo de Zonas de FC
```python
# Calcula zonas baseadas na idade e FC de repouso
"Calcule as zonas de frequência cardíaca para idade 28 anos e FC repouso 65 bpm"
```

### 3. Recomendações de Exercício
```python
# Baseado na FC atual e perfil
"Minha FC atual é 140 bpm, recomende exercícios para uma sessão de 45 minutos"
```

### 4. Registro de Treino
```python
# Após completar exercícios
"Registre minha sessão: corrida 25min + musculação 12min, duração total 45min, FC média 142, esforço percebido 6/10"
```

### 5. Análise de Progresso
```python
# Analytics dos últimos 30 dias
"Mostre minha análise de progresso dos últimos 30 dias"
```

## 🔧 Arquitetura

### Componentes Principais

```
fitness_assistant.py
├── FastMCP Server
├── Pydantic Models
│   ├── UserProfile
│   ├── HeartRateData
│   └── ExerciseRecommendation
├── MCP Tools
│   ├── create_user_profile()
│   ├── calculate_heart_rate_zones()
│   ├── recommend_exercise()
│   ├── log_workout_session()
│   └── get_workout_analytics()
└── Helper Functions
    ├── determine_current_zone()
    ├── generate_safety_notes()
    └── estimate_calories()
```

### Fluxo de Dados
```
Dados Biométricos → Análise de Contexto → LLM → Recomendações → Feedback Loop
```

## 📊 Zonas de Frequência Cardíaca

| Zona | Nome | % FC Máx | Benefícios |
|------|------|----------|------------|
| 1 | Recuperação Ativa | 50-60% | Recuperação, queima gordura |
| 2 | Aeróbica Base | 60-70% | Resistência cardiovascular |
| 3 | Tempo/Ritmo | 70-80% | Eficiência aeróbica |
| 4 | Limiar Anaeróbico | 80-90% | Capacidade anaeróbica |
| 5 | VO2 Max | 90-100% | Potência máxima |

## 🛡️ Recursos de Segurança

### Monitoramento Automático
- Alertas para FC muito alta (>180 bpm)
- Adaptações para condições de saúde específicas
- Recomendações idade-específicas

### Condições Suportadas
- Diabetes: Lembretes sobre glicemia
- Hipertensão: Evita exercícios isométricos prolongados
- 65+ anos: Aquecimento extra e alongamento

## 📈 Analytics e Progresso

### Métricas Calculadas
- Sessões por semana
- Duração média por sessão
- FC média durante exercícios
- Estimativa de calorias queimadas
- Notas de progresso automatizadas

### Insights Automáticos
- Detecção de melhoria cardiovascular
- Análise de consistência nos treinos
- Recomendações de ajuste de intensidade

## 🎯 Casos de Uso

### Para Iniciantes
- Exercícios seguros e progressivos
- Monitoramento de intensidade
- Educação sobre zonas de FC

### Para Intermediários/Avançados
- Otimização de treinos baseada em dados
- Análise de performance detalhada
- Recomendações de periodização

### Para Profissionais
- Ferramenta de apoio para personal trainers
- Base para desenvolvimento de apps fitness
- Integração com dispositivos IoT

## 🔄 Próximos Passos

### Expansões Planejadas
- [ ] Integração com wearables (Apple Watch, Garmin)
- [ ] Machine Learning para predições
- [ ] Planos de treino de longo prazo
- [ ] Integração com APIs de nutrição
- [ ] Dashboard web interativo
- [ ] Notificações push
- [ ] Compartilhamento social

### Melhorias Técnicas
- [ ] Persistência em banco de dados
- [ ] API REST complementar
- [ ] Testes automatizados
- [ ] Deploy em cloud
- [ ] Monitoramento e logs

## 🤝 Contribuindo

Contribuições são bem-vindas! Áreas prioritárias:
- Algoritmos de recomendação mais sofisticados
- Integração com mais dispositivos
- Interface de usuário
- Validação médica das recomendações

## ⚠️ Disclaimer

Este assistente é para fins educacionais e informativos. Sempre consulte profissionais de saúde antes de iniciar novos programas de exercício, especialmente se tiver condições médicas pré-existentes.

---

**Desenvolvido com ❤️ usando FastMCP e Claude**