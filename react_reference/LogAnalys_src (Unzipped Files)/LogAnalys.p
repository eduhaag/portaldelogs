/************************************************************************************************
** Analisador de Logs
**
** Analisa logs do JBoss, Progress Appserver, Progress Client, Fluig, Logix e Profiler Progress
**
** 26/08/2016 - Menna - Criado o programa
** 02/09/2016 - Menna - Adicionado filtro de data e hora
** 05/09/2016 - Menna - Adicionado botao Fix com informacoes para corrigir alguns problemas
** 06/09/2016 - Menna - Adicionado botao Info com informacoes do sistema
** 12/09/2016 - Menna - Adicionado Progress Performance e Tomcat
** 28/09/2016 - Menna - Adicionado o Profiler Progress e Acesso Jboss e Tomcat
** 05/10/2016 - Menna - Adicionado o Appserver Broker e Fluig
** 12/10/2016 - Menna - Adicionado o Progress memory Leak
** 18/10/2016 - Menna - Arrumado logica de leitura de Fix
** 20/10/2016 - Menna - Arrumado logica de leitura de logs volumosa, pois estava dando erro
** 01/11/2016 - Menna - Adicionado clear log e recebimento de parametros para carga
** 02/12/2016 - Menna - Adicionado o webspeed
** 02/05/2017 - Menna - Adicionado o tabanalys
** 29/04/2022 - Menna - Adicionado o XREF
************************************************************************************************/

/*
TODO
- Error - qualquer erro de aparecer no log (todos)
- Not Connect - quando algum banco nao esta conectado (progress)
- AssertionConsumerServlet - quando o ambiente datasul redireciona para ambiente:8480/datasul/ACS (jboss)
- FLUIG_SYNC - Sincronizacao com o fluig. (Jboss)
- **CRC - Erro de CRC. (progress)
- [com.totvs.license] - Informacoes do license. (jboss)
- deployment failed - Quando ocorre erro ao fazer o deploy antes de iniciar o ambiente. (Jboss)

4GLMessages,4GLTrace,4GLTrans,DB.Connects,DS.QryInfo,DS.Cursor,DynObjects.DB,DynObjects.XML,DynObjects.Other,DynObjects.UI,FileID,ProEvents.UI.Char,ProEvents.UI.Command,ProEvents.Other,QryInfo,SAX
ASPlumbing - appserver performance
*/

CREATE WIDGET-POOL.

DEFINE STREAM sImp.
DEFINE STREAM sDad.

FUNCTION getListType    RETURNS CHARACTER () FORWARD.
FUNCTION getListCateg   RETURNS CHARACTER (INPUT cType AS CHARACTER) FORWARD.
FUNCTION createTTInfo   RETURNS CHARACTER (INPUT cKey AS CHARACTER, INPUT cValue AS CHARACTER) FORWARD.
FUNCTION createTTDetail RETURNS CHARACTER (INPUT cLin AS CHARACTER, INPUT iLin AS INTEGER, INPUT iSeq AS INTEGER) FORWARD.
FUNCTION checkInfo      RETURNS CHARACTER (INPUT cLin AS CHARACTER, INPUT toFind1 AS CHARACTER, INPUT toFind2 AS CHARACTER, INPUT cTxt AS CHARACTER) FORWARD.
FUNCTION getDifTime     RETURNS INTEGER   (INPUT t1 AS CHARACTER, INPUT t2 AS CHARACTER) FORWARD.
FUNCTION getProp        RETURNS CHARACTER (INPUT cKey AS CHARACTER) FORWARD.
FUNCTION setProp        RETURNS CHARACTER (INPUT cKey AS CHARACTER, INPUT cVal AS CHARACTER) FORWARD.

DEFINE VARIABLE cArq        AS CHARACTER   NO-UNDO FORMAT "x(255)" LABEL "Arquivo"
                               VIEW-AS EDITOR SIZE 100 BY 1.
DEFINE VARIABLE cArqCfg     AS CHARACTER   NO-UNDO.
DEFINE VARIABLE cDir        AS CHARACTER   NO-UNDO.
DEFINE VARIABLE cbCatLst    AS CHARACTER   NO-UNDO FORMAT "x(20)" LABEL "Categoria"
                               VIEW-AS COMBO-BOX INNER-LINES 10.
DEFINE VARIABLE cbTypeLst   AS CHARACTER   NO-UNDO FORMAT "x(15)" LABEL "Tipos"
                               VIEW-AS COMBO-BOX INNER-LINES 10.
DEFINE VARIABLE cDados      AS CHARACTER   NO-UNDO LABEL "Detalhes"
                               VIEW-AS EDITOR SIZE 155 BY 8 SCROLLBAR-VERTICAL SCROLLBAR-HORIZONTAL.
DEFINE VARIABLE cInfo       AS CHARACTER   NO-UNDO LABEL "Informacoes"
                               VIEW-AS EDITOR SIZE 80 BY 10 SCROLLBAR-VERTICAL SCROLLBAR-HORIZONTAL FONT 2.
DEFINE VARIABLE cbTipLog    AS CHARACTER   NO-UNDO FORMAT "x(37)" LABEL "Tipo Log" INITIAL "jb"
                               VIEW-AS COMBO-BOX INNER-LINES 18 SIZE 40 BY 1
                                    LIST-ITEM-PAIRS "JBoss","jb",
                                                    "TomCat","tc",
                                                    "Acesso JBoss/Tomcat","ac",
                                                    "Fluig","fl",
                                                    "Progress Client","pgCli",
                                                    "Progress Profiler","pgProf",
                                                    "Progress Limpa Log","pgClear",
                                                    "Progress Memory","pgMem",
                                                    "Progress Tabanalys","pgTab",
                                                    "Progress Database","pgDb",
                                                    "Progress XREF","pgXref",
                                                    "Appserver Progress","app",
                                                    "Appserver Limpa Log","appClear",
                                                    "Appserver Performance","appPerf",
                                                    "Appserver Broker","appBk",
                                                    "WebSpeed Progress","web",
                                                    "WebSpeed Limpa Log","webClear",
                                                    "Logix com SQL","lxSql",
                                                    "Logix sem SQL","lx".
