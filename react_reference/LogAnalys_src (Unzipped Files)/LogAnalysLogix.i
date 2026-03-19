/************************************************************************************************
** Procedures para LOGIX
************************************************************************************************/

PROCEDURE criaTTLogix:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hLogBuf AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLog:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tiLinh", "INTE",0,"","","Linha").
    ttLog:ADD-NEW-FIELD("tcData", "DATE",0,"","","Data").
    ttLog:ADD-NEW-FIELD("tcHora", "CHAR",0,"X(09)","","Hora").
    ttLog:ADD-NEW-FIELD("tcType", "CHAR",0,"x(10)","","Tipo").
    ttLog:ADD-NEW-FIELD("tcTxt",  "CHAR",0,"","","Detalhes").
    ttLog:ADD-NEW-FIELD("tcLinh", "CHAR",0,"x(135)","","Conteudo").
    ttLog:ADD-NEW-FIELD("tcCate", "CHAR",0,"x(20)","","Categoria").
    ttLog:ADD-NEW-FIELD("tcProc", "CHAR",0,"x(12)","","Thread").
    ttLog:ADD-NEW-FIELD("tiStat", "INTE",0,"->>>9","","Status").
    ttLog:ADD-NEW-FIELD("tiRows", "INTE",0,">>>,>>9","","Linhas Afetadas","Linhas!Afetadas").
    ttLog:ADD-NEW-FIELD("tcProg", "CHAR",0,"x(20)","","Programa").
    ttLog:ADD-NEW-FIELD("tiProg", "INTE",0,">>,>>9","","Linhas Prog","Linhas!Prog").
    ttLog:ADD-NEW-FIELD("tcRun",  "CHAR",0,"","","Tempo Exec","Tempo!Exec").
    ttLog:ADD-NEW-FIELD("tcComm", "CHAR",0,"x(64)","","Comando").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcProc").
    ttLog:ADD-INDEX-FIELD("codigo", "tcCate").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    ttLog:ADD-NEW-INDEX("codigo2", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo2", "tcProc").
    ttLog:ADD-INDEX-FIELD("codigo2", "tcType").
    ttLog:ADD-INDEX-FIELD("codigo2", "tcCate").
    ttLog:ADD-INDEX-FIELD("codigo2", "tiLinh").

    ttLog:ADD-NEW-INDEX("dataProc", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("dataProc", "tcProc").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcCate").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcData").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcHora").
    ttLog:ADD-INDEX-FIELD("dataProc", "tiLinh").

    ttLog:ADD-NEW-INDEX("dataProc2", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("dataProc2", "tcProc").
    ttLog:ADD-INDEX-FIELD("dataProc2", "tcType").
    ttLog:ADD-INDEX-FIELD("dataProc2", "tcCate").
    ttLog:ADD-INDEX-FIELD("dataProc2", "tcData").
    ttLog:ADD-INDEX-FIELD("dataProc2", "tcHora").
    ttLog:ADD-INDEX-FIELD("dataProc2", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hLogBuf = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logLogix:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE lErros    AS LOGICAL   NO-UNDO LABEL "Somente Erros?"
                                 VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE cChave    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE hQuery    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBrowse   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBuffer   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hTTLog    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE lOrdem    AS LOGICAL   NO-UNDO INITIAL TRUE.

    DEFINE QUERY qDetail FOR ttDetail.

    DEFINE BROWSE bDetail QUERY qDetail DISPLAY
        ttDetail.tiSeq
        WITH 7 DOWN size 15 by 8.

    DEFINE FRAME f-log
        cbTypeLst  AT ROW 01.5 COL 3
        cbCatLst   SPACE(10)
        lErros
        btInfo     AT ROW 01.5 COL 125
        btCorrigir AT ROW 01.5 COL 152
        dDatIni    AT ROW 02.5 COL 3
        dDatFim    SPACE(2)
        cHorIni
        cHorFim    SPACE(2)
        cbFilter
        cFilter    VIEW-AS FILL-IN SIZE 48 BY 1 NO-LABELS
        btFilter   btClear
        bDetail    AT ROW 19.5 COL 3
        cDados     NO-LABELS AT ROW 19.5 COL 18
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTLogix (OUTPUT hTTLog, OUTPUT hBuffer).

    /* cria a query */
    CREATE QUERY hQuery.
    hQuery:SET-BUFFERS(hBuffer).

    /* define o browse */
    CREATE BROWSE hBrowse
        ASSIGN
           FRAME            = FRAME f-log:HANDLE
           QUERY            = hQuery
           COL              = 3.00
           ROW              = 4.00
           WIDTH            = 170
           DOWN             = 17
           VISIBLE          = YES
           SENSITIVE        = NO
           SEPARATORS       = TRUE
           COLUMN-RESIZABLE = TRUE.

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        ASSIGN cbCatLst
               lErros.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbCatLst + ".log".
        OUTPUT TO VALUE(cArqPrint).
        hQuery:GET-FIRST().
        DO  WHILE NOT hQuery:QUERY-OFF-END:
            FOR EACH ttDetail NO-LOCK
                WHERE ttDetail.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE():
                PUT UNFORMATTED
                    ttDetail.tcLinh SKIP.
            END.
            hQuery:GET-NEXT().
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  CHOOSE OF btClip IN FRAME f-log DO:
        DEFINE BUFFER bfDet FOR ttDetail.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.
        FIND FIRST bfDet
            WHERE bfDet.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE()
            NO-LOCK NO-ERROR.
        IF  AVAILABLE bfDet THEN
            ASSIGN CLIPBOARD:VALUE = bfDet.tcLinh.
        ELSE
            ASSIGN CLIPBOARD:VALUE = "".
    END.

    ON  CHOOSE OF btNotepad IN FRAME f-log DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        DEFINE BUFFER bfDet FOR ttDetail.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.

        ASSIGN cbCatLst
               lErros.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbCatLst + "_tmp.log".
        OUTPUT TO VALUE(cArqPrint).
        FOR EACH bfDet NO-LOCK
            WHERE bfDet.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE():
            PUT UNFORMATTED
                bfDet.tcLinh SKIP.
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  VALUE-CHANGED OF cbTypeLst DO:
        ASSIGN cbTypeLst
               cbCatLst.
        ASSIGN cbCatLst:LIST-ITEMS = getListCateg(cbTypeLst).
        IF  CAN-DO(cbCatLst:LIST-ITEMS, "ERROR") THEN
            ASSIGN cbCatLst:SCREEN-VALUE = "ERROR".
        ELSE
            ASSIGN cbCatLst:SCREEN-VALUE = ENTRY(1,cbCatLst:LIST-ITEMS).
        APPLY "value-changed" TO cbCatLst.
    END.

    ON  VALUE-CHANGED OF cbCatLst, lErros DO:
        ASSIGN lOrdem = TRUE.
        APPLY "recall" TO FRAME f-log.
    END.

    ON  MOUSE-SELECT-CLICK OF hBrowse DO:
        IF  hBuffer:AVAILABLE
        AND hBrowse:CURRENT-COLUMN <> ? THEN
            APPLY "recall" TO FRAME f-log.
    END.

    ON  RECALL OF FRAME f-log DO:
        DEFINE VARIABLE cQuery AS CHARACTER NO-UNDO.

        ASSIGN cbTypeLst
               cbCatLst
               lErros.

        ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcType = '" + cbTypeLst + "'"
                      + " and ttLog.tcCate = '" + cbCatLst + "'"
                      + cChave.

        IF  lErros = TRUE THEN
            ASSIGN cQuery = cQuery + " and ttLog.tiStat < 0".

        IF  hBuffer:AVAILABLE
        AND hBrowse:current-column <> ? THEN
            ASSIGN cQuery = cQuery
                          + " by ttLog." + hBrowse:current-column:name
                          + (IF lOrdem THEN " desc" ELSE "")
                   lOrdem = NOT lOrdem.

        hQuery:QUERY-CLOSE().

        hQuery:QUERY-PREPARE(cQuery).

        hQuery:QUERY-OPEN().

        APPLY "VALUE-CHANGED" TO hBrowse.
        APPLY "entry" TO hBrowse.
    END.

    ON  VALUE-CHANGED OF hBrowse DO:
        IF  NOT hBuffer:AVAILABLE THEN DO:
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = "".
            RETURN.
        END.
        OPEN QUERY qDetail
            FOR EACH ttDetail
                WHERE ttDetail.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE().
        APPLY "value-changed" TO bDetail.
    END.

    ON  VALUE-CHANGED OF bDetail DO:
        IF  AVAILABLE ttDetail THEN
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = ttDetail.tcLinh.
        ELSE
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = "".
    END.

    ON  CHOOSE OF btClear DO:
        ASSIGN cFilter:SCREEN-VALUE = ""
               cChave = "".
        APPLY "value-changed" TO cbCatLst.
    END.

    ON  CHOOSE OF btFilter
    OR  RETURN OF cFilter, dDatIni, dDatFim, cHorIni, cHorFim DO:
        ASSIGN cbFilter
               cFilter
               dDatIni
               dDatFim
               cHorIni
               cHorFim.

        ASSIGN cChave = "".
        IF  dDatIni <> 01/01/1800
        OR  dDatFim <> 12/31/9999 THEN
            ASSIGN cChave = cChave
                          + " and ttLog.tcData >= " + string(dDatIni,"99/99/9999")
                          + " and ttLog.tcData <= " + string(dDatFim,"99/99/9999").

        IF  cHorIni <> "000000"
        OR  cHorFim <> "999999" THEN
            ASSIGN cChave = cChave
                          + " and ttLog.tcHora >= '" + string(cHorIni,"99:99:99") + "'"
                          + " and ttLog.tcHora <= '" + string(cHorFim,"99:99:99") + "'".

        CASE cbFilter:
            WHEN "Thread"   THEN ASSIGN cChave = " and ttLog.tcProc begins '" + cFilter + "'".
            WHEN "Status"   THEN ASSIGN cChave = " and ttLog.tiStat = " + cFilter.
            WHEN "Programa" THEN ASSIGN cChave = " and ttLog.tcProg begins '" + cFilter + "'".
            WHEN "Comando"  THEN ASSIGN cChave = " and ttLog.tcComm matches '*" + cFilter + "*'".
        END CASE.

        APPLY "value-changed" TO cbCatLst.
    END.

    ON  CHOOSE OF btCorrigir DO:
        MESSAGE "Este recurso vai passar informacoes de algumas acoes que deverao ser tomadas para corrigir alguns problemas encontrados em seu ambiente." SKIP
                "Este recurso ainda nao esta disponivel!"
                VIEW-AS ALERT-BOX WARNING.
    END.

    ON  CHOOSE OF btInfo DO:
        RUN showInfo.
    END.

    ASSIGN cDados:READ-ONLY = TRUE
           lDetail          = (cLogixType="SQL")
           hFrame           = FRAME f-log:Handle
           hDados           = cDados:handle
           hBrw             = hBrowse
           hDet             = BROWSE bDetail:handle.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaLogix (pDir, pArq, hBuffer).

    /* adiciona as colunas do browse */
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiLinh")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcProc")).

    IF  lDetail = TRUE THEN DO:
        ASSIGN cbFilter:list-items = "Thread,Status,Programa,Comando".
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcData")).
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHora")).
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiStat")).
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcProg")).
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiProg")).
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiRows")).
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcComm")).
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcRun")).
    END.
    ELSE DO:
        ASSIGN cbFilter:list-items = "Thread,Conteudo".
        /* adiciona as colunas do browse */
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcLinh")).
    END.

    DISPLAY dDatIni dDatFim cHorIni cHorFim WITH FRAME f-log.

    ASSIGN cbTypeLst:LIST-ITEMS   = getListType()
           lErros:visible         = lDetail.

    IF  CAN-DO(cbTypeLst:LIST-ITEMS, "ERROR") THEN
        ASSIGN cbTypeLst:SCREEN-VALUE = "ERROR".
    ELSE
        ASSIGN cbTypeLst:SCREEN-VALUE = ENTRY(1,cbTypeLst:LIST-ITEMS).

    APPLY "value-changed" TO cbTypeLst.

    SESSION:SET-WAIT-STATE("").
    HIDE MESSAGE NO-PAUSE.

    ASSIGN btCorrigir:visible = FALSE.

    APPLY "WINDOW-RESIZED" TO CURRENT-WINDOW.
    
    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-log.
    END.

    FINALLY:
        HIDE MESSAGE NO-PAUSE.
        HIDE FRAME f-log NO-PAUSE.
        hQuery:QUERY-CLOSE().
        DELETE OBJECT hBrowse NO-ERROR.
        DELETE OBJECT hQuery NO-ERROR.
        DELETE OBJECT hBuffer NO-ERROR.
        DELETE OBJECT hTTLog NO-ERROR.
    END.
END PROCEDURE.

PROCEDURE importaLogix:
    DEFINE INPUT PARAMETER cDir    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cArq    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE cArq2     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iLinOrg   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iFileLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iProcLen  AS INTEGER   NO-UNDO.

    RUN zeraTT (hBuffer).

    ASSIGN FILE-INFO:FILENAME = cDir + cArq
           iFileLen           = FILE-INFO:FILE-SIZE
           cInfo              = "".

    ASSIGN cArq2 = ENTRY(1,cArq,".") + "_novo." + ENTRY(2,cArq,".").

    INPUT STREAM sDad FROM VALUE(cDir + cArq).
    REPEAT:
        ASSIGN iLinOrg = iLinOrg + 1.
        IMPORT STREAM sDad UNFORMATTED cLin NO-ERROR.
        IF  ERROR-STATUS:ERROR = TRUE THEN
            LEAVE.

        ASSIGN iProcLen = iProcLen + length(cLin).

        IF  TRIM(cLin) = "" THEN
            NEXT.

        IF  (iLinOrg MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando " + STRING(iProcLen, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iFilelen, "zzz,zzz,zzz,zzz,zz9") + " bytes.").
        END.

        CREATE ttLin.
        ASSIGN ttLin.tcLinh = cLin
               ttLin.tiLinh = iLinOrg.
    END.
    INPUT STREAM sDad CLOSE.

    RUN processaLogix (hBuffer).

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE processaLogix:
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE iLinTot   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iLinOrg   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cCat      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cThread   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cRun      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cProg     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cNLin     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cStatus   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cRows     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cComm     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cCateg    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cData     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHora     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE lCria     AS LOGICAL   NO-UNDO.
    DEFINE VARIABLE lEstouro  AS LOGICAL   NO-UNDO.
    DEFINE VARIABLE cType     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTmp      AS CHARACTER NO-UNDO.

    DEFINE VARIABLE itamlin3  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE itamlin2  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE ix        AS INTEGER   NO-UNDO.
    DEFINE VARIABLE i         AS INTEGER   NO-UNDO.

    DEFINE BUFFER bfLin FOR ttLin.

    FIND LAST ttLin NO-LOCK NO-ERROR.
    IF  AVAILABLE ttLin THEN
        ASSIGN iLinTot = ttLin.tiLinh.

    FOR EACH ttLin EXCLUSIVE-LOCK:
        ASSIGN lCria = TRUE.
        IF  (ttLin.tiLinh MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Processando " + STRING(ttLin.tiLinh, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iLinTot, "zzz,zzz,zzz,zzz,zz9") + " linhas.").
        END.

        RUN verifyInfoLogix (ttLin.tcLinh).

        IF  ttLin.tcLinh BEGINS "[THREAD " THEN DO:
            /* zera as variaveis utilizadas */
            ASSIGN cThread  = ""
                   cRun     = ""
                   cProg    = ""
                   cNLin    = ""
                   cStatus  = ""
                   cRows    = ""
                   cComm    = ""
                   cCateg   = ""
                   cData    = ""
                   cHora    = ""
                   cLin2    = ttLin.tcLinh
                   lEstouro = FALSE.

            /* pega a thread */
            ASSIGN cThread = REPLACE(ENTRY(1, ttLin.tcLinh, "]"), "[THREAD ", "")
                   cLin    = REPLACE(ttLin.tcLinh, "[DEBUG]", "").

            /* ignora se na thread nao tem data e hora */
            IF  NUM-ENTRIES(cLin, "[") >= 2 THEN DO:
                /* data e hora */
                ASSIGN cData   = ENTRY(1, ENTRY(3, cLin, "["), " ")
                       cHora   = REPLACE(ENTRY(2, ENTRY(3, clin, "["), " "), "]", "") no-error.
                ASSIGN lCria   = TRUE
                       ix      = 1.
                FOR EACH bfLin EXCLUSIVE-LOCK
                    WHERE bfLin.tiLinh > ttLin.tiLinh:
                    ASSIGN cLin3 = TRIM(bfLin.tcLinh) no-error.
                    IF  LENGTH(cLin3) > 15000 THEN DO:
                        ASSIGN cTmp = "".
                        DO  i = 1 TO LENGTH(cLin3) BY 15000:
                            ASSIGN cTmp = substr(cLin3, i, i + 15000).
                            createTTDetail (cTmp, ttLin.tiLinh, ix).
                            ASSIGN ix = ix + 1.
                        END.
                        ASSIGN cLin3 = "".
                    END.

                    IF  cLin3 = ""
                    OR  cLin3 BEGINS "TRANSLATE: "
                    OR  cLin3 BEGINS "NAME_" THEN DO:
                        DELETE bfLin.
                        NEXT.
                    END.
                    IF  cLin3 BEGINS "[THREAD " THEN
                        LEAVE.

                    IF  INDEX(ENTRY(1, TRIM(bfLin.tcLinh), " "), "-" + cAno)  > 0 
                    OR  INDEX(ENTRY(1, TRIM(bfLin.tcLinh), " "), "-" + cAnoA) > 0 THEN
                        LEAVE.

                    IF  LENGTH(cLin3) > 15000 THEN DO:
                        ASSIGN cTmp = "".
                        DO  i = 1 TO LENGTH(cLin3) BY 15000:
                            ASSIGN cTmp = substr(cLin3, i, i + 15000).
                            createTTDetail (cTmp, ttLin.tiLinh, ix).
                            ASSIGN ix = ix + 1.
                        END.
                        ASSIGN cLin3 = "".
                    END.

                    DO WHILE INDEX(cLin3, "  ") > 0:
                        ASSIGN cLin3 = REPLACE(cLin3, "  ", " ").
                    END.

                    /* running time */
                    IF  cLin3 BEGINS "RUNNING TIME:" THEN
                        ASSIGN cRun = ENTRY(3, cLin3, " ").
                    /* 4gl source e line */
                    IF  cLin3 BEGINS "4GL SOURCE: " THEN DO:
                        ASSIGN cProg = ENTRY(3, cLin3, " ")
                               cNLin = ENTRY(5, cLin3, " ") NO-ERROR.
                    END.
                    /* status e rows affected */
                    IF  cLin3 BEGINS "STATUS: " THEN DO:
                        ASSIGN cStatus = ENTRY(2, cLin3, " ")
                               cRows   = REPLACE(ENTRY(4, cLin3, " "), "AFFECTED:", "").
                    END.
                    /* command */
                    IF  cLin3 BEGINS "COMMAND:" THEN DO:
                        ASSIGN cComm = REPLACE(cLin3, "COMMAND: " , "").
                        IF  cComm BEGINS "INSERT " THEN
                            ASSIGN cCateg = "INSERT".
                        IF  cComm BEGINS "DELETE " THEN
                            ASSIGN cCateg = "DELETE".
                    END.

                    IF  cLin3 = "EXECUTE" THEN
                        ASSIGN cCateg = "EXECUTE".
                    IF  cLin3 = "DECLARE" THEN
                        ASSIGN cCateg = "DECLARE".
                    IF  cLin3 = "OPEN" THEN
                        ASSIGN cCateg = "OPEN".
                    IF  cLin3 = "CLOSE" THEN
                        ASSIGN cCateg = "CLOSE".
                    IF  cLin3 = "FREE" THEN
                        ASSIGN cCateg = "FREE".
                    IF  cLin3 = "FETCH" THEN
                        ASSIGN cCateg = "FETCH".
                    IF  cLin3 = "PREPARE" THEN
                        ASSIGN cCateg = "PREPARE".

                    ASSIGN cLin2 = cLin2
                                 + (IF  cLin2 <> "" THEN CHR(10) ELSE "")
                                 + cLin3.
                    IF  LENGTH(cLin2) > 15000 THEN DO:
                        createTTDetail (cLin2, ttLin.tiLinh, ix).
                        ASSIGN ix    = ix + 1
                               cLin2 = "".
                    END.
                END.
                IF  LENGTH(cLin2) > 0 THEN DO:
                    createTTDetail (cLin2, ttLin.tiLinh, ix).
                    ASSIGN ix    = ix + 1
                           cLin2 = "".
                END.
                RUN verifyInfoLogix (cLin2).
            END.
            IF  lCria = TRUE THEN DO:
                ASSIGN cComm = substr(cComm, 1, 28000).
                ASSIGN cLin2 = substr(cLin2, 1, 28000).
                RUN criaLinLogix (cThread, cData, cHora, cStatus, cRows, cProg, cNLin, cComm, cRun, cCateg, ttLin.tcLinh, "", ttLin.tiLinh, hBuffer).
            END.
        END.
    END.
END PROCEDURE.

PROCEDURE criaLinLogix:
    DEFINE INPUT PARAMETER cThread AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cData   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cHora   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cStatus AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cRows   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cProg   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cNLin   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cComm   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cRun    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cCateg  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cLin    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cTxt    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin    AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE dData    AS DATE      NO-UNDO.
    DEFINE VARIABLE cType    AS CHARACTER NO-UNDO.

    ASSIGN cData = TRIM(cData)
           cHora = TRIM(cHora)
           cLin  = TRIM(cLin).

    /* corrige o formato de data */
    IF  INDEX(cTxt, "[DEBUG]") > 0
    AND INDEX(cData, "-") > 0 THEN
        ASSIGN cData = ENTRY(3, cData, "-") + "/" + entry(2, cData, "-") + "/" + entry(1, cData, "-").

    ASSIGN dData = DATE(cData) no-error.

    /* retira a thread */
    IF  cLin BEGINS "[THREAD " THEN
        ASSIGN cLin = TRIM(substr(cLin, INDEX(cLin, "]") + 1, LENGTH(cLin))).
    IF  cComm BEGINS "[THREAD " THEN
        ASSIGN cComm = TRIM(substr(cComm, INDEX(cComm, "]") + 1, LENGTH(cComm))).

    IF  INDEX(cTxt, "[DEBUG]") > 0
    AND cComm = "" THEN
        ASSIGN cComm = cLin
               cComm = TRIM(substr(cComm, INDEX(cComm, "]") + 1, LENGTH(cComm))).

    /* valida se e uma hora valida */
    IF  INDEX("012", substr(cHora,1,1)) = 0 THEN
        ASSIGN cHora = "".

    IF  cLogixType = ""
    OR  cCateg = "" THEN DO:
        IF  INDEX(cTxt, "WSCERR") > 0
        AND INDEX(cTxt, "ERRO") > 0 THEN DO:
            /* [ERRO: WSCERR063 / Argument error : Missing field XML as base64Binary */
            ASSIGN cType  = "ERROR"
                   cCateg = "WEBSERVICE".
        END.
        ELSE IF  INDEX(cTxt, "[WARN ]") > 0 THEN DO:
            /* [WARN ][SERVER] [Thread 4107975584] AcceptWT error [-1] errno [4] */
            ASSIGN cType  = "WARNING"
                   cCateg = "SERVER"
                   cLin   = TRIM(REPLACE(cLin, "[WARN ]", "")).
        END.
        ELSE IF  INDEX(cTxt, "[LICENSE") > 0 THEN DO:
            /* [Thread 4152101792] [LOGIX] [LICENSE] [SYSTEMKEY] Carregando licen‡as SUP 08:00:33
               [Thread 4090928032] [LOGIX] ERRO: [LICENSE] Chave de sistema CAP invalida no controle de licencas.
            */
            ASSIGN cType  = "LICENSE"
                   cCateg = "DIVERSOS"
                   cLin   = TRIM(REPLACE(cLin, "[LOGIX]", "")).
            IF  INDEX(cTxt, "ERRO:") > 0 THEN
                ASSIGN cCateg = "ERROR".
        END.
        ELSE IF  INDEX(cTxt, "[LOGIX]") > 0 THEN DO:
            /* [Thread 27010] [LOGIX] Aplicacao: LICLOGIX Versao: 12.1.10.55   Liberacao: 26/01/16 18:00Ult. Modificacao: 2016-03-29 10:44:27
               [Thread 4152101792] [LOGIX] ERRO: Leitura de parametro invalido NUM_VERSAO_PED_ANT usando funcao LOG_GETVAR(). [source: SUP8680.4GL
            */
            ASSIGN cType  = "LOGIX"
                   cCateg = "DIVERSOS"
                   cLin   = TRIM(REPLACE(cLin, "[LOGIX]", "")).
            IF  INDEX(cTxt, "ERRO:") > 0 THEN
                ASSIGN cCateg = "ERROR".
        END.
        ELSE DO:
            ASSIGN cType  = "INFO"
                   cCateg = "SERVER".
        END.
    END.
    IF  cType = "" THEN
        ASSIGN cType = "INFO".
    IF  cCateg = "" THEN
        ASSIGN cCateg = "DIVERSOS".

    IF  (cComm = "" OR cComm = ?) THEN DO:
        IF  cLin = "" OR cLin = ? THEN
            ASSIGN cComm = cTxt.
        ELSE
            ASSIGN cComm = cLin.
    END.

    IF  cComm = ""
    OR  cComm = ? THEN
        ASSIGN cComm = cLin.

    IF  cTxt = ""
    OR  cTxt = ? THEN
        ASSIGN cTxt = cLin.

    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tcData"):BUFFER-VALUE() = dData.
    hBuffer:BUFFER-FIELD("tcHora"):BUFFER-VALUE() = cHora.
    hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE() = cLin.
    hBuffer:BUFFER-FIELD("tcType"):BUFFER-VALUE() = cType.
    hBuffer:BUFFER-FIELD("tcCate"):BUFFER-VALUE() = cCateg.
    hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()  = cTxt.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() = iLin.
    hBuffer:BUFFER-FIELD("tcProc"):BUFFER-VALUE() = cThread.
    hBuffer:BUFFER-FIELD("tiStat"):BUFFER-VALUE() = INTEGER(cStatus) NO-ERROR.
    hBuffer:BUFFER-FIELD("tiRows"):BUFFER-VALUE() = INTEGER(cRows) NO-ERROR.
    hBuffer:BUFFER-FIELD("tcProg"):BUFFER-VALUE() = cProg.
    hBuffer:BUFFER-FIELD("tiProg"):BUFFER-VALUE() = INTEGER(cNLin) NO-ERROR.
    hBuffer:BUFFER-FIELD("tcRun"):BUFFER-VALUE() = cRun.
    hBuffer:BUFFER-FIELD("tcComm"):BUFFER-VALUE() = cComm.

    RUN criaCateg (cType, cCateg).
END PROCEDURE.

PROCEDURE verifyInfoLogix:
    DEFINE INPUT PARAMETER cLin   AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cTmp1     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTmp2     AS CHARACTER NO-UNDO.

    /* timeout ativo
        Warning, [GENERAL] INACTIVETIMEOUT = 1800 seconds is ON.
    */

    /* versao do servidor - 08-Sep-2016 07:58:03.285 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log OS Name:               Windows 8.1 */
    checkInfo(cLin, "InactiveTimeOut: ", "", "InactiveTimeOut").

    /* tipo de banco
        TOTVSDbAccess Connected on Server [(local)] Database [ORACLE/betel] Port [7890] SID [29137377]
    */
    checkInfo(cLin, "InactiveTimeOut: ", "", "InactiveTimeOut").
    IF  INDEX(cLin, "TOTVSDBACCESS CONNECTED ON SERVER") > 0 THEN DO:
        FIND FIRST ttInfo
            WHERE ttInfo.tcProp BEGINS "Tipo de Banco"
            NO-LOCK NO-ERROR.
        IF  NOT AVAILABLE ttInfo THEN DO:
            ASSIGN cTmp1 = REPLACE(cLin, "TOTVSDBACCESS CONNECTED ON SERVER", "")
                   cTmp1 = TRIM(substr(cTmp1, INDEX(cTmp1, "database"), LENGTH(cTmp1)))
                   cTmp1 = REPLACE(REPLACE(REPLACE(cTmp1, "[", ""), "]", ""), "port", "").
            IF  INDEX(cTmp1, "SID") > 0 THEN
                ASSIGN cTmp2 = TRIM(REPLACE(substr(cTmp1, R-INDEX(cTmp1, "SID"), LENGTH(cTmp1)),"SID ",""))
                       cTmp2 = TRIM(REPLACE(cTmp2, "SID", ""))
                       cTmp2 = ENTRY(1, TRIM(REPLACE(cTmp2, ":", "")), " ").
            ASSIGN cTmp1 = ENTRY(2, cTmp1, " ").
            createTTInfo("Tipo de Banco", cTmp1).
            IF  cTmp2 <> "" THEN
                createTTInfo("SID de Conexao", cTmp2).
        END.
    END.
END PROCEDURE.

/* fim */
