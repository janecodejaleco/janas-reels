# JANAS BTC — Reels animados regionais, episódio piloto

**5 vídeos completos originais, um para cada região: Brasil, América Latina, mundo anglófono, Rússia/CIS e Israel.** Cada vídeo tem 6 cenas de até 8 segundos (total ~48s) e narração no idioma local, além de legendas gráficas já incluídas. Também exporta os 30 clipes individuais para edição no CapCut.

## Distinção importante

Esta versão emprega **motion graphics 2.5D procedural** (elementos desenhados e animados em Python/Pillow + FFmpeg). **Não é vídeo generativo de IA no sentido de Runway/Kling/Veo**. As animações usam movimentos de câmera simulados, partículas, geometrias, gráficos, cofres, mapas conceituais e documentos **ilustrativos** para contar histórias. O objetivo é ser reproduzível sem API paga nem créditos de vídeo. IA de vídeo não é executada neste workflow.

## Como executar

No GitHub: `Actions → JANAS BTC | 5 Reels cinematicos (6x8 segundos) → Run workflow`. O arquivo `.github/workflows/reels-cinematicos.yml` também executa automaticamente quando criado ou editado. São necessários GitHub Actions em repositório público e acesso online do Edge TTS, que é serviço de terceiros sem SLA.

Abra a execução, depois **Artifacts → janas-cinematicos-5-reels-N**. Baixe e extraia o ZIP (no celular use Files/Gerenciador de Arquivos). Na raiz estão os cinco arquivos `JANAS_BTC_REEL_01_PT.mp4`, `_ES`, `_EN`, `_RU`, `_HE`. Pastas por idioma têm seis clipes `clip_01.mp4` ... `clip_06.mp4` para CapCut. A retenção dos arquivos é de 7 dias.

## Fontes e integridade editorial

O vídeo em hebraico usa como base a **Operação Trapiche**, da Polícia Federal brasileira, novembro de 2023, e a cobertura da **Reuters** da investigação de possível conexão com Hezbollah e da alegação israelense de cooperação do Mossad. Não afirmar como fato nenhuma ligação de políticos brasileiros à lavagem de dinheiro. O documento exibido na tela é **uma ilustração gráfica**, não um registro policial autêntico. Referências para checagem:
- https://www.gov.br/pf/pt-br/assuntos/noticias/2023/11/pf-deflagra-operacao-para-investigar-atos-preparatorios-de-terrorismo-no-brasil
- https://www.reuters.com/world/americas/brazil-police-arrest-two-people-suspected-planning-terrorist-attacks-2023-11-08/

## Custos e limites

O repositório público pode executar GitHub Actions em runners padrão sem tarifa de minutos sob as regras correntes, mas armazenamento e tempo de máquina são recursos sujeitos a políticas e mudanças. O projeto usa Edge TTS, API de voz online não oficial; a geração pode falhar se ficar indisponível. Os vídeos não são publicados automaticamente no Instagram. O workflow é sob demanda, sem trocar ou interromper o calendário diário de aulas existente.