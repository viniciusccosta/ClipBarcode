
ClipBarcode
===============

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

O **ClipBarcode** é um projeto open source que tem como objetivo oferecer praticidade na leitura de códigos de barras e obtenção da linha digitável. Com o **ClipBarcode**, os usuários podem capturar uma imagem de um código de barras usando um print screen e o programa realizará a leitura do código de barras, fornecendo a linha digitável pronta para copiar e colar.

## Recursos Principais
O **ClipBarcode** oferece os seguintes recursos principais:
- **Leitura de Código de Barras**: Com o **ClipBarcode**, os usuários podem facilmente capturar códigos de barras presentes em boletos de cobrança, guias de impostos, convênios, QR Codes e Notas Fiscais. Basta utilizar o print screen para capturar a imagem e o programa realizará a leitura do código de barras automaticamente. O resultado será a linha digitável pronta para ser utilizada em pagamentos ou outras finalidades.
- **Leitura da Linha Digitável**: Se o código de barras estiver danificado ou for muito pequeno para ser capturado com precisão, o usuário tem a opção de fazer um print diretamente da linha digitável. O **ClipBarcode** será capaz de ler a imagem e extrair os dados necessários. Essa opção oferece flexibilidade em casos onde o código de barras não é legível, garantindo a obtenção da linha digitável de forma confiável.

Com esses recursos, o **ClipBarcode** simplifica o processo de leitura de códigos de barras e linha digitável, permitindo que os usuários realizem pagamentos e preenchimento de dados com facilidade e agilidade.

## Instalação

Para instalar o **ClipBarcode**, siga as etapas abaixo:

1. Baixe os três arquivos necessários:
    1. **clipbarcode_v1.1_win64.exe**
        - https://github.com/viniciusccosta/clipbarcode/releases/download/release/clipbarcode_v1.1_win64.exe
    2. **vcredist_x64.exe**
        - Opção de Download 1: https://aka.ms/highdpimfc2013x64enu
        - Opção de Download 2: https://github.com/viniciusccosta/clipbarcode/releases/download/release/vcredist_x64.exe
    3. **tesseract-ocr-w64-setup-v5.2.0.20220712.exe**
        - Opção de Download 1: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.1.0.20220510.exe
        - Opção de Download 2: https://github.com/viniciusccosta/clipbarcode/releases/download/release/tesseract-ocr-w64-setup-v5.2.0.20220712.exe
2. Salve os três arquivos na mesma pasta no seu computador.
3. Execute o instalador do **ClipBarcode** (arquivo **clipbarcode_v1.1_win64.exe**) e siga as instruções fornecidas.
4. Se a instalação não for bem-sucedida ou ocorrerem problemas durante a execução do programa, siga as etapas adicionais abaixo:
    - Instale o arquivo **vcredist_x64.exe** primeiro, executando-o e seguindo as instruções de instalação.
    - Em seguida, instale o arquivo **tesseract-ocr-w64-setup-v5.2.0.20220712.exe**, executando-o e seguindo as instruções de instalação.
    - Após a instalação bem-sucedida dessas dependências, tente realizar a instalação do **ClipBarcode** novamente, executando o arquivo **clipbarcode_v1.1_win64.exe**.

Certifique-se de ter privilégios de administrador para realizar a instalação e, se necessário, desative temporariamente qualquer software antivírus ou firewall que possa interferir no processo de instalação.

## Como Usar

1. Capture uma imagem do código de barras ou da linha digitável:
    - Utilize o comando `Windows + Shift + S` para selecionar apenas a área desejada da tela.
    - Se preferir, configure a tecla `PrintScreen` para capturar a tela.
        - No Windows 11, acesse Configurações > Acessibilidade > Teclado > Usar o botão PrintScreen para abrir a captura de tela.
    - Verifique se o print contém apenas um código de barras.
    - Ajuste o zoom para obter o código de barras no maior tamanho possível.
2. Abra o **ClipBarcode**.
    - Execute o programa **ClipBarcode** no seu computador.
