# Antorx

O **Antorx** é uma ferramenta de automação de navegador desenvolvida em Python e Selenium para auxiliar o preenchimento sequencial da tela **Relação de Passageiros (Passo 2)** do sistema SISAUT/ANTT.

> **Importante:** `passengers.example.csv` contém apenas dados fictícios. O programa bloqueia o uso direto desse arquivo para o cadastro. Para um cadastro real autorizado, crie um arquivo local chamado `passageiros.csv`, revise os dados e mantenha-o fora do Git.

> **Projeto independente:** este repositório não é oficial, afiliado, patrocinado ou endossado pela ANTT. Verifique as regras aplicáveis ao sistema e obtenha autorização antes de usar a automação.

## Índice

- [Funcionalidades](#funcionalidades)
- [Limitações e responsabilidade](#limitações-e-responsabilidade)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Preparar a lista CSV](#preparar-a-lista-csv)
- [Órgão emissor](#órgão-emissor)
- [Executar a automação](#executar-a-automação)
- [Modo de inspeção](#modo-de-inspeção)
- [Se a automação parar](#se-a-automação-parar)
- [Privacidade e Git](#privacidade-e-git)
- [Solução de problemas](#solução-de-problemas)
- [Executar os testes](#executar-os-testes)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Licença](#licença)

## Funcionalidades

- Abre o Chrome ou Chromium e permite que a pessoa faça login manualmente.
- Procura o formulário de passageiros nas abas e frames abertos.
- Preenche os campos de nome, situação, tipo de documento, número do documento e órgão emissor.
- Aguarda a resposta de cada inclusão e tenta confirmar que o registro apareceu na tabela.
- Interrompe a execução quando o resultado é incerto, sem repetir automaticamente o clique, para reduzir o risco de duplicidades.
- Oculta nomes e números de documentos das mensagens normais do terminal.

O script seleciona as opções **Brasileiro Maior** e **Carteira de Identidade**, de acordo com os valores observados no formulário usado durante o desenvolvimento. O órgão emissor padrão é `SSP`, mas pode ser alterado ou deixado vazio.

## Limitações e responsabilidade

- O login é manual. O programa não solicita nem armazena a senha.
- A automação foi escrita para a estrutura específica do formulário clássico identificado durante o desenvolvimento. Mudanças no portal podem exigir ajustes.
- O tipo de documento é definido como **Carteira de Identidade** para todos os registros. Confirme se isso está correto para cada passageiro e para o procedimento.
- O script remove pontuação do campo de documento, mas não valida o comprimento, os dígitos verificadores ou a correspondência entre pessoa e documento.
- Registros com documento vazio não são enviados automaticamente e precisam ser tratados manualmente.
- A automação não emite a licença/autorização final da viagem.
- A detecção automática de sucesso não substitui a conferência final no portal.
- Use o programa somente com autorização e revise a lista e a viagem antes de confirmar o envio.

## Requisitos

- Windows 10/11, macOS ou Linux.
- Python 3.9 ou superior.
- Google Chrome ou Chromium instalado.
- Acesso à internet para instalar dependências e acessar o SISAUT.
- Conta e permissão para usar o sistema.

O Selenium Manager pode baixar/configurar um driver compatível com o navegador na primeira execução. O programa não instala o navegador e não tenta contornar autenticação, CAPTCHA ou outros controles do portal.

## Instalação

Baixe ou clone o repositório e execute os comandos na pasta do projeto. Escolha o bloco do seu sistema operacional.

### Windows (PowerShell ou Prompt de Comando)

Instale Python 3.9+ e Google Chrome/Chromium. Depois execute:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Ou execute `install.bat`. Para rodar a ferramenta, use `run.bat`.

### macOS

Instale Python 3.9+ e Google Chrome/Chromium. No Terminal, execute:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Ou use os scripts `./install.sh` e `./run.sh`.

### Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Em algumas distribuições, pode ser necessário instalar o pacote de suporte ao ambiente virtual (por exemplo, `python3-venv`). Os scripts `./install.sh` e `./run.sh` são opcionais.

### Atualizar dependências

Com o ambiente virtual criado, execute:

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS/Linux:**

```bash
.venv/bin/python -m pip install -r requirements.txt
```

## Preparar a lista CSV

O arquivo `passengers.example.csv` é apenas uma demonstração e o programa bloqueia seu uso direto para o cadastro. Crie uma cópia local chamada **`passageiros.csv`** e substitua os marcadores fictícios pelos dados corretos.

**Windows (PowerShell):**

```powershell
Copy-Item passengers.example.csv passageiros.csv
```

**macOS/Linux:**

```bash
cp passengers.example.csv passageiros.csv
```

Edite `passageiros.csv` localmente. O `.gitignore` ignora esse arquivo e os demais CSVs locais por padrão. Nunca coloque dados reais no arquivo de exemplo versionado.

### Formato do arquivo

O arquivo deve usar codificação **UTF-8**, separador **ponto e vírgula (`;`)** e uma linha de cabeçalho. Use estas colunas:

```csv
name;document
fictional passenger 01;DOCUMENT_PLACEHOLDER_DO_NOT_SUBMIT
fictional passenger 02;DOCUMENT_PLACEHOLDER_DO_NOT_SUBMIT
fictional passenger without document;
```

O texto `DOCUMENT_PLACEHOLDER_DO_NOT_SUBMIT` não contém dígitos; o programa o trata como um documento vazio. Assim, os passageiros de exemplo não entram na fila de envio automático. Mesmo assim, nunca envie dados fictícios ao portal.

**Colunas:**

- `name` (**obrigatória**): nome que será digitado no formulário.
- `document` (**recomendada**): número que será digitado no campo de documento. Pontuação e letras são removidas; o valor não é validado. Preserve zeros iniciais configurando a coluna como texto no editor de planilhas.

Para compatibilidade, também são aceitos os cabeçalhos antigos em português `nome`, `documento` e `cpf`.

Linhas com nome preenchido e documento vazio são contabilizadas, mas **não são enviadas automaticamente**. Linhas sem nome são ignoradas.

## Órgão emissor

O órgão emissor é `SSP` por padrão. Use `--issuer` para informar outro valor. A opção é aplicada a todos os passageiros naquela execução.

```bash
./run.sh --csv passageiros.csv --issuer SSP
./run.sh --csv passageiros.csv --issuer SSP-PI
./run.sh --csv passageiros.csv --issuer ""
```

No Windows, use `run.bat` no lugar de `./run.sh`:

```powershell
run.bat --csv passageiros.csv --issuer SSP
run.bat --csv passageiros.csv --issuer ""
```

O valor vazio deixa o campo do órgão emissor em branco. Se cada passageiro exigir um órgão diferente, esta versão não oferece um órgão por linha; confira as exigências do formulário e os documentos antes de enviar.

## Executar a automação

Confira o arquivo `passageiros.csv` e abra o sistema para a viagem correta antes de começar.

**macOS/Linux:**

```bash
./run.sh --csv passageiros.csv --issuer SSP
```

**Windows:**

```powershell
run.bat --csv passageiros.csv --issuer SSP
```

Também é possível executar diretamente o Python do ambiente virtual:

**macOS/Linux:**

```bash
.venv/bin/python main.py --csv passageiros.csv --issuer SSP
```

**Windows:**

```powershell
.\.venv\Scripts\python.exe main.py --csv passageiros.csv --issuer SSP
```

### Fluxo de execução

1. O navegador é aberto.
2. Faça login manualmente e navegue até a viagem correta e a tela **Relação de Passageiros (Passo 2)**.
3. Volte ao terminal e pressione `Enter` quando solicitado.
4. Confira a quantidade de registros com documento e dos que ficaram para preenchimento manual.
5. Para iniciar, digite exatamente `SIM`. Qualquer outra resposta cancela o envio.
6. Acompanhe o resultado e confira a tabela do SISAUT.

O programa não repete um clique se não consegue confirmar o resultado. Se houver interrupção, confira a tabela antes de executar novamente para não duplicar passageiros.

## Modo de inspeção

O modo de inspeção procura os controles esperados, mas não aciona o botão de inclusão. Ele pode ser usado com o CSV de exemplo.

**macOS/Linux:**

```bash
./run.sh --inspect
```

**Windows:**

```powershell
run.bat --inspect
```

Faça login manualmente e abra a tela de passageiros. Encontrar os controles não garante que o portal continuará compatível nem confirma permissão para cadastrar dados.

## Se a automação parar

**Não execute a lista completa novamente antes de conferir a tabela.** Alguns passageiros podem ter sido incluídos antes da falha.

1. Deixe o navegador aberto e confira os registros no SISAUT.
2. Identifique quais registros foram efetivamente incluídos.
3. Prepare um novo CSV local contendo apenas os passageiros que faltam.
4. Confira os dados e a viagem antes de retomar.

O registro oficial no portal é a referência final, não apenas a mensagem do terminal.

## Privacidade e Git

O `.gitignore` ignora arquivos CSV e planilhas locais, ambientes virtuais, arquivos de configuração sensíveis, chaves e capturas de tela. A única exceção CSV versionada é `passengers.example.csv`, que contém marcadores fictícios.

O `.gitignore` ajuda a evitar publicações acidentais, mas não é uma garantia de segurança:

- Ele não deixa de rastrear arquivos que já foram adicionados ao Git. Antes de publicar, confira `git status --short` e `git diff --cached`.
- Se um CSV real já estiver sendo rastreado, remova-o do índice com `git rm --cached passageiros.csv` e revise o histórico antes de publicar. Apagar do último commit não remove necessariamente dados de commits antigos.
- Não use `git add -f` para forçar arquivos de dados.
- Nunca publique nomes, documentos reais, credenciais, cookies, tokens ou capturas identificáveis.
- Restrinja o acesso aos arquivos locais e apague cópias quando deixarem de ser necessárias, conforme as regras aplicáveis.

## Solução de problemas

### Ambiente virtual não encontrado

Execute os passos da seção [Instalação](#instalação). No Windows, confirme que `py -3` funciona; no macOS/Linux, confirme `python3 --version`.

### Chrome não abre ou ocorre erro de driver

Confirme que Chrome/Chromium está instalado e abre normalmente. Verifique a internet e atualize o Selenium pelo Python do ambiente virtual. Regras de rede ou restrições corporativas podem impedir que o Selenium Manager configure o driver.

### Formulário não localizado

Confirme que você está na tela **Relação de Passageiros (Passo 2)** e que a página carregou. A sessão pode ter expirado ou o site pode ter mudado. Confira manualmente e não tente contornar controles de segurança.

### Resposta demora ou a execução para

Confira a tabela no SISAUT antes de tentar novamente. Não repita uma inclusão sem confirmar se ela já foi salva.

### Acentos ou zeros iniciais ficaram incorretos

Salve o CSV em UTF-8 e configure a coluna `document` como texto no editor de planilhas. Abra e revise o arquivo exportado antes de executar.

## Executar os testes

Com as dependências instaladas, execute na pasta do projeto.

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**macOS/Linux:**

```bash
.venv/bin/python -m unittest discover -s tests -v
```

O GitHub Actions também executa os testes em Windows, macOS e Ubuntu com Python 3.11 e 3.12 em cada push e pull request. Esses testes podem detectar falhas no código, mas não testam o cadastro real no portal, pois isso exige uma sessão autenticada e uma viagem de teste autorizada.

## Estrutura do projeto

```text
antorx/
├── .github/workflows/tests.yml
├── .gitignore
├── LICENSE
├── README.md
├── install.bat
├── install.sh
├── main.py
├── passengers.example.csv
├── requirements.txt
├── run.bat
├── run.sh
└── tests/test_main.py
```

## Licença

O Antorx é distribuído sob a licença [MIT](LICENSE). Consulte o arquivo `LICENSE` para ver os termos completos.