DEFINE VARIABLE cbFilter    AS CHARACTER   NO-UNDO FORMAT "x(10)" LABEL "Filtro"
                               VIEW-AS COMBO-BOX INNER-LINES 10.
DEFINE VARIABLE cFilter     AS CHARACTER   FORMAT "x(256)" NO-UNDO LABEL "Filtro"
                               VIEW-AS FILL-IN SIZE 50 BY 1.

DEFINE VARIABLE dDatIni     AS DATE      FORMAT "99/99/9999" NO-UNDO LABEL "Data" INITIAL 01/01/1800.
DEFINE VARIABLE dDatFim     AS DATE      FORMAT "99/99/9999" NO-UNDO LABEL "a"    INITIAL 12/31/9999.
DEFINE VARIABLE cHorIni     AS CHARACTER FORMAT "99:99:99"   NO-UNDO LABEL "Hora" INITIAL "000000".
DEFINE VARIABLE cHorFim     AS CHARACTER FORMAT "99:99:99"   NO-UNDO LABEL "a"    INITIAL "999999".

DEFINE VARIABLE cLimp        AS CHARACTER     NO-UNDO.
DEFINE VARIABLE cLin         AS CHARACTER     NO-UNDO.
DEFINE VARIABLE cLin2        AS CHARACTER     NO-UNDO.
DEFINE VARIABLE cLin3        AS CHARACTER     NO-UNDO.
DEFINE VARIABLE cAno         AS CHARACTER     NO-UNDO.
DEFINE VARIABLE cAnoA        AS CHARACTER     NO-UNDO.
DEFINE VARIABLE wh-jan       AS WIDGET-HANDLE NO-UNDO.
DEFINE VARIABLE cLogixType   AS CHARACTER     NO-UNDO.
DEFINE VARIABLE lDetail      AS LOGICAL       NO-UNDO.
DEFINE VARIABLE lNoQuit      AS LOGICAL       NO-UNDO.
DEFINE VARIABLE hFrame       AS HANDLE        NO-UNDO.
DEFINE VARIABLE hDados       AS HANDLE        NO-UNDO.
DEFINE VARIABLE hBrw         AS HANDLE        NO-UNDO.
DEFINE VARIABLE hDet         AS HANDLE        NO-UNDO.
DEFINE VARIABLE cParam       AS CHARACTER     NO-UNDO.

DEFINE BUTTON btArq      LABEL "...".
DEFINE BUTTON btProc     LABEL "&Processar".
DEFINE BUTTON btExit     LABEL "&Sair"      AUTO-ENDKEY.
DEFINE BUTTON btClip     LABEL "&Clipboard".
DEFINE BUTTON btNotepad  LABEL "&Notepad".
DEFINE BUTTON btPrint    LABEL "&Imprimir Browse".
DEFINE BUTTON btCorrigir LABEL "I&dentificar Problemas".
DEFINE BUTTON btInfo     LABEL "Informacoes do &Ambiente".
DEFINE BUTTON btFilter   LABEL "&Filtrar" SIZE 10 BY 1.
DEFINE BUTTON btClear    LABEL "&Limpar"  SIZE 8  BY 1.

DEFINE TEMP-TABLE ttCat NO-UNDO
    FIELD tcCate AS CHARACTER
    FIELD tcType AS CHARACTER
    INDEX categ  IS PRIMARY tcCate
    INDEX tipo   tcType.

DEFINE TEMP-TABLE ttFix NO-UNDO
    FIELD tcError AS CHARACTER
    FIELD tcToDo  AS CHARACTER
    FIELD tcLinh  AS CHARACTER
    FIELD tiLinh  AS INTEGER
    INDEX codigo IS PRIMARY tiLinh tcError.

DEFINE TEMP-TABLE ttInfo NO-UNDO
    FIELD tcProp  AS CHARACTER
    FIELD tcValue AS CHARACTER
    FIELD tiLinh  AS INTEGER
    INDEX codigo IS PRIMARY tiLinh tcProp.

DEFINE TEMP-TABLE ttLin NO-UNDO
    FIELD tcLinh  AS CHARACTER
    FIELD tiLinh  AS INTEGER
    FIELD tcProc  AS CHARACTER
    FIELD tcData  AS CHARACTER
    FIELD tcCate  AS CHARACTER
    INDEX codigo IS PRIMARY tiLinh
    INDEX tcProc     tcProc tcData tiLinh.

DEFINE TEMP-TABLE ttProp NO-UNDO
    FIELD tcKey   AS CHARACTER
    FIELD tcVal   AS CHARACTER
    INDEX codigo IS PRIMARY tcKey.

DEFINE TEMP-TABLE ttDetail NO-UNDO
    FIELD tiLinh  AS INTEGER
    FIELD tiSeq   AS INTEGER LABEL "Pagina"
    FIELD tcLinh  AS CHARACTER
    INDEX codigo IS PRIMARY tiLinh tiSeq.

CREATE WINDOW wh-jan
    ASSIGN ROW          = 1
           COL          = 7
           WIDTH-CHARS  = 178
           HEIGHT-CHARS = 30
           TITLE        = "Log Analys"
           MESSAGE-AREA = YES.

ASSIGN current-window = wh-jan
       cAno           = STRING(YEAR(TODAY), "9999")
       cAnoA          = STRING(YEAR(TODAY) - 1, "9999")
       cArqCfg        = SESSION:TEMP-DIRECTORY + "LogAnalys.cfg".

DEFINE FRAME f-main
    cbTipLog   AT ROW 01.5 COL 10 COLON-ALIGNED SPACE(0)
    cArq       NO-LABELS SPACE(0)
    btArq      btProc btExit
    WITH SIDE-LABELS THREE-D SIZE 178 BY 2
       DROP-TARGET.
STATUS INPUT "Analisador de Logs v1.3 By Menna".

ASSIGN CURRENT-WINDOW:MAX-HEIGHT   = ?
       CURRENT-WINDOW:MAX-WIDTH    = ?
       CURRENT-WINDOW:WINDOW-STATE = WINDOW-NORMAL.