3. Realize a leitura da imagem:
    - A leitura da imagem será realizada automaticamente assim que o **ClipBarcode** for aberto.
    - Caso o programa já esteja aberto, clique no botão "Ler Print" para iniciar a leitura da imagem capturada.
4. Aguarde o processamento e a leitura do código de barras:
    - Aguarde alguns instantes enquanto o **ClipBarcode** processa a imagem e realiza a leitura do código de barras.
5. Visualize a linha digitável:
    - O **ClipBarcode** exibirá a linha digitável obtida na interface do programa.
    - Copie e cole a linha digitável conforme necessário para realizar pagamentos ou outras finalidades.

## Instruções Adicionais

Aqui estão algumas informações adicionais sobre o **ClipBarcode**:

- **Histórico de Leituras**: O programa salvará todas as capturas de tela localmente no seu computador e fornecerá um histórico para acessar suas leituras anteriores. Isso permite que você tenha acesso fácil às suas capturas anteriores de uma forma conveniente.
- **Contorno Vermelho**: Um contorno vermelho será adicionado ao redor do código de barras lido, facilitando a identificação visual da captura correta da imagem fornecida pelo usuário.
- **Tipo de Leitura**: O programa exibirá na tela o tipo de leitura realizada, identificando se é um QR Code, Boleto, Nota Fiscal ou simplesmente Texto. Isso oferece uma visão clara do tipo de dado que foi extraído da imagem.

Essas informações adicionais fornecem uma visão mais detalhada sobre o funcionamento do **ClipBarcode** e seus recursos, permitindo uma utilização mais completa e eficiente do programa.

## Troubleshooting

Se você encontrar algum problema ao utilizar o **ClipBarcode**, aqui estão algumas soluções comuns para ajudar a resolver possíveis dificuldades:
- **Não realizou a leitura do código de barras**: Caso o programa não consiga ler o código de barras corretamente, tente aumentar o zoom na imagem antes de capturá-la. Ampliar o tamanho do código de barras na imagem pode melhorar a precisão da leitura.
- **Programa não inicia ou fecha inesperadamente**: Se o **ClipBarcode** não estiver iniciando corretamente ou fechando de forma inesperada, certifique-se de ter instalado os seguintes arquivos de dependência: **vcredist_x64.exe** e **tesseract-ocr-w64-setup-v5.2.0.20220712.exe**.

## Possíveis Atualizações

Abaixo estão algumas possíveis atualizações que podem ser implementadas no futuro:
- **Descrição Personalizada**: Adicionar a capacidade para os usuários inserirem uma descrição personalizada para cada leitura. Isso permitirá que os usuários identifiquem e rotulem facilmente cada leitura para referência posterior.
- **Atualização Automática**: Implementar um sistema de atualização automática para garantir que os usuários sempre tenham acesso às últimas melhorias e correções de bugs. O programa fará o download e instalará automaticamente as atualizações disponíveis, proporcionando uma experiência contínua e atualizada.
- **Leitura Automática**: Adicionar a funcionalidade de leitura automática caso o **ClipBarcode** já esteja aberto. Isso permitirá que os usuários capturem uma imagem do código de barras ou linha digitável e a leitura seja realizada automaticamente, sem a necessidade de clicar no botão "Ler Print".

Essas são apenas algumas sugestões de possíveis atualizações. O projeto está aberto a contribuições da comunidade, e novas ideias e recursos podem ser adicionados no futuro para melhorar ainda mais a funcionalidade e usabilidade do **ClipBarcode**.

## Contribuição

O **ClipBarcode** é um projeto open source e recebe contribuições da comunidade. Caso você queira contribuir, siga os passos abaixo:
- Faça um fork do repositório do **ClipBarcode**.
- Implemente as alterações desejadas ou corrija bugs.
- Faça um pull request para enviar suas alterações.
- Aguarde a análise e a revisão da sua contribuição pela equipe responsável.

## Licença

O **ClipBarcode** é distribuído sob a licença MIT. Para mais detalhes, consulte o arquivo LICENSE.
