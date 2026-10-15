# JANAS BTC — 5 Reels por dia, sem Gemini, sem IA paga

Este é um gerador **faceless** com 30 aulas originais pré-escritas em **cinco idiomas** (PT-BR, espanhol latino-americano, inglês, russo e hebraico). Total: **150 roteiros completos**, cada um com cinco cenas. Roteiros e traduções foram preparados antecipadamente no ChatGPT; no momento da geração não existe chamada ao Gemini, ChatGPT API ou outro modelo pago.

**O que a automação realmente faz:** todos os dias o GitHub Actions escolhe uma aula, sintetiza cinco narrações com Edge TTS, renderiza artes gráficas e transições simples com Python/Pillow/FFmpeg, incorpora legendas, e entrega **cinco vídeos MP4 verticais de 720 × 1280**, mais as legendas do Instagram. O tempo dos vídeos depende das vozes. São slides visuais animados, não vídeo generativo cinematográfico.

**O que não faz:** não pesquisa notícias novas, não cria novos roteiros depois das 30 aulas, não publica automaticamente no Instagram, não clona sua voz e não é um serviço 100% offline. A série **repete após 30 dias** até receber novos roteiros. Edge TTS é um serviço online usado por biblioteca não oficial, gratuito no contexto deste projeto, mas disponibilidade, limites e condições podem mudar.

## Passos para ativar (sem API key, sem cadastro de cartão)

1. Crie uma conta em https://github.com se ainda não tiver.
2. Crie **um repositório público** chamado, por exemplo, `janas-reels`. A execução em runners padrão de repositórios públicos é gratuita dentro das regras vigentes do GitHub. **Não envie material privado ao repositório.**
3. Extraia o arquivo ZIP. Envie **todos os arquivos da pasta** para a raiz do repositório, **preservando a pasta oculta `.github/workflows/reels-diarios.yml`**. O GitHub Desktop ajuda a enviar a pasta inteira sem perder a estrutura.
4. Na guia **Actions** do GitHub, aceite habilitar workflows se for solicitado e escolha `JANAS BTC | Cinco Reels diarios (sem IA paga)`.
5. Clique em **Run workflow**. Para testar a aula 1, coloque `dia = 1`. Depois, os demais dias podem ficar automáticos (`dia = 0`).
6. Quando a execução terminar, abra o job e baixe o arquivo **Artifacts → janabtc-reels-NÚMERO**. Ele contém os cinco MP4, um arquivo com as legendas para publicar e `roteiros.json` com os textos utilizados.

O agendamento é **todos os dias às 09h17 no fuso America/Sao_Paulo**. Esse horário é aproximado: execuções agendadas podem atrasar ou ser ignoradas em períodos de alta demanda. Os artefatos ficam disponíveis por **três dias**; baixe-os regularmente.

## Configuração de data

O arquivo `.github/workflows/reels-diarios.yml` contém:

```yaml
DATA_INICIO: '2026-10-16'
```

A partir de 16 de outubro de 2026 a automação começa pela aula 1. Se criar a conta mais tarde, substitua essa data **pela data em que quer começar a série**, para não pular aulas. Para gerar uma aula específica manualmente, use o campo `dia` do botão `Run workflow` e insira um número de 1 a 30.

## Estrutura do pacote

- `roteiros_30_dias.txt`: os 150 roteiros editáveis. Cada linha tem dia, idioma, título, cinco cenas separadas por `~`. **Não remova os cinco idiomas de nenhum dia.**
- `gerar_reels.py`: gerador, montagem e legendas sincronizadas.
- `.github/workflows/reels-diarios.yml`: agenda do GitHub, configuração de dependências e entrega dos MP4.
- `requirements.txt`: duas bibliotecas Python.
- `previa_pt.png` e `previa_he.png`: imagens de prévia do visual, sem gerar uma voz real.

## Testes no computador (opcional)

Requer Python 3.11+, FFmpeg com `libass` e `libx264`, e fontes Noto:

```bash
python -m pip install -r requirements.txt
python gerar_reels.py --validate
python gerar_reels.py --day 1 --only pt
```

Para testar sem acessar o serviço de voz e renderizar apenas uma cena silenciosa:

```bash
python gerar_reels.py --day 1 --only pt --scenes 1 --fake-tts
```

**Não publique um MP4 gerado com `--fake-tts`: ele não possui narração real.**

## Segurança e qualidade

- Sem chaves de API e sem billing de IA. **Nunca é necessário ativar pagamento do Gemini ou da OpenAI.**
- Execuções em repositórios públicos usam máquinas padrão gratuitas, mas os artefatos consomem armazenamento sujeito a limites. Repositórios privados seguem outra política de cotas e potencial cobrança.
- A voz vem de um serviço online de terceiros. Se o serviço ficar indisponível, a execução pode falhar. Não há garantia de funcionamento ilimitado ou perpétuo.
- Você deve revisar pronúncia, hebraico, russo e conteúdos antes de publicar. São roteiros educativos gerais, sem aconselhamento financeiro personalizado.
- O vídeo usa apenas elementos geométricos gerados pelo próprio script. A ilustração da rede não representa preços reais.
- Os agendamentos de repositórios públicos podem ser desativados após 60 dias sem atividade no repositório.
- Para conectar publicação automática ao Instagram, é necessário configurar posteriormente um serviço de agendamento ou a API oficial da Meta; **não está incluído nesta versão**.

## Fonte das aulas

Os 30 dias abordam: natureza do Bitcoin, limite de emissão, mineração, prova de trabalho, chaves privadas, frase de recuperação, carteiras, corretoras, confirmações, taxas, mempool, Lightning, UTXO, nós completos, halving, preço e escassez, volatilidade, stablecoins, USDC, golpes, phishing, dois fatores, redes e endereços, estornos, blockchain pública, pseudonimato, compras periódicas, ataque de 51%, código aberto e primeiro envio seguro.