ON  WINDOW-RESIZED OF CURRENT-WINDOW DO:
    DEFINE VARIABLE hObj    AS HANDLE  NO-UNDO.
    DEFINE VARIABLE hTmp    AS HANDLE  NO-UNDO.
    DEFINE VARIABLE hBrwO   AS HANDLE  NO-UNDO.
    DEFINE VARIABLE hCol    AS HANDLE  NO-UNDO.
    DEFINE VARIABLE deTam   AS DECIMAL NO-UNDO.
    DEFINE VARIABLE deDifW  AS DECIMAL NO-UNDO.
    DEFINE VARIABLE deDifH  AS DECIMAL NO-UNDO.
    DEFINE VARIABLE lWinMax AS LOGICAL NO-UNDO.

    /* guarda a diferenca de tamanho da tela */
    ASSIGN deDifW = CURRENT-WINDOW:WIDTH-CHARS  - FRAME f-main:WIDTH-CHARS.
    ASSIGN deDifH = CURRENT-WINDOW:HEIGHT-CHARS - FRAME f-main:height-CHARS.

    IF  VALID-HANDLE(hDet)  = TRUE THEN
        ASSIGN hDet:VISIBLE = FALSE
               hDet:ROW     = 1.

    /* ajusta o tamanho da frame f-main */
    ASSIGN FRAME f-main:WIDTH-CHARS         = CURRENT-WINDOW:WIDTH-CHARS
           FRAME f-main:virtual-width-chars = CURRENT-WINDOW:WIDTH-CHARS.

    /* ajusta o tamanho da frame filha */
    IF  VALID-HANDLE(hFrame) = TRUE THEN DO:
        ASSIGN hFrame:WIDTH-CHARS          = CURRENT-WINDOW:WIDTH-CHARS
               hFrame:VIRTUAL-WIDTH-CHARS  = CURRENT-WINDOW:WIDTH-CHARS
               hFrame:HEIGHT-CHARS         = CURRENT-WINDOW:HEIGHT-CHARS - FRAME f-main:height-chars
               hFrame:VIRTUAL-HEIGHT-CHARS = CURRENT-WINDOW:HEIGHT-CHARS - FRAME f-main:height-chars.

        /* ajusta a posicao dos objetos */
        ASSIGN hObj = hFrame:FIRST-CHILD.
        DO  WHILE VALID-HANDLE(hObj):
            IF  hObj:TYPE = "Field-Group" THEN DO:
                ASSIGN hTmp = hObj:FIRST-CHILD.
                DO  WHILE VALID-HANDLE(hTmp):
                    IF  hTmp:TYPE = "RECTANGLE" THEN
                        ASSIGN hTmp:WIDTH-CHARS = hTmp:WIDTH-CHARS + deDifW.
                    IF  hTmp:TYPE = "EDITOR" AND hTmp:NAME = "cDados" THEN
                        ASSIGN hTmp:WIDTH-CHARS = hTmp:WIDTH-CHARS + deDifW.
                    IF  hTmp:TYPE = "BROWSE" AND hTmp:NAME <> "bDetail" THEN DO:
                        ASSIGN hTmp:WIDTH-CHARS = hTmp:WIDTH-CHARS + deDifW.
                        ASSIGN hBrwO = hTmp:FIRST-COLUMN.
                        DO  WHILE VALID-HANDLE(hBrwO):
                            IF  hBrwO:NAME = "tcLinh"
                            OR  hBrwO:NAME = "tcComm" THEN
                                ASSIGN hCol = hBrwO.
                            ELSE
                                ASSIGN deTam = deTam + hBrwO:WIDTH-CHARS.
                           ASSIGN hBrwO = hBrwO:NEXT-COLUMN No-error.
                        END.
                        IF  VALID-HANDLE(hCol) = TRUE THEN
                            ASSIGN hCol:WIDTH-CHARS = hCol:WIDTH-CHARS + deTam + deDifW - 20.
                    END.
                    IF  hTmp:TYPE = "BUTTON" THEN DO:
                        /* nao movimentara os botoes de correcao e informacooes
                        IF  hTmp:name = "btCorrigir"
                        OR  hTmp:name = "btInfo" THEN
                             ASSIGN hTmp:col = hTmp:col + deDifW.
                        */
                        IF  hTmp:NAME = "btClip"
                        OR  hTmp:NAME = "btPrint"
                        OR  hTmp:NAME = "btNotepad"
                        OR  hTmp:NAME = "btExit" THEN
                            ASSIGN hTmp:ROW = hFrame:height - .5.
                        
                        IF  VALID-HANDLE(hDados) = TRUE THEN
                            ASSIGN hDados:ROW = hTmp:ROW - hDados:HEIGHT-CHARS no-error.
                    END.
                    ASSIGN hTmp = hTmp:NEXT-SIBLING.
                END.
            END.
            ASSIGN hObj = hObj:NEXT-SIBLING.
        END.
        IF  VALID-HANDLE(hBrw)   = TRUE 
        AND VALID-HANDLE(hDados) = TRUE THEN
            ASSIGN hBrw:height = hFrame:height - hDados:height - 5.5.
        ELSE DO:
            IF  VALID-HANDLE(hBrw)   = TRUE THEN 
                ASSIGN hBrw:height = hFrame:height - 5.5.
        END.
        
        IF  VALID-HANDLE(hDet)   = TRUE
        AND VALID-HANDLE(hDados) = TRUE THEN
            ASSIGN hDet:ROW     = hDados:ROW
                   hDet:VISIBLE = TRUE.
    END.
END.

ON  WINDOW-CLOSE, ENDKEY OF CURRENT-WINDOW
    APPLY "CHOOSE" TO btExit IN FRAME f-main.

ON  DROP-FILE-NOTIFY OF FRAME f-main DO:
    DEFINE VARIABLE ix   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cTmp AS CHARACTER NO-UNDO.

    DO  ix = 1 TO FRAME f-main:NUM-DROPPED-FILES:
        ASSIGN cTmp = FRAME f-main:GET-DROPPED-FILE(ix).
        FILE-INFO:FILE-NAME = cTmp.
        IF  INDEX(FILE-INFO:FILE-TYPE, 'F') > 0  THEN DO:
            cArq:screen-value = cTmp.
            LEAVE.
        END.
    END.
    FRAME f-main:END-FILE-DROP().
END.

