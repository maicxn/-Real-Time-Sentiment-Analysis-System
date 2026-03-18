# Como Rodar o Projeto

Este guia mostra como rodar a API de Análise de Sentimentos localmente no seu computador (Windows).

## Requisitos
Para rodar este projeto é necessário ter o **Python (versão 3.10 ou superior)** instalado na sua máquina.

### 1. Instalar as Dependências
Abra o terminal dentro da pasta do projeto e instale as bibliotecas necessárias rodando o seguinte comando:
```bash
python -m pip install -r requirements.txt
```

### 2. Iniciar o Servidor (API)
Com as dependências instaladas, inicie a API utilizando o `uvicorn` através do Python:

```bash
python -m uvicorn main:app --reload
```
Aguarde até ver a mensagem `Application startup complete.` no terminal.

### 3. Acessar e Testar a API
Para enviar requisições e testar sua API visualmente, utilize a documentação interativa gerada pelo Swagger:

👉 **Acesse no seu navegador:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Lá, você verá o endpoint POST `/analyze-feed`.
Para testar:
1. Clique na rota `/analyze-feed` (caixa verde)
2. Clique no botão **"Try it out"** à direita
3. Edite o JSON de exemplo (se desejar)
4. Clique no botão azul **"Execute"** para enviar os dados para a sua API e ver a análise de sentimentos retornada!

### 4. Executar os Testes Automatizados (Opcional)
Este projeto conta com uma suíte de testes preparada no `pytest`. Para garantir que toda a lógica de negócio e da API está operando perfeitamente, você pode rodar (com o servidor `uvicorn` desligado ou em outro terminal):
    
```bash
python -m pytest
```
*Você verá os testes passando no console, confirmando que tudo está em ordem.*

---

## 🛠️ Passos Opcionais

### A) Não tenho Python instalado
Caso ainda não tenha o Python (versão 3.10 ou superior) instalado, abra o terminal como Administrador e instale-o pelo gerenciador de pacotes do Windows:
```bash
winget install -e --id Python.Python.3.12
```
*Após a instalação, feche e abra o terminal novamente.*

### B) Como usar um Ambiente Virtual (venv)
O `venv` serve para isolar as bibliotecas do projeto da sua máquina. Se desejar utilizá-lo, siga os passos abaixo **antes** de instalar as dependências (Passo 1):

Abra o terminal na pasta do projeto e crie o ambiente:
```bash
python -m venv venv
```
Para **ativá-lo**, rode:
```bash
venv\Scripts\activate
```
*(Seu terminal mostrará `(venv)` no começo da linha)*. Depois, basta seguir normalmente os passos 1 e 2 lá do começo do guia!
