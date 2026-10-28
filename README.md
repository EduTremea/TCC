# Reescrita de consultas SQL com modelos de linguagem

Trabalho de Conclusão de Curso em Ciência da Computação, Atitus Educação (Passo Fundo, RS). Autor: Luiz Eduardo Treméa. Orientador: Fahad Kalil.

O artigo compara dois modelos locais, executados em CPU pelo Ollama (llama3.2 3B e llama3 8B), com o GPT-4o na reescrita de consultas SQL. O modelo só propõe a reescrita; o PostgreSQL executa a original e a reescrita, compara os resultados e classifica cada execução em cinco categorias, com o custo estimado pelo planejador como medida de ganho. O experimento usa 18 consultas de uma base controlada e quatro do TPC-H, em quatro fases de contexto e três repetições.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `sbc-template.tex` | texto do artigo (modelo SBC com os ajustes da Atitus) |
| `sbc-template.bib` | referências, no padrão ABNT (biblatex-abnt) |
| `sbc-template.pdf` | versão compilada do artigo |
| `figuras/` | figuras usadas no artigo |
| `sbc-template.sty`, `sty/`, `latexmkrc` | estilos do modelo e configuração da compilação |
| `Execução/prototipo/` | código do experimento, consultas e instruções de reprodução |
| `Execução/resultados/` | tabelas, CSV, figuras e planilha com todas as execuções |

## Compilar o artigo

São necessários pdfLaTeX, biber e o pacote biblatex-abnt. Com eles instalados, na raiz do repositório:

```bash
latexmk -pdf sbc-template.tex
```

O `latexmkrc` acrescenta a pasta `sty/` ao caminho de busca, por isso a compilação deve ser feita pelo `latexmk` ou por uma extensão que o use.

**Windows.** Instale o [MiKTeX](https://miktex.org/download), usado no desenvolvimento, ou o [TeX Live](https://mirror.ctan.org/systems/texlive/tlnet/install-tl-windows.exe), cuja instalação completa ocupa cerca de 10 GB. O MiKTeX pode instalar sozinho os pacotes que faltarem, se a instalação automática estiver ativada no MiKTeX Console.

**Ubuntu / Debian.**

```bash
sudo apt update
sudo apt install -y texlive-latex-recommended texlive-latex-extra texlive-lang-portuguese texlive-fonts-extra texlive-bibtex-extra biber latexmk
```

**VS Code.** A extensão LaTeX Workshop (James Yu) compila com `latexmk` ao salvar.

## Resultados

A pasta `Execução/resultados/` guarda a saída usada no artigo:

- `tcc_execucoes_classificadas.csv` e `tpch_execucoes_classificadas.csv`: uma linha por execução (648 na base controlada e 144 no TPC-H), com o prompt, a reescrita, o custo, o tempo e a categoria;
- `execucoes.xlsx`: as mesmas execuções em planilha, com uma aba de resumo e uma de legenda;
- `tabelas.md` e os demais CSV: as tabelas agregadas do artigo;
- `fig_tpch.png` e `fig_controlada.png`: as figuras de classificação por fase.

## Reproduzir o experimento

As instruções estão em [`Execução/prototipo/README.md`](Execução/prototipo/README.md). Em resumo, o protótipo usa Docker (PostgreSQL 14), [uv](https://docs.astral.sh/uv/) e [Ollama](https://ollama.com/). A chave da API do modelo pago fica apenas no arquivo `.env`, que não é versionado; o repositório traz só o `.env.example`.

As chamadas ao GPT-4o foram feitas entre 7 e 12 de outubro de 2026 com o identificador `gpt-4o`, que aponta para uma versão datada. A remoção dessas versões da API está prevista para 14 de janeiro de 2027; depois disso, essa parte do experimento não pode ser repetida com o mesmo modelo.
