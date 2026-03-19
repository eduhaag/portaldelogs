/************************************************************************************************
** Procedures para Appserver Broker
************************************************************************************************/

PROCEDURE criaTTAppBroker:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hBuffer AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLog:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tiLinh", "INTE",0,"","","Linha").
    ttLog:ADD-NEW-FIELD("tcData", "DATE",0,"","","Data").
    ttLog:ADD-NEW-FIELD("tcHora", "CHAR",0,"X(13)","","Hora").
    ttLog:ADD-NEW-FIELD("tcTxt",  "CHAR",0,"","","Detalhes").
    ttLog:ADD-NEW-FIELD("tcLinh", "CHAR",0,"x(90)","","Conteudo").
    ttLog:ADD-NEW-FIELD("tcCate", "CHAR",0,"x(20)","","Categoria").
    ttLog:ADD-NEW-FIELD("tcProc", "CHAR",0,"x(10)","","Processo").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcProc").
    ttLog:ADD-INDEX-FIELD("codigo", "tcCate").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    ttLog:ADD-NEW-INDEX("dataProc", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("dataProc", "tcProc").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcCate").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcData").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcHora").
    ttLog:ADD-INDEX-FIELD("dataProc", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hBuffer = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logAppBroker:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cChave    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE hQuery    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBrowse   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBuffer   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hTTLog    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE lOrdem    AS LOGICAL   NO-UNDO INITIAL TRUE.

    DEFINE FRAME f-log
        cbTypeLst  LABEL "Processo" AT ROW 01.5 COL 3
        cbCatLst
        dDatIni    AT ROW 02.5 COL 3
        dDatFim    SPACE(2)
        cHorIni
        cHorFim    SPACE(2)
        cFilter    VIEW-AS FILL-IN SIZE 47 BY 1 NO-LABELS
        btFilter   btClear
        cDados     NO-LABELS AT ROW 19.5 COL 3
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTAppBroker (OUTPUT hTTLog, OUTPUT hBuffer).

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
           DOWN             = 16
           VISIBLE          = YES
           SENSITIVE        = NO
           SEPARATORS       = TRUE
           COLUMN-RESIZABLE = TRUE.

    /* adiciona as colunas do browse */
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiLinh")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcData")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHora")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcLinh")).

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER   NO-UNDO.
        ASSIGN cbTypeLst
               cbCatLst.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbTypeLst + "_" + cbCatLst + ".log".
        OUTPUT TO VALUE(cArqPrint).
        hQuery:GET-FIRST().
        DO  WHILE NOT hQuery:QUERY-OFF-END:
            PUT UNFORMATTED
                hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE() SKIP.
            hQuery:GET-NEXT().
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  CHOOSE OF btClip IN FRAME f-log DO:
        IF  hBuffer:AVAILABLE THEN
            ASSIGN CLIPBOARD:VALUE = hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE().
    END.

    ON  CHOOSE OF btNotepad IN FRAME f-log DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        DEFINE BUFFER bfDet FOR ttDetail.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.

        ASSIGN cbTypeLst
               cbCatLst.

        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbTypeLst + "_" + cbCatLst + "_tmp.log".
        OUTPUT TO VALUE(cArqPrint).
        PUT UNFORMATTED
           hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()
           SKIP.
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

    ON  VALUE-CHANGED OF cbCatLst DO:
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
               cbCatLst.

        ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcProc = '" + cbTypeLst + "'"
                      + " and ttLog.tcCate = '" + cbCatLst + "'"
                      + cChave.

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
        IF  hBuffer:AVAILABLE THEN
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE().
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
        ASSIGN cFilter
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
                          + " and ttLog.tcHora >= '" + string(cHorIni,"99:99:99") + ",000'"
                          + " and ttLog.tcHora <= '" + string(cHorFim,"99:99:99") + ",999'".

        APPLY "value-changed" TO cbCatLst.
    END.

    ASSIGN cDados:READ-ONLY = TRUE
           hFrame           = FRAME f-log:Handle
           hDados           = cDados:handle
           hBrw             = hBrowse.

    DISPLAY dDatIni dDatFim cHorIni cHorFim WITH FRAME f-log.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaAppBroker (pDir, pArq, hBuffer).

    ASSIGN cbTypeLst:LIST-ITEMS = getListType().
    IF  CAN-DO(cbTypeLst:LIST-ITEMS, "ERROR") THEN
        ASSIGN cbTypeLst:SCREEN-VALUE = "ERROR".
    ELSE
        ASSIGN cbTypeLst:SCREEN-VALUE = ENTRY(1,cbTypeLst:LIST-ITEMS).

    APPLY "value-changed" TO cbTypeLst.

    SESSION:SET-WAIT-STATE("").
    HIDE MESSAGE NO-PAUSE.

    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-log.
    END.

    FINALLY:
        HIDE MESSAGE NO-PAUSE.
        HIDE FRAME f-log NO-PAUSE.
        hQuery:QUERY-CLOSE().
        DELETE OBJECT hQuery NO-ERROR.
        DELETE OBJECT hTTLog NO-ERROR.
        DELETE OBJECT hBrowse NO-ERROR.
        DELETE OBJECT hBuffer NO-ERROR.
    END.