ON  CHOOSE OF btArq DO:
    ASSIGN cArq.
    DEFINE VARIABLE lResp AS LOG NO-UNDO.
    SYSTEM-DIALOG GET-FILE cArq
        TITLE "Selecione o arquivo de log"
        FILTERS "*.log" "*.log",
                "*.txt" "*.txt",
                "*.*" "*.*"
        MUST-EXIST
        INITIAL-DIR cArq
        USE-FILENAME
        UPDATE lResp.

    DISPLAY cArq WITH FRAME f-main.
END.

ON  CHOOSE OF btProc DO:
    ASSIGN cbTipLog cArq.

    IF  cbTipLog <> "pgProf" THEN DO:
        FILE-INFO:FILE-NAME = cArq.
        IF  FILE-INFO:PATHNAME = ? THEN DO:
            MESSAGE "O arquivo de log " cArq "nao foi encontrado!"
                    VIEW-AS ALERT-BOX ERROR.
            RETURN NO-APPLY.
        END.
    END.

    ASSIGN CURRENT-WINDOW:WINDOW-STATE = WINDOW-NORMAL.
    APPLY "Window-resized" TO CURRENT-WINDOW.

    /* faz a carga inicial de todas as propriedades */
    IF  getProp("ArquivoProgs")         = "" THEN setProp("ArquivoProgs",         "").
    IF  getProp("ArquivoProgsMem")      = "" THEN setProp("ArquivoProgsMem",      "").
    IF  getProp("ArquivoProgsProfiler") = "" THEN setProp("ArquivoProgsProfiler", "").
    IF  getProp("ArquivoProgsClear")    = "" THEN setProp("ArquivoProgsClear",    "").
    IF  getProp("ArquivoProgsTab")      = "" THEN setProp("ArquivoProgsTab",      "").
    IF  getProp("ArquivoProgsDb")       = "" THEN setProp("ArquivoProgsDb",       "").
    IF  getProp("ArquivoProgsXref")     = "" THEN setProp("ArquivoProgsXref",     "").
    IF  getProp("ArquivoApp")           = "" THEN setProp("ArquivoApp",           "").
    IF  getProp("ArquivoAppPerf")       = "" THEN setProp("ArquivoAppPerf",       "").
    IF  getProp("ArquivoAppBroker")     = "" THEN setProp("ArquivoAppBroker",     "").
    IF  getProp("ArquivoAppClear")      = "" THEN setProp("ArquivoAppClear",      "").
    IF  getProp("ArquivoJboss")         = "" THEN setProp("ArquivoJboss",         "").
    IF  getProp("ArquivoTomcat")        = "" THEN setProp("ArquivoTomcat",        "").
    IF  getProp("ArquivoLogixSQL")      = "" THEN setProp("ArquivoLogixSQL",      "").
    IF  getProp("ArquivoLogix")         = "" THEN setProp("ArquivoLogix",         "").
    IF  getProp("ArquivoAcesso")        = "" THEN setProp("ArquivoAcesso",        "").
    IF  getProp("ArquivoFluig")         = "" THEN setProp("ArquivoFluig",         "").
    IF  getProp("ArquivoWeb")           = "" THEN setProp("ArquivoWeb",           "").
    IF  getProp("ArquivoWebClear")      = "" THEN setProp("ArquivoWebClear",      "").

    CASE cbTipLog:
        WHEN "pgCli"    THEN setProp("ArquivoProgs",      cArq).
        WHEN "pgMem"    THEN setProp("ArquivoProgsMem",   cArq).
        /* WHEN "pgProf" THEN setProp("ArquivoProgsProfiler", cArq). nao pode ser gravado aqui  */
        WHEN "pgClear"  THEN setProp("ArquivoProgsClear", cArq).
        WHEN "pgTab"    THEN setProp("ArquivoProgsTab",   cArq).
        WHEN "pgDb"     THEN setProp("ArquivoProgsDb",    cArq).
        WHEN "pgXref"   THEN setProp("ArquivoProgsXref",  cArq).
        WHEN "app"      THEN setProp("ArquivoApp",        cArq).
        WHEN "appPerf"  THEN setProp("ArquivoAppPerf",    cArq).
        WHEN "appBk"    THEN setProp("ArquivoAppBroker",  cArq).
        WHEN "appClear" THEN setProp("ArquivoAppClear",   cArq).
        WHEN "web"      THEN setProp("ArquivoWeb",        cArq).
        WHEN "webClear" THEN setProp("ArquivoWebClear",   cArq).
        WHEN "jb"       THEN setProp("ArquivoJboss",      cArq).
        WHEN "tc"       THEN setProp("ArquivoTomcat",     cArq).
        WHEN "lxSQL"    THEN setProp("ArquivoLogixSQL",   cArq).
        WHEN "lx"       THEN setProp("ArquivoLogix",      cArq).
        WHEN "ac"       THEN setProp("ArquivoAcesso",     cArq).
        WHEN "fl"       THEN setProp("ArquivoFluig",      cArq).
    END.

    setProp("tipoLog", cbTipLog).

    RUN saveProp.

    IF  cbTipLog <> "pgProf" THEN DO:
        ASSIGN cArq       = REPLACE(cArq, "~\", "/")
               cDir       = cArq
               ENTRY(NUM-ENTRIES(cDir,"/"), cDir, "/") = ""
               cArq       = ENTRY(NUM-ENTRIES(cArq, "/"), cArq, "/")
               cInfo      = ""
               cLogixType = "".
    END.

    DISABLE ALL WITH FRAME f-main.

    IF  cbTipLog = "lxSQL" THEN
        ASSIGN cLogixType = "SQL".

    CASE cbTipLog:
        WHEN "jb"       THEN RUN logJboss         (cDir, cArq).
        WHEN "tc"       THEN RUN logTomcat        (cDir, cArq).
        WHEN "pgCli"    OR
        WHEN "app"      OR
        WHEN "web"      THEN RUN logProgs         (cDir, cArq).
        WHEN "pgProf"   THEN RUN logProgsProfiler.
        WHEN "pgTab"    THEN RUN logProgsTab      (cDir, cArq).
        WHEN "pgDb"     THEN RUN logProgsDb       (cDir, cArq).
        WHEN "pgXref"   THEN RUN logProgsXref     (cDir, cArq).
        WHEN "pgClear"  OR
        WHEN "appClear" OR
        WHEN "webClear" THEN RUN logClear         (cDir, cArq).
        WHEN "appPerf"  THEN RUN logAppPerf       (cDir, cArq).
        WHEN "appBk"    THEN RUN logAppBroker     (cDir, cArq).
        WHEN "pgMem"    THEN RUN logProgsMem      (cDir, cArq).
        WHEN "lxSQL"    OR
        WHEN "lx"       THEN RUN logLogix         (cDir, cArq).
        WHEN "ac"       THEN RUN logAcesso        (cDir, cArq).
        WHEN "fl"       THEN RUN logFluig         (cDir, cArq).
    END CASE.

    ENABLE ALL WITH FRAME f-main.

    APPLY "Entry" TO FRAME f-main.

    RUN showMessage("Dica: Escolha o tipo de log, arraste o arquivo de log para o campo de arquivo e clique em 'Processar'").

    APPLY "value-changed" TO cbTipLog.
END.

ON  VALUE-CHANGED OF cbTipLog DO:
    ASSIGN cbTipLog.

    ASSIGN cArq:visible  = (cbTipLog <> "pgProf")
           btArq:visible = cArq:visible.

    CASE cbTipLog:
        WHEN "pgCli"    THEN ASSIGN cArq:screen-value = getProp("arquivoProgs").
        WHEN "pgMem"    THEN ASSIGN cArq:screen-value = getProp("arquivoProgsMem").
        /* WHEN "pgProf" THEN ASSIGN cArq:screen-value = getProp("arquivoProgsProfiler"). nao pode ser lido aqui */
        WHEN "pgClear"  THEN ASSIGN cArq:screen-value = getProp("arquivoProgsClear").
        WHEN "pgTab"    THEN ASSIGN cArq:screen-value = getProp("arquivoProgsTab").
        WHEN "pgDb"     THEN ASSIGN cArq:screen-value = getProp("arquivoProgsDb").
        WHEN "pgXref"   THEN ASSIGN cArq:screen-value = getProp("arquivoProgsXref").
        WHEN "app"      THEN ASSIGN cArq:screen-value = getProp("arquivoApp").
        WHEN "appPerf"  THEN ASSIGN cArq:screen-value = getProp("arquivoAppPerf").
        WHEN "appBk"    THEN ASSIGN cArq:screen-value = getProp("arquivoAppBroker").
        WHEN "appClear" THEN ASSIGN cArq:screen-value = getProp("arquivoAppClear").
        WHEN "web"      THEN ASSIGN cArq:screen-value = getProp("arquivoWeb").
        WHEN "webClear" THEN ASSIGN cArq:screen-value = getProp("arquivoWebClear").
        WHEN "jb"       THEN ASSIGN cArq:screen-value = getProp("arquivoJboss").
        WHEN "tc"       THEN ASSIGN cArq:screen-value = getProp("arquivoTomcat").
        WHEN "lxSQL"    THEN ASSIGN cArq:screen-value = getProp("arquivoLogixSQL").
        WHEN "lx"       THEN ASSIGN cArq:screen-value = getProp("arquivoLogix").
        WHEN "ac"       THEN ASSIGN cArq:screen-value = getProp("arquivoAcesso").
        WHEN "fl"       THEN ASSIGN cArq:screen-value = getProp("arquivoFluig").
    END.
END.

ON  ESC OF FRAME f-main, wh-jan  DO:
    APPLY "choose" TO btExit.
END.

RUN readProp.

ASSIGN cbTipLog = getProp("tipoLog").

DISPLAY cbTipLog cArq WITH FRAME f-main.

ENABLE ALL WITH FRAME f-main.

APPLY "value-changed" TO cbTipLog.

RUN showMessage("Dica: Escolha o tipo de log, arraste o arquivo de log para o campo de arquivo e clique em 'Processar'").

SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "showMessage"     ANYWHERE.
SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "saveProp"        ANYWHERE.
SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "readProp"        ANYWHERE.
SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "setPropParam"    ANYWHERE.
SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "getPropParam"    ANYWHERE.
SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "setPropParamLog" ANYWHERE.
SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "getPropParamLog" ANYWHERE.
SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "setPropParamInt" ANYWHERE.
SUBSCRIBE PROCEDURE THIS-PROCEDURE TO "getPropParamInt" ANYWHERE.

ASSIGN cParam  = SESSION:PARAMETER
       lNoQuit = FALSE. 
IF  cParam <> ? 
AND cParam <> "" THEN DO:
    IF  NUM-ENTRIES(cParam,";") >= 2 THEN DO:
        ASSIGN cArq     = ENTRY(2, cParam, ";")
               cbTipLog = "".
        CASE ENTRY(1, cParam, ";"):
            WHEN "PROCLI"    THEN ASSIGN cbTipLog = "pgCli".
            WHEN "PROMEN"    THEN ASSIGN cbTipLog = "pgMem".
            WHEN "PROPROF"   THEN ASSIGN cbTipLog = "pgProf".
            WHEN "PROCLEAR"  THEN ASSIGN cbTipLog = "pgClear".
            WHEN "PROTAB"    THEN ASSIGN cbTipLog = "pgTab".
            WHEN "PRODB"     THEN ASSIGN cbTipLog = "pgDb".
            WHEN "PROXREF"   THEN ASSIGN cbTipLog = "pgXref".
            WHEN "APPSERV"   THEN ASSIGN cbTipLog = "app".
            WHEN "APPPERF"   THEN ASSIGN cbTipLog = "appPerf".
            WHEN "APPBROKER" THEN ASSIGN cbTipLog = "appBk".
            WHEN "APPCLEAR"  THEN ASSIGN cbTipLog = "appClear".
            WHEN "WEBSPEED"  THEN ASSIGN cbTipLog = "web".
            WHEN "WEBCLEAR"  THEN ASSIGN cbTipLog = "webClear".
            WHEN "JBOSS"     THEN ASSIGN cbTipLog = "jb".
            WHEN "TOMCAT"    THEN ASSIGN cbTipLog = "tc".
            WHEN "LOGIXSQL"  THEN ASSIGN cbTipLog = "lxSql".
            WHEN "LOGIX"     THEN ASSIGN cbTipLog = "lx".
            WHEN "ACESSO"    THEN ASSIGN cbTipLog = "ac".
            WHEN "FLUIG"     THEN ASSIGN cbTipLog = "fl".
        END CASE.
        IF  NUM-ENTRIES(cParam, ";") = 3 
        AND ENTRY(3, cParam, ";") = "NO-QUIT" THEN
            ASSIGN lNoQuit = TRUE.
            
        IF  cbTipLog <> "" THEN DO:
            DISPLAY cbTipLog WITH FRAME f-main.
            APPLY "value-changed" TO cbTipLog.
            IF  cbTipLog <> "PROPROF" THEN  
                DISPLAY cArq WITH FRAME f-main.
            APPLY "choose" TO btProc.
        END.
    END.
    ELSE DO:
        RUN showMsgParam.
    END.
END.

DO  WITH FRAME f-main
    ON ENDKEY UNDO, LEAVE
    ON ERROR  UNDO, RETRY
    ON STOP   UNDO, RETRY
    ON QUIT   UNDO, RETRY:

    WAIT-FOR CHOOSE OF btExit.
END.

DELETE OBJECT wh-jan.
IF  lNoQuit = FALSE THEN
    QUIT.

/* final do mainBlock */

{log/LogAnalysAcesso.i}
{log/LogAnalysJBoss.i}
{log/LogAnalysLogix.i}
{log/LogAnalysProgress.i}
{log/LogAnalysProgressTab.i}
{log/LogAnalysProgressDb.i}
{log/LogAnalysProgressXref.i}
{log/LogAnalysAppPerf.i}
{log/LogAnalysTomCat.i}
{log/LogAnalysAppBroker.i}
{log/LogAnalysFluig.i}
{log/LogAnalysProfiler.i}
{log/LogAnalysProgressMemory.i}
{log/LogAnalysClear.i}

/*****************************************************************************************
** Procedures gerericas
*****************************************************************************************/
PROCEDURE showMsgParam:
    MESSAGE "LogAnalys" SKIP
            "=========" SKIP
            "Para chamada direta, os parametros devem ser especificados com -param do progress." SKIP
            "Deverao ser especificados o ~"TIPO;Nome_do_Arquivo;TIPO_SAIDA~"" SKIP
            "Exemplo: c:~\dlc122~\bin~\prowin.exe -p LogAnalys.p -param ~"PROCLI;c:\temp\arquivo.log~"" SKIP(1)
            "         c:~\dlc122~\bin~\prowin.exe -p LogAnalys.p -param ~"PROCLI;c:\temp\arquivo.log;NO-QUIT~"" SKIP(1)
            "Tipos permitidos" SKIP
            "----------------" SKIP
            "JBOSS     - JBoss" SKIP
            "TOMCAT    - TomCat" SKIP
            "ACESSO    - Acesso JBoss/TomCat" SKIP
            "FLUIG     - Fluig" SKIP
            "PROCLI    - Progress Client" SKIP
            "PROPROF   - Progress Profiler" SKIP
            "PROCLEAR  - Progress Limpa Log" SKIP
            "PROMEM    - Progress Memory" SKIP
            "PROTAB    - Progress Tabanalys" SKIP
            "PROXREF   - Progress Xref" SKIP
            "PRODB     - Progress Database" SKIP
            "APPSERV   - Appserver Progress" SKIP
            "APPPERF   - Appserver Performance" SKIP
            "APPBROKER - Appserver Broker" SKIP
            "APPCLEAR  - Appserver Limpa Log" SKIP
            "WEBSPEED  - WebSpeed Progress" SKIP
            "WEBCLEAR  - WebSpeed Limpa Log" SKIP
            "LOGIX     - Logix sem SQL" SKIP
            "LOGIXSQL  - Logix com SQL" SKIP(1)
            "Tipos de Saida" SKIP
            "---------------" SKIP
            "NO-QUIT - quando terminar a execucao NAO faz um quit"
            VIEW-AS ALERT-BOX.
END PROCEDURE.

PROCEDURE setPropParam:
    DEFINE INPUT PARAMETER cProp  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cValue AS CHARACTER NO-UNDO.

    setProp(cProp, cValue).
END PROCEDURE.

PROCEDURE getPropParam:
    DEFINE INPUT  PARAMETER cProp  AS CHARACTER NO-UNDO.
    DEFINE OUTPUT PARAMETER cValue AS CHARACTER NO-UNDO.

    cValue = getProp(cProp).
END PROCEDURE.

PROCEDURE setPropParamLog:
    DEFINE INPUT PARAMETER cProp  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cValue AS LOGICAL   NO-UNDO.

    setProp(cProp, STRING(cValue)).
END PROCEDURE.

PROCEDURE getPropParamLog:
    DEFINE INPUT  PARAMETER cProp  AS CHARACTER NO-UNDO.
    DEFINE OUTPUT PARAMETER cValue AS LOGICAL   NO-UNDO.

    cValue = (getProp(cProp) = "yes").
END PROCEDURE.

PROCEDURE setPropParamInt:
    DEFINE INPUT PARAMETER cProp  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cValue AS INTEGER   NO-UNDO.

    setProp(cProp, STRING(cValue)).
END PROCEDURE.

PROCEDURE getPropParamInt:
    DEFINE INPUT  PARAMETER cProp  AS CHARACTER NO-UNDO.
    DEFINE OUTPUT PARAMETER cValue AS INTEGER   NO-UNDO.

    cValue = INTEGER(getProp(cProp)) NO-ERROR.
END PROCEDURE.

PROCEDURE criaFix:
    DEFINE INPUT PARAMETER cError AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cToDo  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin   AS INTEGER   NO-UNDO.

    FIND FIRST ttFix
        WHERE ttFix.tiLinh  = iLin
        AND   ttFix.tcError = cError
        NO-LOCK NO-ERROR.
    IF  NOT AVAILABLE ttFix THEN DO:
        CREATE ttFix.
        ASSIGN ttFix.tcError = cError
               ttFix.tcToDo  = cToDo
               ttFix.tiLinh  = iLin.
    END.
END PROCEDURE.

PROCEDURE atualizaFix:
    FOR EACH ttFix EXCLUSIVE-LOCK:
        FIND FIRST ttDetail
            WHERE ttDetail.tiLinh = ttFix.tiLinh
            NO-LOCK NO-ERROR.
        IF  AVAILABLE ttDetail THEN
            ASSIGN ttFix.tcLinh = ttDetail.tcLinh.
    END.
END PROCEDURE.

PROCEDURE criaCateg:
    DEFINE INPUT PARAMETER cType AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cCat  AS CHARACTER NO-UNDO.

    /* cria a tabela de categorias */
    FIND FIRST ttCat
        WHERE ttCat.tcCate = cCat
        AND   ttCat.tcType = cType
        NO-LOCK NO-ERROR.
    IF  NOT AVAILABLE ttCat THEN DO:
        CREATE ttCat.
        ASSIGN ttCat.tcCate = cCat
               ttCat.tcType = cType.
    END.
END PROCEDURE.

PROCEDURE showFix:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cError    AS CHARACTER   NO-UNDO LABEL "Problema"
                                 VIEW-AS EDITOR SIZE 150 BY 4 SCROLLBAR-VERTICAL SCROLLBAR-HORIZONTAL.
    DEFINE VARIABLE cToDo     AS CHARACTER   NO-UNDO LABEL "Acao"
                                 VIEW-AS EDITOR SIZE 150 BY 4 SCROLLBAR-VERTICAL SCROLLBAR-HORIZONTAL.

    DEFINE BUTTON btShow LABEL "Mostrar a Linha Original".

    DEFINE QUERY qFix FOR ttFix.
    DEFINE BROWSE bFix QUERY qFix DISPLAY
        ttFix.tcError FORMAT "x(134)" LABEL "Erro"
        ttFix.tiLin                   LABEL "Linha"
        with separators 9 down width 150.

    DEFINE FRAME f-fix
        bFix             AT ROW 1.5 COL 03 SKIP(.5)
        "Problema:"      AT 03
        cError NO-LABELS AT 03
        "Acao:"          AT 03
        cToDo  NO-LABELS AT 03 SKIP(.5)
        btClip           AT 03 btPrint btShow btExit
        WITH  SIDE-LABELS THREE-D SIZE 158 BY 23
             VIEW-AS DIALOG-BOX TITLE "Problemas Encontrados".

    ON  CHOOSE OF btClip IN FRAME f-fix DO:
        ASSIGN cLin = "Problema......: " + ttFix.tcError + chr(10)
                    + "Acao..........: " + ttFix.tcToDo  + chr(10)
                    + "Numero Linha..: " + string(ttFix.tiLinh) + chr(10)
                    + "Linha Original: " + ttFix.tcLinh  + chr(10) + chr(10).
        ASSIGN CLIPBOARD:VALUE = cLin.
    END.

    ON  VALUE-CHANGED OF bFix DO:
        IF  AVAILABLE ttFix THEN
            ASSIGN cError:Screen-value = ttFix.tcError
                   cToDo:Screen-value  = ttFix.tcToDo.
        ELSE
            ASSIGN cError:Screen-value = ""
                   cToDo:Screen-value  = "".
    END.

    ON  CHOOSE OF btPrint DO:
        DEFINE BUFFER bttFix FOR ttFix.
        DEFINE VARIABLE cArqPrint AS CHARACTER   NO-UNDO.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_corrigir.log".
        OUTPUT TO VALUE(cArqPrint).
        PUT UNFORMATTED "Problemas encontrados" SKIP
                        "=====================" SKIP (1).
        FOR EACH bttFix NO-LOCK:
            PUT UNFORMATTED
                "Problema......: " + bttFix.tcError + chr(10)
                "Acao..........: " + bttFix.tcToDo  + chr(10)
                "Numero Linha..: " + string(bttFix.tiLinh) + chr(10)
                "Linha Original: " + bttFix.tcLinh  + chr(10) + chr(10).
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  CHOOSE OF btShow DO:
        MESSAGE ttFix.tcLinh VIEW-AS ALERT-BOX INFORMATION TITLE "Linha Original".
    END.

    OPEN QUERY qFix FOR EACH ttFix NO-LOCK.

    ASSIGN cError:READ-ONLY = TRUE
           cToDo:READ-ONLY  = TRUE
           cError:word-wrap = TRUE
           cToDo:word-wrap  = TRUE.

    ENABLE ALL WITH FRAME f-fix.

    APPLY "entry" TO bFix.
    APPLY "value-changed" TO bFix.

    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-fix.
    END.
END PROCEDURE.

PROCEDURE showInfo:
    DEFINE VARIABLE cLin AS CHARACTER NO-UNDO.

    DEFINE FRAME f-info
        cInfo   NO-LABELS AT ROW 1.50 COL 03 SKIP(.5)
        btClip            AT 03 btExit
        WITH  SIDE-LABELS THREE-D SIZE 84 BY 14
             VIEW-AS DIALOG-BOX TITLE "Informacoes do Ambiente".

    ON  CHOOSE OF btClip IN FRAME f-info DO:
        ASSIGN CLIPBOARD:VALUE = cInfo:screen-value.
    END.

    ASSIGN cInfo:READ-ONLY = TRUE.

    ENABLE ALL WITH FRAME f-info.

    FOR EACH ttInfo NO-LOCK:
        ASSIGN cLin = cLin
                    + (IF cLin <> "" THEN CHR(10) ELSE "")
                    + ttInfo.tcProp + ": " + ttInfo.tcValue.
    END.

    ASSIGN cInfo = cLin.

    DISPLAY cInfo WITH FRAME f-Info.

    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-info.
    END.
END PROCEDURE.

PROCEDURE showMessage:
    DEFINE INPUT PARAMETER cMsg AS CHARACTER NO-UNDO.

    MESSAGE cMsg.
    PROCESS EVENTS.
END PROCEDURE.

PROCEDURE zeraTT:
    DEFINE INPUT PARAMETER hBuffer AS HANDLE NO-UNDO.

    hBuffer:EMPTY-TEMP-TABLE().
    EMPTY TEMP-TABLE ttCat.
    EMPTY TEMP-TABLE ttFix.
    EMPTY TEMP-TABLE ttLin.
    EMPTY TEMP-TABLE ttInfo.
    EMPTY TEMP-TABLE ttDetail.
END PROCEDURE.

FUNCTION getListType RETURNS CHARACTER ():
    DEFINE VARIABLE cLin AS CHARACTER NO-UNDO.
    FOR EACH ttCat NO-LOCK
        BREAK BY ttCat.tcType:
        IF  FIRST-OF(ttCat.tcType) THEN
            ASSIGN cLin = cLin + (IF cLin <> "" THEN "," ELSE "") + ttCat.tcType.
    END.
    RETURN cLin.
END FUNCTION.

FUNCTION getListCateg RETURNS CHARACTER (INPUT cType AS CHARACTER):
    DEFINE VARIABLE cLin AS CHARACTER NO-UNDO.
    IF  cType <> "" THEN DO:
        FOR EACH ttCat NO-LOCK
            WHERE ttCat.tcType = cType
            BY ttCat.tcCate:
            ASSIGN cLin = cLin + (IF cLin <> "" THEN "," ELSE "") + ttCat.tcCate.
        END.
    END.
    ELSE DO:
        FOR EACH ttCat NO-LOCK
            BY ttCat.tcCate:
            ASSIGN cLin = cLin + (IF cLin <> "" THEN "," ELSE "") + ttCat.tcCate.
        END.
    END.
    RETURN cLin.
END FUNCTION.

FUNCTION createTTInfo RETURNS CHARACTER (INPUT cKey AS CHARACTER, INPUT cValue AS CHARACTER):
    DEFINE VARIABLE cTmp1     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iCont     AS INTEGER   NO-UNDO.

    ASSIGN cKey = cKey + fill(".", 20 - length(cKey))
           cKey = TRIM(cKey).
    FIND FIRST ttInfo
        WHERE ttInfo.tcProp = cKey
        NO-LOCK NO-ERROR.
    IF  NOT AVAILABLE ttInfo THEN DO:
        FIND LAST ttInfo NO-LOCK NO-ERROR.
        IF  NOT AVAILABLE ttInfo THEN
            ASSIGN iCont = 0.
        ELSE
            ASSIGN iCont = ttInfo.tiLinh + 1.
        CREATE ttInfo.
        ASSIGN ttInfo.tcProp  = cKey
               ttInfo.tcValue = TRIM(cValue)
               ttInfo.tiLinh  = iCont.
    END.
END FUNCTION.

FUNCTION checkInfo RETURNS CHARACTER (INPUT cLin AS CHARACTER, INPUT toFind1 AS CHARACTER, INPUT toFind2 AS CHARACTER, INPUT cTxt AS CHARACTER):
    DEFINE VARIABLE cTmp1     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTmp2     AS CHARACTER NO-UNDO.

    IF  INDEX(cLin, toFind1) > 0
    AND INDEX(cLin, toFind2) > 0 THEN DO:
        ASSIGN cTmp1 = substr(cLin, INDEX(cLin, toFind1) + length(toFind1) + 1, LENGTH(cLin)).
        createTTInfo(cTxt, cTmp1).
    END.
    RETURN "".
END FUNCTION.

FUNCTION createTTDetail RETURNS CHARACTER (INPUT cLin AS CHARACTER, INPUT iLin AS INTEGER, INPUT iSeq AS INTEGER):
    CREATE ttDetail.
    ASSIGN ttDetail.tcLinh = cLin
           ttDetail.tiLinh = iLin.
           ttDetail.tiSeq  = iSeq.
END FUNCTION.

FUNCTION getDifTime RETURNS INTEGER (INPUT t1 AS CHARACTER, INPUT t2 AS CHARACTER):
    DEFINE VARIABLE ihi AS INTEGER NO-UNDO.
    DEFINE VARIABLE ihf AS INTEGER NO-UNDO.
    DEFINE VARIABLE ihd AS INTEGER NO-UNDO.

    ASSIGN ihi = INTEGER(ENTRY(1, t1,":")) * 3600
               + INTEGER(ENTRY(2, t1, ":")) * 60
               + INTEGER(ENTRY(1, ENTRY(3, t1, ":"), "."))
           ihi = ihi * 1000 + INTEGER(ENTRY(2, ENTRY(3, t1, ":"), ".")).

    ASSIGN ihf = INTEGER(ENTRY(1, t2,":")) * 3600
               + INTEGER(ENTRY(2, t2, ":")) * 60
               + INTEGER(ENTRY(1, ENTRY(3, t2, ":"), "."))
           ihf = ihf * 1000 + INTEGER(ENTRY(2, ENTRY(3, t2, ":"), ".")).
    ASSIGN ihd = abs(ihi - ihf).
    RETURN ihd.
END FUNCTION.

FUNCTION setProp RETURNS CHARACTER (INPUT cKey AS CHARACTER, INPUT cVal AS CHARACTER):
    FIND FIRST ttProp
        WHERE ttprop.tcKey = ckey
        NO-LOCK NO-ERROR.
    IF  NOT AVAILABLE ttProp THEN DO:
        CREATE ttProp.
        ASSIGN ttProp.tcKey = cKey.
    END.
    ASSIGN ttProp.tcVal = cVal.
    RETURN "".
END FUNCTION.

FUNCTION getProp RETURNS CHARACTER (INPUT cKey AS CHARACTER):
    DEFINE VARIABLE cRet AS CHARACTER NO-UNDO INITIAL "".
    FIND FIRST ttProp
        WHERE ttprop.tcKey = ckey
        NO-LOCK NO-ERROR.
    IF  AVAILABLE ttProp THEN
        ASSIGN cRet = ttProp.tcVal.
    RETURN cRet.
END FUNCTION.

PROCEDURE saveProp:
    OUTPUT to value(cArqCfg).
    FOR EACH ttProp NO-LOCK:
        PUT UNFORMATTED
            ttProp.tcKey "=" ttProp.tcVal SKIP.
    END.
    OUTPUT close.
END PROCEDURE.

PROCEDURE readProp:
    IF  SEARCH(cArqCfg) <> ? THEN DO:
        INPUT stream sImp from value(cArqCfg).
        REPEAT:
            IMPORT STREAM sImp UNFORMATTED cLin.
            IF  cLin = "" THEN
                LEAVE.
            setProp(ENTRY(1, cLin, "="), ENTRY(2, cLin, "=")) NO-ERROR.
        END.
        INPUT stream sImp close.
    END.
END PROCEDURE.

/* fim */
