# Projeto TCC

Este repositório reúne o material do trabalho de conclusão de curso sobre reescrita de consultas SQL com modelos de linguagem.

## Como usar

### 1. Instalação local do TeX

#### Ubuntu / Debian

1. Baixe o ZIP do projeto no Overleaf, se estiver usando um arquivo exportado.
2. No terminal, instale o TeX Live e ferramentas relacionadas:

```bash
sudo apt update
sudo apt install -y texlive-latex-recommended texlive-latex-extra texlive-lang-portuguese texlive-fonts-extra texlive-bibtex-extra biber latexmk
```

#### Windows

1. Baixe o instalador do TeX Live:
   https://mirror.ctan.org/systems/texlive/tlnet/install-tl-windows.exe
2. A instalação completa exige bastante espaço em disco, em torno de 10 GB.
3. Se quiser, desmarque o componente "TeXworks" durante a instalação.

### 2. Editando no VS Code

Se você usa VS Code, instale duas extensões úteis para LaTeX:

- LaTeX Workshop (James Yu)
- Latex Language Support

Em seguida, abra a pasta do projeto no VS Code e use os comandos da extensão para compilar o documento.

## Observações

- O arquivo principal é `sbc-template.tex`.
- A pasta `sty/` contém estilos usados pelo documento.
- Este README foi ajustado para ficar mais direto e mais fácil de usar.




