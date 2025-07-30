# Configuração do GitHub para AURA NEXUS

## Opção 1: Via Browser (Mais Simples)

1. **Criar o repositório no GitHub:**
   - Acesse: https://github.com/new
   - Nome do repositório: `aura-nexus`
   - Descrição: "Sistema avançado de enriquecimento de leads empresariais"
   - Deixe como Public
   - NÃO inicialize com README (já temos)
   - Clique em "Create repository"

2. **Conectar seu repositório local:**
   ```bash
   cd aura-nexus-clean
   git remote add origin https://github.com/eluzquadros/aura-nexus.git
   git branch -M main
   git push -u origin main
   ```

3. **Quando pedir credenciais:**
   - Username: `eluzquadros`
   - Password: Use um Personal Access Token (não sua senha)

## Opção 2: Criar Personal Access Token

1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token (classic)"
3. Nome: "AURA NEXUS Push"
4. Expiração: 90 dias
5. Selecione permissões:
   - [x] repo (todos)
   - [x] workflow
6. Clique em "Generate token"
7. COPIE O TOKEN (só aparece uma vez!)

## Opção 3: Usar Git Credential Manager

```bash
# Windows já tem o Git Credential Manager
# Ao fazer push, abrirá uma janela do browser
git push -u origin main
# Faça login no browser quando solicitado
```

## Comandos Completos:

```bash
# Entrar na pasta do projeto
cd C:\workspace\aura_nexus\aura-nexus-clean

# Adicionar repositório remoto
git remote add origin https://github.com/eluzquadros/aura-nexus.git

# Verificar remoto
git remote -v

# Renomear branch para main (padrão GitHub)
git branch -M main

# Fazer push inicial
git push -u origin main
```

## Após o Push:

1. Acesse: https://github.com/eluzquadros/aura-nexus
2. Configure:
   - About: Adicione descrição e topics
   - Settings > Pages: Para documentação
   - Issues: Para rastreamento
   - Actions: Para CI/CD

## Segurança:

⚠️ **IMPORTANTE**: 
- NUNCA use sua senha real do GitHub
- Use Personal Access Token ou OAuth
- Mude sua senha se ela foi exposta