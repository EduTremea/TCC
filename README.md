## INSTALAÇÃO LOCAL

#### Parte 1: Baixando pacotes TeX Live
<img src="https://skillicons.dev/icons?i=ubuntu" /> **Ubuntu Linux**

 - [Baixar e extrair o ZIP do projeto no Overleaf](https://www.overleaf.com/learn/how-to/Exporting_your_work_from_Overleaf#Downloading_your_current_project_as_a_.zip_file)

 - No terminal (baixar pacotes do TeX Live):
       sudo apt update
       sudo apt install -y texlive-latex-recommended texlive-latex-extra texlive-lang-portuguese texlive-fonts-extra texlive-bibtex-extra biber latexmk

<img src="https://skillicons.dev/icons?i=windows" /> **Windows 10/11**

- [Baixar o instalador do TeX Live](https://mirror.ctan.org/systems/texlive/tlnet/install-tl-windows.exe)
- A instalação completa inclui diversos pacotes resultando na necessidade de cerca de 10GB de espaço em disco
- Na tela do "Instalador TeX Live" desmarcar o item: 'Instalar editor TeXworks'

#### Parte 2: Configurando VSCode
 - Editando no VSCode (>= 1.96.0):
    - Instalar a extensão [Latex Language Support](https://marketplace.visualstudio.com/items?itemName=torn4dom4n.latex-support)
    - Instalar a extensão [LaTex Workshop (Autor: James Yu)](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop)
    - Carregar a pasta do projeto
	- Use a barra lateral contendo os comandos presentes na extensão:	
	<img src="https://vkuhlmann.com/assets/files/VisualStudioCodeDemo-44dc77498e90e4586d28d7caf1c9547d.png" width="90%"/>