END PROCEDURE.

PROCEDURE importaAppBroker:
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

    RUN processaAppBroker (hBuffer).

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE processaAppBroker:
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE iLinTot   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cData     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHora     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTxt      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cProces   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cCateg    AS CHARACTER NO-UNDO.

    DEFINE BUFFER bfLin FOR ttLin.

    FIND LAST ttLin NO-LOCK NO-ERROR.
    IF  AVAILABLE ttLin THEN
        ASSIGN iLinTot = ttLin.tiLinh.

    FOR EACH ttLin EXCLUSIVE-LOCK:
        IF  (ttLin.tiLinh MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Processando " + STRING(ttLin.tiLinh, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iLinTot, "zzz,zzz,zzz,zzz,zz9") + " linhas.").
        END.

        ASSIGN cLin = ttLin.tcLinh.

        IF  TRIM(cLin) BEGINS "["
        AND NUM-ENTRIES(cLin, "/") > 2
        AND NUM-ENTRIES(cLin, " ") > 4 THEN DO:
            /* zera as variaveis utilizadas */
            ASSIGN cProces = ""
                   cCateg  = ""
                   cData   = ""
                   cHora   = ""
                   cTxt    = ""
                   cLin2   = cLin.

            /* Processo, data, hora e categoria */
            ASSIGN cProces = ENTRY(2, cLin, " ")
                   cData   = ENTRY(2, ENTRY(1, cLin, "@"), "[")
                   cHora   = REPLACE(ENTRY(2, ENTRY(1, cLin, "]"), "@"), "-0300", "")
                   cHora   = REPLACE(cHora, "-0200", "")
                   cCateg  = ENTRY(6, cLin, " ").

            IF  ENTRY(3, cLin, " ") = "T-Main"
            OR  ENTRY(3, cLin, " ") = "T-RMI" THEN
                ASSIGN cCateg = ENTRY(8, cLin, " ")
                       ENTRY(8, cLin, " ") = ""
                       ENTRY(7, cLin, " ") = "".

            IF  cCateg BEGINS "---" THEN
                ASSIGN cCateg = "BASIC".

            /* retira a parte inicial da linha pois ja esta categorizado e temos a data, hora e processo */
            ASSIGN ENTRY(1, cLin, " ") = ""
                   ENTRY(2, cLin, " ") = ""
                   ENTRY(3, cLin, " ") = ""
                   ENTRY(4, cLin, " ") = ""
                   ENTRY(5, cLin, " ") = ""
                   ENTRY(6, cLin, " ") = ""
                   cLin                = REPLACE(cLin, "procStatsData= ", "")
                   cLin                = TRIM(cLin).

            /* [16/04/28@12:15:25.678-0300] P-012117 T-S-0003 3 UB Basic          procStatsData= java/authentication.p|none|PERSISTENT|1|0|0|0|0|1|1 */
            IF  NUM-ENTRIES(cLin, "|") > 3 THEN
                ASSIGN cCateg = "EXECUTION".

            IF  INDEX(cLin, ":") > 1 THEN DO:
                IF  INDEX(cLin, "os.name ") > 0             THEN ASSIGN cTxt = "Sistema Operacional".
                IF  INDEX(cLin, "os.version ") > 0          THEN ASSIGN cTxt = "Versao S.O.........".
                IF  INDEX(cLin, "java.version ") > 0        THEN ASSIGN cTxt = "Versao JAVA........".
                IF  INDEX(cLin, "java.class.path ") > 0     THEN ASSIGN cTxt = "JAVA Class Path....".
                IF  INDEX(cLin, "user.dir ") > 0            THEN ASSIGN cTxt = "Diretorio Usuario..".
                IF  INDEX(cLin, "appserviceNameList ") > 0  THEN ASSIGN cTxt = "Nome do Appserver..".
                IF  INDEX(cLin, "installDir ") > 0          THEN ASSIGN cTxt = "Diretorio Progress.".
                IF  INDEX(cLin, "localHost ") > 0           THEN ASSIGN cTxt = "IP do servidor.....".
                IF  INDEX(cLin, "Started server: ") > 0     THEN
                    ASSIGN cTxt = "Client Carregado...".
                ELSE
                    IF  INDEX(cLin, "ipver ") > 0          THEN
                        ASSIGN cTxt = "Tipo de IP.........".
                IF  INDEX(cLin, "operatingMode ") > 0       THEN ASSIGN cTxt = "Tipo de conexao....".
                IF  INDEX(cLin, "nameServer host ") > 0     THEN ASSIGN cTxt = "NameServer Host....".
                IF  INDEX(cLin, "nameServer port ") > 0     THEN ASSIGN cTxt = "NameServer Port....".
                IF  INDEX(cLin, "PROPATH ") > 0             THEN ASSIGN cTxt = "Propath............".
                IF  INDEX(cLin, "properties file ") > 0     THEN ASSIGN cTxt = "Arquivo Properties.".
                IF  INDEX(cLin, "srvrActivateProc ") > 0    THEN ASSIGN cTxt = "Prog.Ativacao......".
                IF  INDEX(cLin, "srvrConnectProc ") > 0     THEN ASSIGN cTxt = "Prog.Conexao.......".
                IF  INDEX(cLin, "srvrDeactivateProc ") > 0  THEN ASSIGN cTxt = "Prog.Desativacao...".
                IF  INDEX(cLin, "srvrDisconnProc ") > 0     THEN ASSIGN cTxt = "Prog.Desconexao....".
                IF  INDEX(cLin, "srvrShutdownProc ") > 0    THEN ASSIGN cTxt = "Prog.Shutdown......".
                IF  INDEX(cLin, "srvrStartupParam ") > 0    THEN ASSIGN cTxt = "Param.Inicializacao".
                IF  INDEX(cLin, "srvrStartupProc ") > 0     THEN ASSIGN cTxt = "Prog.Inicializacao.".
                IF  INDEX(cLin, "srvrStartupProcParam") > 0 THEN ASSIGN cTxt = "Param.Prog.Inic....".
                IF  INDEX(cLin, "initialSrvrInstance ") > 0 THEN ASSIGN cTxt = "Num.inicial Instanc".
                IF  INDEX(cLin, "maxClientInstance ") > 0   THEN ASSIGN cTxt = "Num. Max clients...".
                IF  INDEX(cLin, "minIdleServers ") > 0      THEN ASSIGN cTxt = "Num. Min. Servers..".
                IF  INDEX(cLin, "maxIdleServers ") > 0      THEN ASSIGN cTxt = "Num. Max. Servers..".
                IF  INDEX(cLin, "minSrvrInstance ") > 0     THEN ASSIGN cTxt = "Num. Min. Instanc..".
                IF  INDEX(cLin, "maxSrvrInstance ") > 0     THEN ASSIGN cTxt = "Num. Max. Instanc..".
                IF  INDEX(cLin, "sessionTimeout ") > 0      THEN ASSIGN cTxt = "Session Timeout....".
                IF  cTxt <> "" THEN
                    ASSIGN cLin   = cTxt + ": " + trim(ENTRY(2, cLin, ":"))
                           cCateg = "AMBIENT".
            END.
            IF  INDEX(cLin, "ERROR:") > 0 THEN
                ASSIGN cCateg = "ERROR".

            RUN criaLinAppBroker (cProces, cData, cHora, upper(cCateg), cLin, cLin2, ttLin.tiLinh, hBuffer).
            DELETE ttLin.
        END.
    END.
    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE criaLinAppBroker:
    DEFINE INPUT PARAMETER cProces AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cData   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cHora   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cCateg  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cLin    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cTxt    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin    AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE dData  AS DATE        NO-UNDO.

    IF  NUM-ENTRIES(cData, "/") > 1 THEN
        ASSIGN dData = DATE(ENTRY(3, cData, "/") + "/" + entry(2, cData, "/") + "/" + entry(1, cData, "/")) no-error.

    /* cria a linha com a informacao */
    IF  cTxt = ""
    OR  cTxt = ? THEN
        ASSIGN cTxt = cLin.

    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tcProc"):BUFFER-VALUE() = cProces.
    hBuffer:BUFFER-FIELD("tcData"):BUFFER-VALUE() = dData.
    hBuffer:BUFFER-FIELD("tcHora"):BUFFER-VALUE() = cHora.
    hBuffer:BUFFER-FIELD("tcCate"):BUFFER-VALUE() = cCateg.
    hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE() = cLin.
    hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()  = cTxt.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() = iLin.

    RUN criaCateg (cProces, cCateg).
END PROCEDURE.

/* fim */
